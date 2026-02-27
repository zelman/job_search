# Job Search Automation Enhancement Ideas

*Created: February 24, 2026*

## Overview

Potential enhancements to the n8n job search automation system, organized by category. The system currently has a modular architecture with shared pipelines (Job Evaluation Pipeline, Enrich & Evaluate Pipeline) called by multiple scrapers and parsers.

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

---

## Enrichment Enhancements

### 4. Full Job Description Fetching [SELECTED]
- Many email alerts only have title + company
- Add node to scrape full JD from Job URL before evaluation
- Better scoring with complete context

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
- **Trigger**: Before evaluation in Job Evaluation Pipeline v2 and Enrich & Evaluate Pipeline v2
- **Process**:
  1. Generate normalized dedup key (`job:{company}:{title}` or `company:{company}`)
  2. Query `Seen Opportunities` table for existing record
  3. Skip evaluation if duplicate, register new entries after Airtable upsert
- **Components**:
  - `Dedup Check Subworkflow.json` - Lookup with parallel path to handle empty Airtable results
  - `Dedup Register Subworkflow.json` - Registration after successful record creation
  - `Seen Opportunities` table (Airtable) - Central dedup registry
- **Benefit**: Saves Claude API costs by not re-evaluating the same job/company from multiple sources
- **Files**: `Dedup Check Subworkflow.json`, `Dedup Register Subworkflow.json`, `Job Evaluation Pipeline v2.json`, `Enrich & Evaluate Pipeline v2.json`

### 8. Company-Level Tracking
- Separate "Companies" table from "Jobs" table
- One company → many jobs over time
- Track company-level notes, research, contacts

### 9. Stale Job Cleanup
- Jobs >30 days old with no action → archive
- Recheck job URLs for 404s (position filled)

---

## Outreach Automation

### 10. Cover Letter Drafting
- **Trigger**: Job marked "Apply"
- **Input**: Job description + Tide Pool lens + resume
- **Output**: Draft cover letter in Google Doc, linked in Airtable

### 11. Application Tracker
- Status progression: New → Researching → Applied → Interviewing → Offer/Rejected
- Automated follow-up reminders (7 days post-application)

### 12. Network Match Alerts
- Cross-reference new companies against LinkedIn connections
- "You know someone at this company" flag

---

## Analytics & Reporting

### 13. Weekly Digest Email
- Top 10 new opportunities by score
- Pipeline summary (X new, Y applied, Z interviewing)
- Source effectiveness (which VCs/emails produce best matches)

### 14. Scoring Distribution Dashboard
- How many jobs hit each threshold (80+, 60-79, <60)
- Trend over time (are you finding better fits?)

### 15. VC Effectiveness Tracking
- Which VCs produce the most qualified companies?
- Drop low-yield scrapers, add high-yield ones

---

## Quick Wins Reference

| Enhancement | Effort | Value | Status |
|-------------|--------|-------|--------|
| Full JD fetching | Medium | High - better scoring | ✅ Done |
| "Not a Fit" feedback loop | Medium | High - self-improving system | ✅ Done |
| Applied feedback loop | Medium | High - reinforces good patterns | ✅ Done |
| Cross-source dedup | Medium | Medium - cost savings | ✅ Done |
| Weekly digest email | Low | Medium - stay on top of pipeline | |
| Cover letter drafting | Medium | High - time savings | |

---

## Implementation Status

| Enhancement | Status | Date | Notes |
|-------------|--------|------|-------|
| Full JD Fetching | **Implemented** | 2026-02-24 | Added to Job Evaluation Pipeline - HTTP + Browserless fallback |
| Not a Fit Feedback | **Implemented** | 2026-02-24 | `Feedback Loop - Not a Fit.json` - weekly Monday 9am, uses Claude Sonnet |
| Applied Feedback | **Implemented** | 2026-02-24 | `Feedback Loop - Applied.json` - weekly Monday 9:30am, uses Claude Sonnet |
| Cross-Source Dedup | **Implemented** | 2026-02-26 | `Dedup Check/Register Subworkflows` + `Seen Opportunities` table. Pipelines updated to v2. |

### Feedback Loop Details

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

### Cross-Source Deduplication Details

The dedup system prevents duplicate evaluations across all sources using a central `Seen Opportunities` table.

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

