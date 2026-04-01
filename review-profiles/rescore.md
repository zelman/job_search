# Review Context: Funding Alerts Rescore

## What This Code Does
Standalone n8n workflow that re-evaluates existing Funding Alerts records through Brave Search enrichment and Claude scoring. Runs every 2 minutes, processes unscored or stale records. Uses config-driven architecture where all thresholds come from an Airtable Config table.

## Config-Driven Architecture
All gate thresholds stored in Airtable Config table (tblofzQpzGEN8igVS), not hardcoded.
Config Fetcher subworkflow: aCym9UVO8b7Lz2Lt
PE Firms table: tblU2izcb0wnCNMuV (43 firms with aliases)

Key config values:
- EMPLOYEE_HARD_CAP: 150
- EMPLOYEE_SOFT_CAP: 100
- FUNDING_HARD_CAP: 75000000
- FUNDING_SOFT_CAP: 50000000
- FUNDING_PER_HEAD_THRESHOLD: 2000000 (only below 50 employees)
- STAGE_DQ_LIST: Series C, D, E, F, Growth, IPO
- COMPANY_AGE_HARD_CAP: 8
- VALUATION_UNICORN: 1000000000
- VALUATION_HIGH: 500000000
- SCORE_APPLY_THRESHOLD: 70
- SCORE_WATCH_THRESHOLD: 40
- HEADCOUNT_PENALTY: -10
- REBUILD_BONUS: 20

Config Fetcher returns:
```javascript
{ config: { EMPLOYEE_HARD_CAP: 150, ... },
  peFirms: ["Vista Equity", "Thoma Bravo", ...],
  peAliasMap: { "new mountain": "New Mountain Capital", ... },
  peRegexPattern: "\\b(Vista Equity|Thoma Bravo|...)\\b" }
```

## Known Bug: isRescore (Fixed in v4.15)
When isRescore=true, both pre-existing copy AND detection blocks were skipped, leaving disqualifiers empty. Previously DQ'd records (score=0, DQ reasons populated) went through scoring and got new non-zero scores.
Fix: Handle isRescore explicitly to preserve existing DQ reasons.
Example: InVision (Series D, unicorn, founded 2011) was getting Status=Monitor, Score=62 instead of Auto-Disqualified.
**Verify this fix is present in any rescore code changes.**

## Known Bug: DQ Duplication (Fixed in v4.12)
Detection logic must be wrapped in `if (!existing_dq_reasons)` to prevent duplicate DQ reasons accumulating on rescore.

## Airtable Update Pattern
MUST use HTTP Request with record ID in URL path, NOT the n8n Airtable node (batch scrambling bug).
Pattern: PATCH https://api.airtable.com/v0/appFEzXvPWvRtXgRY/Funding%20Alerts/{RECORD_ID}
Auth: Header, Authorization: Bearer {pat_token}
Body: { "fields": { ... } } (no id field needed, it's in the URL)

## Version History
- v4.15: isRescore bug fix (CURRENT)
- v4.14: Stage Gate + mature company detection
- v4.13: Config-driven architecture
- v4.12: DQ duplication fix
- v4.11: Gate tightening (employee 150, funding $75M)
