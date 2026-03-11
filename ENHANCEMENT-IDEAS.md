# Job Search Automation Enhancement Ideas

*Created: February 24, 2026*
*Updated: March 11, 2026*

## Overview

Potential enhancements to the n8n job search automation system, organized by category. The system currently has a modular architecture with shared pipelines (Job Evaluation Pipeline v6.1, Enrich & Evaluate Pipeline v9) called by multiple scrapers and parsers.

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

### 23. Tide-Pool Scoring Pipeline Improvements [IMPLEMENTED - v9]

**Context**: Analysis of 20 companies scored 68-72 revealed only 5% yield (1 strong fit). Many companies should have been auto-disqualified before expensive Claude evaluation.

**Problem**: Current workflow relies on:
1. Brave Search regex extraction (unreliable for employee counts, funding)
2. Claude prompt "hard caps" (advisory, not enforced)
3. No pre-filters (every record goes to Claude even if obviously disqualified)

**Evidence from Pipeline Research Report (March 3, 2026)**:
| Company | Score | Should Have Been | Actual Issue |
|---------|-------|------------------|--------------|
| Torq | 72 | Auto-skip | 350+ employees, $332M funding |
| Together AI | 68 | Auto-skip | 313 employees, $534M funding |
| Labelbox | 68 | Auto-skip | 144-232 employees, $189M funding |
| Clearbit | 68 | Auto-skip | Acquired by HubSpot (2023) |
| AG5 | 68 | Auto-skip | Amsterdam HQ (non-US) |
| Flocean | 68 | Auto-skip | Oslo HQ, hardware company |

**Proposed Improvements**:

#### A. Pre-Filter Node (Quick Win)
Add node after Enrich, before Claude call:
```javascript
const disqualifyReasons = [];

// Hard filters
if (employee_count && employee_count > 100) {
  disqualifyReasons.push(`${employee_count} employees exceeds 100 cap`);
}
if (total_funding_parsed > 500000000) {
  disqualifyReasons.push(`Funding exceeds $500M cap`);
}
if (pe_backed) {
  disqualifyReasons.push(`PE-backed investor detected`);
}

// If disqualified, skip Claude call entirely
if (disqualifyReasons.length > 0) {
  return { bucket: 'PASS', score: 30, disqualifyReasons: disqualifyReasons.join('; ') };
}
```

#### B. Expand PE Investor Detection
Current list missing growth equity firms. Add:
- Brighton Park Capital
- General Atlantic
- Warburg Pincus
- Francisco Partners
- Summit Partners
- Providence Equity
- Welsh Carson
- TPG Capital

#### C. HQ Location Extraction
Add to Brave Search query: `"{company}" headquarters location`
Extract and filter non-US HQ companies (significant penalty or auto-skip)

#### D. Acquisition Status Check
Add to Brave Search query: `"{company}" acquired OR acquisition site:techcrunch.com OR site:crunchbase.com`
Auto-skip if acquired (no longer independent company)

#### E. Business Model Classification
Improve prompt to distinguish:
- B2B SaaS (target)
- Hardware/infrastructure (skip)
- B2C/consumer (skip)
- Marketplace (evaluate case-by-case)

**New Airtable Fields Needed**:
| Field | Type | Purpose |
|-------|------|---------|
| `HQ Location` | singleLineText | Extracted headquarters city/country |
| `HQ Country` | singleSelect | US / Non-US / Unknown |
| `Acquisition Status` | singleSelect | Independent / Acquired / Unknown |
| `Acquired By` | singleLineText | Acquiring company if applicable |
| `Business Model` | singleSelect | B2B SaaS / Hardware / B2C / Marketplace |
| `Auto-Disqualified` | checkbox | True if pre-filter skipped Claude |

**Implementation Status** (as of v9):
1. ✅ **Pre-filter node**: Multi-tier gate architecture (Tiers 1-5) before Claude evaluation
2. ✅ **PE investor list**: Expanded to 25+ firms including growth equity
3. ✅ **HQ/acquisition extraction**: Geography detection, enhanced acquisition patterns
4. ✅ **CS Hire Readiness threshold**: Quick Claude call to check CS need before full evaluation
5. ✅ **Domain distance scoring**: Penalty/bonus based on sector fit
6. ❌ **Crunchbase API**: Deferred (too expensive ~$500/mo)

**Observed Impact**:
- ~50-60% of companies auto-disqualified before full Claude evaluation
- Better signal quality (Hint Health scored 65 with target domain)
- CS Readiness threshold (>= 10) catches companies without clear CS hiring need

---

## New Job Sources [NEW - March 2026]

### 24. High-Priority Job Aggregators

