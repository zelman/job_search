# Job Search Automation Enhancement Ideas

*Created: February 24, 2026*
*Updated: March 1, 2026*

## Overview

Potential enhancements to the n8n job search automation system, organized by category. The system currently has a modular architecture with shared pipelines (Job Evaluation Pipeline v4, Enrich & Evaluate Pipeline v4) called by multiple scrapers and parsers.

---

## Feedback Loops (Learning from Decisions)

### 1. "Not a Fit" Pattern Analysis [IMPLEMENTED]
- **Trigger**: Weekly Monday 9:00am
- **Query**: Jobs marked "Not a Fit" in past 7 days
- **Process**: Claude Sonnet analyzes rejection patterns across all jobs
- **Output**: HTML email report with:
  - Patterns identified in rejected jobs
  - Suggested new auto-disqualifiers (with affected job counts)
  - Scoring adjustment recommendations
  - What's working well
- **Example insight**: "7 of 12 skipped jobs required 'agency experience' - consider adding to auto-disqualifiers"
- **File**: `Feedback Loop - Not a Fit.json`

### 2. Score Calibration / Applied Feedback Loop [IMPLEMENTED]
- **Trigger**: Weekly Monday 9:30am
- **Query**: Jobs marked "Applied" in past 7 days
- **Process**: Claude Sonnet analyzes what made jobs worth applying to
- **Output**: HTML email report with:
  - Score distribution stats (min, max, avg, median)
  - Calibration issues (good jobs scoring too low)
  - New positive signals to add to scoring
  - Positive signals that worked
- **Why Sonnet?**: Strategic analysis across multiple jobs requires higher capability than individual scoring
- **File**: `Feedback Loop - Applied.json`

### 3. Outcome Tracking
- Add "Interview", "Offer", "Rejected" statuses to Airtable
- Correlate outcomes with scores, company attributes, role types
- Learn which signals actually predict good fits
- **Status**: Partially tracked in Job Applications table

---

## Enrichment Enhancements

### 4. Full Job Description Fetching [IMPLEMENTED]
- Many email alerts only have title + company
- HTTP fetch + Browserless fallback for JavaScript-rendered pages
- Better scoring with complete context
- **File**: `Job Evaluation Pipeline v4.json`

### 5. Company Growth Signals
- LinkedIn employee count delta (hiring velocity)
- Recent funding announcements (Crunchbase RSS/API)
- News mentions (Google News API or Brave News)

### 6. Glassdoor/Blind Sentiment
- Scrape company ratings, CS/Support team reviews
- Flag companies with poor support team sentiment

---

## Pipeline Improvements

### 7. Cross-Source Deduplication [IMPLEMENTED]
- **Trigger**: Before evaluation in Job Evaluation Pipeline v4 and Enrich & Evaluate Pipeline v4
- **Process**:
  1. Generate normalized dedup key (`job:{company}:{title}` or `company:{company}`)
  2. Query `Seen Opportunities` table for existing record
  3. Skip evaluation if duplicate, register new entries after Airtable upsert
- **Components**:
  - `Dedup Check Subworkflow.json` - Lookup with parallel path to handle empty Airtable results
  - `Dedup Register Subworkflow.json` - Registration after successful record creation
  - `Seen Opportunities` table (Airtable) - Central dedup registry
- **Benefit**: Saves Claude API costs by not re-evaluating the same job/company from multiple sources

### 8. Job Listings Cross-Reference [IMPLEMENTED]
- **Trigger**: During company evaluation in Enrich & Evaluate Pipeline v4
- **Process**: Cross-references Funding Alerts against Job Listings table
- **New fields in Funding Alerts**:
  - `Has Active Job Posting` (checkbox)
  - `Has CX Job Posting` (checkbox)
  - `Matching Job Titles` (text)
- **New status**: `Immediate Action` - company has both funding alert AND active CX job posting
- **Benefit**: Surfaces high-priority opportunities where timing aligns

