# Claude Code Project Instructions

## Version Numbering

**Always iterate version numbers when modifying workflows.**

When editing any n8n workflow JSON file:
1. Update the version number in the workflow `name` field
2. Update the filename to match (e.g., `v23` → `v24`)
3. Keep the previous version file if the user wants to preserve it

Current versions (as of Feb 2026):
- `Job Alert Email Parser v3-35.json`
- `Work at a Startup Scraper v12.json`
- `Indeed Job Scraper v4.json`
- `VC Scraper - Healthcare.json` (v25)
- `vc-portfolio-scraper-v26-enriched.json` (v26 - Enterprise/Generalist)
- `VC Scraper - Climate Tech.json` (v23)
- `VC Scraper - Social Justice.json` (v25) - Backstage uses /headliners/ links
- `VC Scraper - Micro-VC v14.json` (v14) - Pear VC, Floodgate, Afore, Unshackled, 2048, **Y Combinator** (sorted by launch date, extracts batch from cards). v14: reduced 2048 scroll iterations to prevent timeout.
- `Enrich & Evaluate Pipeline v4.json` (shared subworkflow - companies, with cross-source dedup + Job Listings cross-reference). v4: optimized Check Job Matches with Map lookup instead of combineAll cartesian product; limited Get Existing Companies fields.
- `Job Evaluation Pipeline v4.json` (shared subworkflow - jobs, with JD fetching, cross-source dedup, 500-999 employee penalty, Support title penalty, network connection override for Google VP contact)
- `Job Evaluation Pipeline v3.json` (previous version, retained for rollback)
- `Dedup Check Subworkflow.json` (cross-source deduplication lookup)
- `Dedup Register Subworkflow.json` (cross-source deduplication registration)
- `Feedback Loop - Not a Fit.json` (weekly pattern analysis)
- `Feedback Loop - Applied.json` (weekly calibration analysis)

## Workflow Architecture

**Company evaluation (VC scrapers):**
All VC scrapers use the shared `Enrich & Evaluate Pipeline v3.json` subworkflow via Execute Workflow node.

**Job evaluation:**
Both job workflows use the shared `Job Evaluation Pipeline v4.json` subworkflow:
- Work at a Startup Scraper v12
- Job Alert Email Parser v3-35

**Accelerator monitoring:**
- Y Combinator is now integrated into `VC Scraper - Micro-VC v13.json`
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
