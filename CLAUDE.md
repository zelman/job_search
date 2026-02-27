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
- `VC Scraper - Micro-VC v12.json` (v12) - Pear VC, Floodgate, Afore, Unshackled, 2048 (batched, 2048 uses /function endpoint for infinite scroll, extracts company URLs with news domain filtering)
- `Enrich & Evaluate Pipeline v2.json` (shared subworkflow - companies, with cross-source dedup)
- `Job Evaluation Pipeline v3.json` (shared subworkflow - jobs, with JD fetching, cross-source dedup, 500-999 employee penalty, Support title penalty)
- `Dedup Check Subworkflow.json` (cross-source deduplication lookup)
- `Dedup Register Subworkflow.json` (cross-source deduplication registration)
- `Feedback Loop - Not a Fit.json` (weekly pattern analysis)
- `Feedback Loop - Applied.json` (weekly calibration analysis)

## Workflow Architecture

**Company evaluation (VC scrapers):**
All VC scrapers use the shared `Enrich & Evaluate Pipeline.json` subworkflow via Execute Workflow node.

**Job evaluation:**
Both job workflows use the shared `Job Evaluation Pipeline.json` subworkflow:
- Work at a Startup Scraper v12
- Job Alert Email Parser v3-35

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
