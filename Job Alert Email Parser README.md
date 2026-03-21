# Job Alert Email Parser v3-43

An n8n workflow that automatically processes job alert emails from multiple sources, filters for relevant roles, enriches company data via Brave Search, uses AI to rate job fit with builder vs maintainer classification, and adds them to an Airtable database.

**Note:** Uses shared `Job Evaluation Pipeline v6.6` subworkflow for evaluation.

## Overview

This workflow runs hourly to:
1. Fetch unread job alert emails from Gmail
2. Identify the source of each email
3. Parse job listings using source-specific parsers
4. Scrape OmniJobs for additional senior CS roles
5. Filter for customer support/success leadership roles
6. Deduplicate against existing Airtable records
7. Prefilter jobs using builder vs maintainer signals
8. Enrich company data via Brave Search
9. Rate job fit using Claude AI (Haiku 4.5) with Tide Pool scoring
10. Auto-disqualify PE-backed, 1000+ employees, $500M+ funding, public companies
11. Add new jobs to Airtable
12. Label processed emails in Gmail

## Supported Job Sources

| Source | Email Domain | Data Extracted |
|--------|--------------|----------------|
| LinkedIn | jobs-listings@linkedin.com, jobalerts-noreply@linkedin.com | Title, Company, Location, Job URL |
| Himalayas | himalayas.app | Title, Company, Location (Remote), Job URL |
| Wellfound | wellfound.com | Title, Company, Location, Company Size, Job URL |
| Built In | builtin.com | Title, Company, Location, Salary, Job URL |
| Remotive | remotive.com | Title, Company, Location, Job URL |
| Indeed | indeed.com | Title, Company, Salary, Job URL |
| Welcome to the Jungle | welcometothejungle.com | Title, Company, Location, Salary, Job URL |
| Google Careers | careers-noreply@google.com | Title, Company (Google), Location, Job URL |
| Jobright | jobright.ai | Title, Company, Location, Salary, Job URL |
| Bloomberry | bloomberry.com | Title, Company, Location, Salary, Job URL |
| **OmniJobs** | Browserless scrape | Senior/Lead CS roles, Remote US, B2B/Healthtech/SaaS tags |

## Role Filtering

Jobs must contain:

**At least one support/success keyword:**
- support, success, customer, client, cx, experience

**AND at least one leadership keyword:**
- manager, director, vp, vice president, head, lead, chief, supervisor, team lead

## Job Evaluation Pipeline v6.6 Features

### Enrichment (Brave Search)
- Employee count
- Funding stage (Seed → Series D+)
- Total funding raised
- PE vs VC backing
- Founded year / company age

### AI Scoring (Claude Haiku 4.5)
- Tide-Pool Score (0-100)
- Role type (builder/maintainer/hybrid)
- Builder evidence / Maintainer evidence
- Recommendation (apply/research/skip)
- Industry classification
- Company stage detection

### Auto-Disqualifiers
- PE-backed company (35+ firm names detected)
- 1,000+ employees
- $500M+ total funding
- Public company
- Known large companies (Anthropic, Google, Meta, etc.)
- Zombie companies (7+ years, still Seed, <100 employees)
- Healthcare compliance skills mismatch