| Source | URL | Why |
|--------|-----|-----|
| **Getro / Jobs in VC** | jobsinvc.getro.com | Powers 700+ VC fund job boards aggregated - biggest coverage gap |
| **TrueUp** | trueup.io | 15,000+ early-stage startup roles, pre-unicorn filters, salary data |
| **GTMfund Job Board** | jobs.gtmfund.com | B2B SaaS-focused VC, frequently has CS/CX leadership roles |
| **TopStartups.io** | topstartups.io | Aggregates Sequoia, a16z, Benchmark, Accel, Bessemer portfolios |

### 25. CX/CS-Specific Boards

| Source | URL | Notes |
|--------|-----|-------|
| **CS Insider** | csinsider.co | Dedicated Customer Success job board and community |
| **TalentWay** | talentway.com | AI-powered daily CSM job matches, scans 10+ boards |
| **Aspireship** | aspireship.com | SaaS CS training + placement, companies hire directly |
| **CXPA Career Center** | cxpaglobal.org | Customer Experience Professionals Association board |

### 26. Additional VC Portfolio Boards

Not yet scraped:
- a16z talent network
- General Catalyst jobs
- Sequoia portfolio jobs
- Lightspeed portfolio jobs
- Bessemer portfolio jobs
- Battery Ventures portfolio jobs
- Primary Venture Partners (jobs.primary.vc)
- Backed VC (talent.backed.vc)

**Recommended Priority:**
1. Add Getro/Jobs in VC (single source covering biggest blind spot)
2. Add TrueUp (best startup aggregator not currently used)
3. Add CS Insider or TalentWay (CX-specific coverage)

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

### 16. Network Match Alerts [DISABLED - NEEDS FIX]
- Cross-reference new companies against LinkedIn connections
- "You know someone at this company" flag
- **Fields**: `Has Network Connection`, `Connection Name`, `Connection LinkedIn URL`
- **Status**: Implemented in v5, but **disabled in v9** to fix duplicate record bug
- **Issue**: Two parallel merge paths (Job Check + LinkedIn Check) both fed into downstream node, causing duplicate Airtable records
- **Fix needed**: Re-architect with single merge path that combines both job and LinkedIn data before proceeding
- **Priority**: Low (user reports limited startup contacts in LinkedIn, not providing much value currently)
- **File**: `Enrich & Evaluate Pipeline v9.json` (LinkedIn search still runs, but output disconnected)

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
| Network match alerts | Medium | High - warm intros | ⚠️ Disabled (dupe fix) |
| Scoring pre-filters | Low | High - API cost savings, better signal | ✅ Done (v9) |
| PE investor list expansion | Low | Medium - catch growth equity | ✅ Done (v9) |
| HQ/acquisition extraction | Medium | Medium - catch non-US, acquired | ✅ Done (v9) |
| CS Hire Readiness threshold | Medium | High - timing alignment | ✅ Done (v9) |
| Domain distance scoring | Medium | Medium - sector fit penalty/bonus | ✅ Done (v9) |
| Getro/Jobs in VC scraper | Medium | High - 700+ VC boards in one | |
| TrueUp scraper | Medium | High - best startup aggregator | |
| CS Insider scraper | Low | Medium - CX-specific roles | |
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
| Network Match Alerts | **Disabled** | 2026-03-11 | Disabled in v9 to fix dupe bug; needs re-architecture |
| v9 Full Redesign | **Implemented** | 2026-03-11 | Entity validation, acquisition detection, GTM gates, CS Readiness, domain distance |

### Current Pipeline Versions

| Pipeline | Version | Key Features |
|----------|---------|--------------|
| Job Evaluation Pipeline | v6.1 | JD fetching, dedup, scoring refinements, source field preservation |
| Enrich & Evaluate Pipeline | v9 | Full redesign: Entity validation, enhanced acquisition detection, GTM motion gates, CS Hire Readiness threshold, domain distance scoring, dupe fix |
| Job Alert Email Parser | v3-43 | Uses Job Evaluation Pipeline v6.1 |
| Work at a Startup Scraper | v12 | Uses Job Evaluation Pipeline v6.1 |
| VC Scraper - Micro-VC | v14 | Includes Y Combinator, uses Enrich & Evaluate Pipeline v9 |
| VC Scraper - Healthcare | v27 | 14 VC portfolios, uses Enrich & Evaluate Pipeline v9 |

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

Based on v9 deployment (March 11, 2026):

1. ~~**Scoring Pre-Filter Node**~~ ✅ Implemented in v9 (multi-tier gates)
2. ~~**PE Investor List Expansion**~~ ✅ Implemented in v9 (25+ firms)
3. ~~**HQ/Acquisition Extraction**~~ ✅ Implemented in v9
4. **Founder Research Automation** - Reduce manual research time for top companies
5. **Application Funnel Tracking** - Better understand what's working
6. **Weekly Digest Email** - Stay on top of pipeline without checking Airtable daily
7. **Getro/Jobs in VC Scraper** - Single source covering 700+ VC fund job boards
8. **TrueUp Scraper** - Best startup job aggregator not currently used
9. **Re-enable LinkedIn Network Matching** - Low priority; needs single-path merge architecture to avoid dupes
