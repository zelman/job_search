# Claude Code Project Instructions

## Version Numbering

**Always iterate version numbers when modifying workflows.**

When editing any n8n workflow JSON file:
1. Update the version number in the workflow `name` field
2. Update the filename to match (e.g., `v23` → `v24`)
3. Keep the previous version file if the user wants to preserve it

Current versions (as of Mar 2026):
- `Job Alert Email Parser v3-37.json` - v3-37: added OmniJobs scraping via Browserless (Senior/Lead CS roles, Remote US, B2B/Healthtech/SaaS/AI tags), reduced Gmail limit to 2 emails/run to prevent OOM
- `Job Alert Email Parser v3-36.json` (previous version)
- `Work at a Startup Scraper v12.json`
- `Indeed Job Scraper v4.json`
- `VC Scraper - Healthcare.json` (v25)
- `vc-portfolio-scraper-v26-enriched.json` (v26 - Enterprise/Generalist)
- `VC Scraper - Climate Tech.json` (v23)
- `VC Scraper - Social Justice.json` (v25) - Backstage uses /headliners/ links
- `VC Scraper - Micro-VC v14.json` (v14) - Pear VC, Floodgate, Afore, Unshackled, 2048, **Y Combinator** (sorted by launch date, extracts batch from cards). v14: reduced 2048 scroll iterations to prevent timeout.
- `Enrich & Evaluate Pipeline v7.json` (shared subworkflow - companies). v7: aligned pre-filter with Funding Alerts Rescore v2 - expanded PE list (29 firms), acquisition detection, tightened thresholds (>100 employees, >$500M funding), removed founded-year disqualifier.
- `Enrich & Evaluate Pipeline v6.json` (previous version). v6: consumer/DTC exclusion, defense/govt penalty (cap 35), hardware vs SaaS distinction, maturity detection (cap 40), biotech/pharma drug development exclusion (cap 35, distinct from healthcare SaaS).
- `Enrich & Evaluate Pipeline v5.json` (previous version - adds LinkedIn Connections cross-reference for Network Match Alerts)
- `Enrich & Evaluate Pipeline v4.json` (older version - with cross-source dedup + Job Listings cross-reference, optimized Check Job Matches with Map lookup)
- `Job Evaluation Pipeline v6.json` (shared subworkflow - jobs). v6: **CRITICAL FIX** - upsert no longer overwrites Review Status; only sets "New" for genuinely new records. Preserves "Applied" and other user-set statuses. (Mar 4, 2026: Restored 157 records that had statuses overwritten by v5 bug.)
- `Job Evaluation Pipeline v5.json` (previous version). v5: tighter scoring thresholds - 200-499 emp penalty, $50M+ funding penalty, >5yr at Series B+ penalty, stronger MAINTAINER detection (scale existing org, multi-tier, global teams 30+)
- `Job Evaluation Pipeline v4.json` (older version - with JD fetching, cross-source dedup, 500-999 employee penalty, Support title penalty, network connection override)
- `Job Evaluation Pipeline v3.json` (older version, retained for rollback)
- `Dedup Check Subworkflow.json` (cross-source deduplication lookup)
- `Dedup Register Subworkflow.json` (cross-source deduplication registration)
- `Feedback Loop - Not a Fit.json` (weekly pattern analysis)
- `Feedback Loop - Applied.json` (weekly calibration analysis)
- `Funding Alerts Rescore v2.json` (v2 - adds pre-filter node to skip obvious disqualifications before Claude call)
- `Funding Alerts Rescore v1.json` (v1 - original, no pre-filter)

## Workflow Architecture

**Company evaluation (VC scrapers):**
All VC scrapers use the shared `Enrich & Evaluate Pipeline v6.json` subworkflow via Execute Workflow node.

**Job evaluation:**
Both job workflows use the shared `Job Evaluation Pipeline v6.json` subworkflow:
- Work at a Startup Scraper v12
- Job Alert Email Parser v3-37 (includes OmniJobs scraping, Gmail limit: 2)

