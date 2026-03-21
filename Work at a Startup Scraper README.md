# Work at a Startup Scraper v12

An n8n workflow that scrapes job listings from Y Combinator's Work at a Startup and Costanoa Ventures portfolio, using the shared Job Evaluation Pipeline v6.6 for AI-powered job scoring.

## Overview

This workflow runs every 6 hours to:
1. Scrape YC Work at a Startup (authenticated via Browserless)
2. Scrape Costanoa Ventures job board
3. Filter for customer support/success leadership roles
4. Deduplicate against existing Airtable records
5. Prefilter using builder vs. maintainer signals
6. Enrich company data via Brave Search (employee count, funding, PE/VC backing)
7. Score using Claude AI (Haiku 4.5) with Tide Pool Agent Lens
8. Add scored jobs to Airtable

**Note:** Uses shared `Job Evaluation Pipeline v6.6` subworkflow for evaluation.

## Data Sources

### Work at a Startup (YC)
- **URL**: workatastartup.com
- **Method**: Browserless headless browser with YC account login
- **Filter**: Support/success + leadership keywords

### Costanoa Ventures
- **URL**: jobs.costanoa.vc
- **Method**: Browserless extraction of `serverInitialData`
- **Filter**: 1-100 employee companies, support/success + leadership

## Pipeline

```
Schedule Trigger (6 hours)
       │
       ├──→ Get Config (Airtable)
       │
       ├──→ Search Existing Jobs (dedup)
       │
       └──→ Fetch Profile (GitHub)
                   │
              Parse Config
                   │
       ┌───────────┴───────────┐
       ▼                       ▼
  Scrape YC              Scrape Costanoa
(Browserless)            (Browserless)
       │                       │
       ▼                       ▼
Parse & Filter           Parse Costanoa
       │                       │
       └───────────┬───────────┘
                   ▼
           Merge Job Sources
                   │
                   ▼
        Dedup Against Airtable
                   │
                   ▼
              Has Jobs?
                   │
                   ▼
    Prefilter: Builder vs Maintainer
                   │
                   ▼
         IF: Should Process
                   │
    ┌──────────────┴──────────────┐
    ▼                             ▼
Skip Filtered          Execute Job Evaluation
                       Pipeline v6.1
                              │
                              ▼
                      Add to Airtable
```

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
- PE-backed company
- 1,000+ employees
- $500M+ total funding
- Public company
- Zombie companies (7+ years, still Seed, <100 employees)

### v6.1 Improvements
- Upsert preserves Review Status (doesn't overwrite "Applied")
- Source field preserved with fallback lookups
- Fixed CS Insider jobs having empty Source field

## Role Filtering

Jobs must contain:

**At least one support/success keyword:**
- support, success, customer, client, cx, experience

**AND at least one leadership keyword:**
- manager, director, vp, vice president, head, lead, chief, supervisor, team lead

## Configuration

### Airtable Config Table

| Key | Description |
|-----|-------------|
| `ANTHROPIC_API_KEY` | Claude API key for scoring |
| `BROWSERLESS_TOKEN` | Browserless.io API token |
| `YC_USER` | Work at a Startup email |
| `YC_PASSWORD` | Work at a Startup password |

### n8n Credentials

| Credential | Type | Used By |
|------------|------|---------|
| Airtable | Token | All Airtable nodes |
| Brave Search | Header Auth | Brave Search Company |

### External Dependencies

| Service | Purpose |
|---------|---------|
| Browserless.io | Headless browser scraping |
| Brave Search API | Company enrichment |
| Anthropic Claude API | AI scoring (Haiku 4.5) |
| GitHub Raw | Tide Pool profile hosting |

## Output Fields

| Field | Description |
|-------|-------------|
| Job Title | Role title |
| Company | Company name |
| Location | Work location |
| Source | "Work at a Startup" or "Costanoa VC" |
| Job URL | Link to posting |
| Tide-Pool Score | 0-100 fit score |
| Tide-Pool Rationale | AI explanation + enrichment data |
| Role Type | builder/maintainer/hybrid |
| Builder Evidence | Positive signals |
| Maintainer Evidence | Negative signals |
| Recommendation | apply/research/skip |

## Troubleshooting

### No jobs scraped
- Check Browserless token is valid
- Verify YC credentials work (try manual login)
- Check if site structure changed

### Brave Search errors
- Verify Brave API key in Header Auth credential
- Check monthly quota (2,000 free requests)

### Claude API errors
- Verify ANTHROPIC_API_KEY in Airtable Config
- Check for rate limiting (30s delay should prevent)

## Related Documentation

- `ARCHITECTURE.md` - Technical architecture
- `Job Alert Email Parser README.md` - Similar job evaluation workflow
- `CLAUDE.md` - Workflow IDs and credentials

## Version History

- **v12**: Uses Job Evaluation Pipeline v6.6 with Batch 4 scoring fixes
- **v11**: Uses Job Evaluation Pipeline v5 with tighter scoring thresholds
- **v10**: Added cross-source deduplication via shared subworkflows
- **v9**: Refactored to use shared Job Evaluation Pipeline subworkflow
- **v8**: Added JD fetching with HTTP fallback to Browserless
- **v7**: Added network connection override for companies with direct contacts
- **v6**: Refactored to use standardized evaluation sub-routine

---

*Last updated: March 2026*