### 9. Scoring Refinements [IMPLEMENTED]
- **500-999 employee penalty**: Mid-size companies often have established CS teams
- **Support title penalty**: "Support" roles typically junior-level
- **Network connection override**: Google VP contact triggers elevated priority
- **File**: `Job Evaluation Pipeline v4.json`

### 10. Pipeline Performance Optimization [IMPLEMENTED]
- **Map lookup optimization**: Replaced combineAll cartesian product with Map-based lookup in Check Job Matches
- **Field limiting**: Reduced fields fetched from Airtable to minimize payload size
- **File**: `Enrich & Evaluate Pipeline v4.json`

### 11. Company-Level Tracking
- Separate "Companies" table from "Jobs" table
- One company → many jobs over time
- Track company-level notes, research, contacts
- **Status**: Partially implemented via Funding Alerts table

### 12. Stale Job Cleanup
- Jobs >30 days old with no action → archive
- Recheck job URLs for 404s (position filled)

---

## Outreach Automation

### 13. Founder Research Pipeline [NEW]
- **Concept**: For top Tide Pool companies, auto-research:
  - Founder names + LinkedIn URLs
  - Recent podcast/video appearances
  - Company news and announcements
- **Output**: Enriched company profile with outreach context
- **Status**: Manual process documented in `FOUNDER-OUTREACH-TOP-20.md`

### 14. Cover Letter Drafting
- **Trigger**: Job marked "Apply"
- **Input**: Job description + Tide Pool lens + resume
- **Output**: Draft cover letter in Google Doc, linked in Airtable

### 15. Application Tracker [PARTIAL]
- Status progression: New → Researching → Applied → Interviewing → Offer/Rejected
- Automated follow-up reminders (7 days post-application)
- **Status**: Manual tracking in Job Applications table (86 records)

### 16. Network Match Alerts [IMPLEMENTED]
- Cross-reference new companies against LinkedIn connections
- "You know someone at this company" flag
- **Status**: Implemented in Enrich & Evaluate Pipeline v5
- **Fields**: `Has Network Connection`, `Connection Name`, `Connection LinkedIn URL`
- **File**: `Enrich & Evaluate Pipeline v5.json`

---

## Analytics & Reporting

### 17. Weekly Digest Email
- Top 10 new opportunities by score
- Pipeline summary (X new, Y applied, Z interviewing)
- Source effectiveness (which VCs/emails produce best matches)

### 18. Scoring Distribution Dashboard
- How many jobs hit each threshold (80+, 60-79, <60)
- Trend over time (are you finding better fits?)

### 19. VC Effectiveness Tracking
- Which VCs produce the most qualified companies?
- Drop low-yield scrapers, add high-yield ones

### 20. Application Funnel Analysis [NEW]
- Track conversion rates: Applied → Response → Interview → Offer
- Identify patterns in successful applications
- **Current data**: ~90 applications, ~5% response rate, early-stage companies outperform

---

## Strategic Considerations

### 21. Python + GitHub Actions Migration [EVALUATED - DEFERRED]
- **Pros**: Better version control, CI/CD, testing, no n8n dependency
- **Cons**: Significant rewrite, n8n working well, time investment
- **Decision**: Stay on n8n unless ongoing evolution required
- **Reference**: `MIGRATION-PLAN-PYTHON-GHA.md`

### 22. Lens Project Commercialization [EVALUATED - LONG-TERM]
- **Concept**: Productize Tide Pool scoring for other job seekers
- **Models evaluated**: PLG subscription vs VC portfolio intelligence
- **Conclusion**: Viable niche ($200-500k ARR ceiling) but 12-24 month build
- **Reference**: `LENS-PROJECT-ANALYSIS.md`

---

## Quick Wins Reference

| Enhancement | Effort | Value | Status |
|-------------|--------|-------|--------|
| Full JD fetching | Medium | High - better scoring | ✅ Done |
| "Not a Fit" feedback loop | Medium | High - self-improving system | ✅ Done |
| Applied feedback loop | Medium | High - reinforces good patterns | ✅ Done |
| Cross-source dedup | Medium | Medium - cost savings | ✅ Done |
| Job Listings cross-reference | Medium | High - surfaces timing alignment | ✅ Done |
| Scoring refinements | Low | Medium - better signal quality | ✅ Done |
| Pipeline optimization | Low | Medium - performance gains | ✅ Done |
| Founder research pipeline | High | High - better outreach | Manual |
| Network match alerts | Medium | High - warm intros | ✅ Done |
| Weekly digest email | Low | Medium - stay on top of pipeline | |
| Cover letter drafting | Medium | High - time savings | |