**Accelerator monitoring:**
- Y Combinator is now integrated into `VC Scraper - Micro-VC v14.json`
- Scrapes YC companies sorted by launch date, extracts batch from cards (W26, S25, etc.)
- Runs on same Tue/Fri schedule as other Micro-VCs

## Job Listings Cross-Reference (v3 feature)

The Enrich & Evaluate Pipeline v3 adds a cross-reference step that checks if a company already has active job postings in the Job Listings table.

**New fields in Funding Alerts table:**
- `Has Active Job Posting` (checkbox) - True if company has any active job
- `Has CX Job Posting` (checkbox) - True if company has active CX/Support job specifically
- `Matching Job Titles` (text) - List of matching job titles

**New status:**
- `Immediate Action` - Company has both funding alert AND active CX job posting

**Email notifications:**
- If `hasCxJobPosting = true`, sends urgent email alert with matching job titles
- Uses Gmail OAuth2 credentials (same as existing)

## Network Match Alerts (v5 feature)

The Enrich & Evaluate Pipeline v5 cross-references companies against your LinkedIn Connections table.

**Airtable table:** `LinkedIn Connections` (tbliKHRPEVI6SceJX)
- Imported from LinkedIn export CSV
- Fields: Name, Company, Position, LinkedIn URL, Connected On, Company Normalized (formula)

**New fields in Funding Alerts table:**
- `Has Network Connection` (checkbox) - True if you have a LinkedIn connection at the company
- `Connection Name` (text) - Name(s) of connection(s) with their position
- `Connection LinkedIn URL` (url) - LinkedIn profile URL for outreach

**New status:**
- `Network Lead` - Company has a network connection (elevated priority for warm outreach)

**Email notifications:**
- Priority alerts sent when company has network connection OR active CX job posting
- Email includes connection name and LinkedIn URL for easy outreach

## Pre-Filter Disqualification (v2 feature)

The Funding Alerts Rescore v2 adds a pre-filter node that auto-disqualifies companies before the expensive Claude API call.

**Disqualification criteria** (any triggers auto-skip):
- Employee count > 100
- Total funding > $500M
- PE/Growth Equity investor detected
- Company was acquired
- Series D+ stage

**Expanded PE/Growth Equity firm list** (v2):
Vista Equity, Thoma Bravo, KKR, Blackstone, Bain Capital, Silver Lake, Apollo, Insight Partners, Clearlake, TA Associates, Brighton Park Capital, General Atlantic, Warburg Pincus, Francisco Partners, Summit Partners, Providence Equity, Welsh Carson, TPG Capital, Hellman & Friedman, Advent International, Permira, EQT Partners, Carlyle, SoftBank Vision Fund

**Disqualified records**:
- Score set to 30, Status to "Skip"
- `Disqualify Reasons` field populated with specific reasons
- `Summary` field shows "Auto-disqualified: {reasons}"
- Enriched fields (Stage, Funding, Employee Count) still updated

**Workflow flow**:
```
Enrich → Pre-Filter → Check DQ?
  ├── Yes (disqualified) → Skip Parse → Update (no Claude call)
  └── No (evaluate) → Prompt → Claude → Parse → Update
```

**Expected savings**: ~30-40% reduction in Claude API calls

---

## Cross-Source Deduplication

The dedup system prevents duplicate evaluations across all sources using a central `Seen Opportunities` table in Airtable.

**Key generation:**
- Jobs: `job:{normalized_company}:{normalized_title}`
- Companies: `company:{normalized_company}`

**Workflow integration:**
1. Before evaluation, call `Dedup Check Subworkflow` to check if already processed
2. If duplicate, skip evaluation (saves Claude API costs)
3. After Airtable record creation, call `Dedup Register Subworkflow` to register new entry

**Airtable table:** `Seen Opportunities` in base `appFEzXvPWvRtXgRY`

## Claude Model

Use `claude-haiku-4-5` for all evaluation nodes (cost-effective for high-volume scoring).
