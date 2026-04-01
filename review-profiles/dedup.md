# Review Context: Deduplication System

## What This Code Does
Cross-source deduplication preventing the same company or job from being evaluated multiple times across different scrapers and job boards.

## Key Generation
- Companies: `company:{normalized_name}` (lowercase, alphanumeric only)
- Jobs: `job:{normalized_company}:{normalized_title}`
- Normalization: `name.toLowerCase().replace(/[^a-z0-9]/g, '')`

## Tables
- Seen Opportunities (tbll8igHTftSqsTtQ): Intended central dedup registry
- Funding Alerts (tbl7yU6QYfIFSC2nD): Company evaluation results
- Job Listings (tbl6ZV2rHjWz56pP3): Job evaluation results
- All in base appFEzXvPWvRtXgRY

## CRITICAL BUG: Dedup Register Not Writing (OPEN)
Discovered April 1, 2026.
The Dedup Register subworkflow (MDzcHPZMySqn1DrGh8J0-) is NOT populating Seen Opportunities. Verified: Discord, Airbnb, Instacart all exist in Funding Alerts but NOT in Seen Opportunities.
Root cause unknown. Needs investigation:
- Is the subworkflow being called by the pipeline?
- If called, is the Airtable write failing silently?
- Is the connection from E&E pipeline to the subworkflow broken?

## Workaround: Dual-Source Dedup (Proven Pattern)
All scraper-level dedup must check BOTH tables:
1. Fetch Seen Opportunities (filter: LEFT({Key}, 8) = "company:")
2. Fetch Funding Alerts (Company Name field only, return all)
3. Merge both into a normalized Set stored in workflow staticData
4. Filter companies against this Set before sending to pipeline

Currently implemented in: Growth Stage v2.7, Healthcare v28, Enterprise v28.
Still needed in: Micro-VC v15, Social Justice v25, Climate Tech v23, Lightspeed v1.

## Pipeline-Level Dedup
The E&E pipeline has its own "Dedup Against Existing Table" node that does returnAll on the Funding Alerts table. This catches most repeats but is expensive (reads entire table per run, currently 3,393+ records). The scraper-level dedup reduces how many companies even reach this check.

## Subworkflows
- Dedup Check: bBjeG_RXRI10eAA5TiN7n (used by both pipelines and SEC Form D)
- Dedup Register: MDzcHPZMySqn1DrGh8J0- (used by both pipelines, BUT NOT WORKING)

## Network Match Alerts (DISABLED)
LinkedIn cross-reference feature disabled in v9 due to duplicate record bug. Two parallel merge paths (Job Check + LinkedIn Check) both fed downstream node, causing duplicate Airtable records. Needs single-path re-architecture.
