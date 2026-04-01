# Review Context: Job Evaluation Pipeline

## What This Code Does
Evaluates individual job postings from job boards (Work at a Startup, Indeed, First Round, Health Tech Nerds, Lightspeed) against candidate fit criteria. Fetches full job description via Browserless, applies pre-scoring gates, then scores with Claude Haiku on a 100-point weighted system.

Pipeline ID: v24qHkIsp8GVCwFkscHP8
Airtable table: Job Listings (tbl6ZV2rHjWz56pP3)

## Scoring Dimensions (rebalanced in v6.3)
- Stage & Size: 30 points (was 50)
- CS Hire Readiness: 25 points (new in v6.3, was missing)
- Role Mandate: 25 points (was 30)
- Sector & Mission: 20 points

## Pre-Scoring Gates (from JD text)
- NRR-first language in opening bullets: immediate disqualifier
- IT support / helpdesk / MSP language: disqualifier
- Scale signals (10K+ customers, "mature CS org"): penalty
- Maintainer density (optimize, streamline, existing playbook): penalty

## JD Fetch Architecture
Primary: Browserless.io renders the page, extracts job description
Fallback: Direct HTTP fetch if Browserless fails
HTML is truncated at 50K chars before regex matching to prevent catastrophic backtracking (v6.4 fix).
All try-catch blocks must have console.error() logging (v6.4 fix, was silently swallowing errors).

## Developer-as-Customer Gate
- Developer persona + <50 employees + no enterprise signals = auto-pass
- Developer persona + 50+ employees + 2+ enterprise signals = proceed (exception)
Enterprise signals: SOC 2, HIPAA, Fortune 500 customers, enterprise sales team, SSO/SAML, ACV/ARR mentions

## Sector Detection
24 sector patterns ported from company pipeline v9.7: fintech, construction, food/CPG, physical security, insurtech, SaaS management, consumer digital health, AI calling, healthcare care delivery, medical device, cybersecurity, legal tech, ed-tech, property management, tax automation, sales tools, veterinary, and more.

## Known Bugs / Previously Fixed
- v6.8: isPEBacked was checked before computed (fixed, moved mergerDQReason after isPEBacked calculation)
- v6.5: Connection routing bug where Brave Search -> IF: HTTP Success bypassed JD fetch (fixed)
- v6.5: Stalled company threshold aligned to 350 employees
- v6.4: HTML truncation at 50K chars before regex (fixes catastrophic backtracking)
- v6.4: console.error() added to all try-catch blocks
- Employee hard DQ in job pipeline: 1000 (different from company pipeline's 150)

## CS Hire Readiness Score Capping (v6.6)
- unlikely = max 65 total score
- low = max 75 total score
Prevents sector/stage inflation from overriding weak CS readiness signals.

## CX Tooling Company Detection (v6.6)
Companies selling helpdesk/ticketing/chatbot software don't get sector bonus (they sell TO CS teams, don't need CS leadership).