### v6.1 Improvements
- Upsert preserves Review Status (doesn't overwrite "Applied")
- Source field preserved with fallback lookups
- Fixed OmniJobs/CS Insider jobs having empty Source field

## Workflow Architecture

```
Schedule Trigger (hourly)
       │
       ├──→ Fetch Profile (GitHub)
       │
       ├──→ Get Config (Airtable: ANTHROPIC_API_KEY)
       │
       └──→ Get many messages (Gmail)
                   │
                   ▼
              Mark as Read
                   │
                   ▼
         Identify Source (10 parsers)
                   │
                   ├──→ Parse Jobs (email sources)
                   │
                   └──→ Scrape OmniJobs (Browserless)
                               │
                               ▼
                          Has Jobs?
                               │
                               ▼
                        Merge + Dedup
                               │
                               ▼
                    Map Fields for Airtable
                               │
                               ▼
                Prefilter: Builder vs Maintainer
                               │
                               ▼
                     IF: Should Process
                               │
                ┌──────────────┴──────────────┐
                ▼                             ▼
        Skip Filtered              Execute Job Evaluation
                                   Pipeline v6.1
                                          │
                                          ▼
                                   Add to Airtable
                                          │
                                          ▼
                               Add label to message (Gmail)
```

## Airtable Schema

| Field Name | Type | Description |
|------------|------|-------------|
| Job Title | Text | The job title |
| Company | Text | Company name |
| Location | Text | Job location |
| Source | Text | Where the job was found |
| Job URL | URL | Link to the job posting |
| Job ID | Text | Unique identifier for deduplication |
| Salary Info | Text | Salary range if available |
| Date Found | Date | When the job was added |
| Review Status | Single Select | New, Reviewing, Applied, Not a Fit |
| Tide-Pool Score | Number | AI fit score (0-100) |
| Tide-Pool Rationale | Long Text | AI explanation + enrichment data |
| Role Type | Text | builder, maintainer, or hybrid |
| Builder Evidence | Long Text | Positive signals |
| Maintainer Evidence | Long Text | Negative signals |
| Recommendation | Text | apply, research, or skip |

## Configuration

### Gmail Setup
- OAuth2 authentication required
- Needs access to read emails and modify labels

### Airtable Setup
- Personal Access Token authentication
- Base ID: `appFEzXvPWvRtXgRY`
- Table ID: `tbl6ZV2rHjWz56pP3`

### Required API Keys (Airtable Config table)

| Key | Description |
|-----|-------------|
| `ANTHROPIC_API_KEY` | Claude API key for scoring |

### Brave Search Setup
- Create "Header Auth" credential in n8n:
  - Name: `X-Subscription-Token`
  - Value: your Brave API key
- Assign to "Brave Search Company" node

## Troubleshooting

### No jobs being added
- Check if emails are being marked as read before processing completes
- Verify the source is detected correctly in "Identify Source"
- Check "Parse Jobs" output for `_noJobs: true`

### OmniJobs scraping issues
- Browserless token must be valid
- Pagination limited to 3 pages to prevent timeout
- Sleep times reduced to prevent memory issues

### Duplicate jobs
- Verify Job URL or Title+Company combination is unique
- Check cross-source dedup via Seen Opportunities table

## Related Documentation

- `ARCHITECTURE.md` - Technical architecture
- `Work at a Startup Scraper README.md` - Similar job scraping workflow
- `CLAUDE.md` - Workflow IDs and credentials

## Version History

- **v3-43**: Rewrote Browserless title extraction with `isTitleLine()`. Added `isRemoteLocation()` for location patterns. Added "IF: Has Email ID?" for OmniJobs Gmail labeling fix. Fixed Job Evaluation Pipeline v6.6 Upsert for Review Status.
- **v3-42**: Fixed OmniJobs company extraction with comprehensive location detection.
- **v3-41**: Improved OmniJobs company extraction, dedup debug logging.
- **v3-40**: CRITICAL FIX - Dedup was treating Airtable records as new jobs.
- **v3-39**: Reduced OmniJobs pagination to 3 pages to prevent timeout.
- **v3-38**: Fixed OmniJobs `/en/` regex parsing error.
- **v3-37**: Added OmniJobs scraping via Browserless.
- **v3-35**: Uses Job Evaluation Pipeline v5 with tighter thresholds.
- **v3-34**: Added cross-source deduplication.
- **v3-33**: Refactored to use shared Job Evaluation Pipeline.
- **v3-32**: Removed Underdog.io (reverse recruiting, not job board).
- **v3-31**: Added zombie company auto-disqualifier.

---

*Last updated: March 2026*