---

## Implementation Status

| Enhancement | Status | Date | Notes |
|-------------|--------|------|-------|
| Full JD Fetching | **Implemented** | 2026-02-24 | HTTP + Browserless fallback |
| Not a Fit Feedback | **Implemented** | 2026-02-24 | Weekly Monday 9am, Claude Sonnet |
| Applied Feedback | **Implemented** | 2026-02-24 | Weekly Monday 9:30am, Claude Sonnet |
| Cross-Source Dedup | **Implemented** | 2026-02-26 | `Dedup Check/Register Subworkflows` + `Seen Opportunities` table |
| Job Listings X-Ref | **Implemented** | 2026-02-27 | Enrich & Evaluate Pipeline v4 |
| Scoring Refinements | **Implemented** | 2026-02-27 | Job Evaluation Pipeline v4 |
| Pipeline Optimization | **Implemented** | 2026-02-27 | Map lookup, field limiting |
| Founder Research | **Manual** | 2026-03-01 | `FOUNDER-OUTREACH-TOP-20.md` |
| Network Match Alerts | **Implemented** | 2026-03-01 | `Enrich & Evaluate Pipeline v5.json` + `LinkedIn Connections` table |

### Current Pipeline Versions

| Pipeline | Version | Key Features |
|----------|---------|--------------|
| Job Evaluation Pipeline | v4 | JD fetching, dedup, 500-999 penalty, Support penalty, network override |
| Enrich & Evaluate Pipeline | v5 | Dedup, Job Listings cross-ref, LinkedIn Connections cross-ref, Network Match Alerts |
| Job Alert Email Parser | v3-35 | Uses Job Evaluation Pipeline v4 |
| Work at a Startup Scraper | v12 | Uses Job Evaluation Pipeline v4 |
| VC Scraper - Micro-VC | v14 | Includes Y Combinator, uses Enrich & Evaluate Pipeline v5 |

### Feedback Loop Architecture

Both feedback loops form a **closed-loop learning system**:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Job Discovery  │ ──▶ │  User Decision  │ ──▶ │ Feedback Loops  │
│  & Scoring      │     │  (Applied/Not)  │     │ (Weekly)        │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
        ▲                                                │
        │                                                │
        │           ┌─────────────────┐                  │
        └───────────│  Update Lens    │◀─────────────────┘
                    │  (Manual)       │
                    └─────────────────┘
```

**Workflow**: Reports suggest changes → Human reviews → Update Tide Pool lens on GitHub → Changes propagate to all workflows

### Cross-Source Deduplication Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Job Discovery  │ ──▶ │  Dedup Check    │ ──▶ │  Evaluation     │
│  (Any Source)   │     │  (Is it new?)   │     │  (If new)       │
└─────────────────┘     └────────┬────────┘     └────────┬────────┘
                                 │                       │
                        Already seen?                    │
                                 │                       │
                        ┌────────▼────────┐     ┌────────▼────────┐
                        │  Skip (save $)  │     │  Dedup Register │
                        └─────────────────┘     │  (Track it)     │
                                                └─────────────────┘
```

**Key Generation**:
- Jobs: `job:{normalized_company}:{normalized_title}`
- Companies: `company:{normalized_company}`

**Normalization**: Lowercase, remove non-alphanumeric, trim

---

## Next Priority Items

Based on current job search status (~90 applications, ~5% response rate):

1. **Founder Research Automation** - Reduce manual research time for top companies
2. **Application Funnel Tracking** - Better understand what's working
3. **Weekly Digest Email** - Stay on top of pipeline without checking Airtable daily
4. ~~**Network Match Alerts**~~ ✅ Implemented in v5
