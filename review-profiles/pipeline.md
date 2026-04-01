# Review Context: Pipeline (Enrich & Evaluate)

## What This Code Does
Tide Pool Enrich & Evaluate Pipeline. Processes companies from VC portfolio scrapers through 6 phases: entity validation, Brave Search enrichment, pre-evaluation gates, persona classification, CS hire readiness check, and full 100-point scoring. Output is an Airtable record with score, status (Apply/Monitor/Passed/Auto-Disqualified), and enriched fields.

## Architecture (6 Phases)
Phase 0: Entity Validation (regex, no API) - catches non-companies
Phase 1: Enrichment (Brave Search) - extracts stage, funding, employees, sector
Phase 2: Pre-Evaluation Gates - 5 tiers (Hard > Sector > GTM > Stale > Soft)
Phase 3: Customer Persona Classification (Claude Haiku) - business/developer/mixed
Phase 4: CS Hire Readiness Threshold (Claude Haiku) - must score >= 10
Phase 5: Full Evaluation (Claude Haiku) - 100-point scoring + domain distance

## Pre-Brave Gate (v9.17)
8 nodes BEFORE Brave Search that DQ companies using scraper-provided data only:
1. Late stage (Series C/D/E/F/Growth/IPO)
2. Employee cap >150
3. Company age >10 years
4. Funding cap >$75M
5. Known large companies list
6. PE ownership keywords
7. Hard sector DQ (biotech, hardware, crypto, consumer, agtech) with SaaS escape hatch
Companies failing pre-Brave gate are written as "Pre-Brave DQ: {reason}" without consuming a Brave query.

## Scoring Dimensions (100 points + domain distance)
- CS Hire Readiness: 0-25
- Stage & Size Fit: 0-25
- Role Mandate: 0-20
- Sector & Mission: 0-15
- Outreach Feasibility: 0-15
Domain distance: +5 (healthcare B2B SaaS) to -10 (physical security)
Thresholds: 60+ = APPLY, 40-59 = WATCH, <40 = PASS

## Current Thresholds (from Airtable Config table)
- EMPLOYEE_HARD_CAP: 150
- EMPLOYEE_SOFT_CAP: 100
- FUNDING_HARD_CAP: $75M
- FUNDING_SOFT_CAP: $50M
- FUNDING_PER_HEAD_THRESHOLD: $2M (only below 50 employees)
- VALUATION_UNICORN: $1B (DQ)
- VALUATION_HIGH: $500M (DQ)
- STAGE_DQ: Series C, D, E, F, Growth, IPO
- COMPANY_AGE_HARD_CAP: 8 years (DQ)
- COMPANY_AGE_SOFT_CAP: 5 years (flag)
- SCORE_APPLY_THRESHOLD: 70
- SCORE_WATCH_THRESHOLD: 40

## Domain Distance Scoring
High-distance (subtract): IT Ops/ITSM -8, Physical Security -10, Vertical Retail POS -8, RegTech -6, Legal Tech -6, Real Estate -7, Construction -7
Target (add): Healthcare B2B SaaS +5, Clinical Operations +5, Care Coordination +4, Patient Engagement +3, DevTools/DevOps +2

## Known Bugs to Check Against
1. **Dedup Register not writing to Seen Opportunities** - Subworkflow MDzcHPZMySqn1DrGh8J0- is not populating Seen Opportunities table. If code interacts with dedup, verify it checks BOTH tables.
2. **Airtable batch node data scrambling** - n8n Airtable node caches record IDs incorrectly in batch. Use HTTP Request with record ID in URL path instead.
3. **Network Match Alerts disabled** - LinkedIn cross-reference disabled in v9 due to duplicate record bug from parallel merge paths.

## Previously Fixed (do not re-flag)
- isRescore DQ preservation: Fixed in Rescore v4.15. If reviewing rescore code, verify the fix is present. Pipeline handles this via separate path.
- Airtable updates: Pipeline uses HTTP Request with record ID in URL path for all PATCH operations. Airtable nodes used only for creates/reads (which are safe).
- Stage gate fallback: v9.16 added sourceStage from Airtable when Brave doesn't extract stage.

## Candidate Profile (What "Good Fit" Means)
Target: Founding CS hire role at VC-backed B2B SaaS, Series A/B, 20-150 employees.
Builder mandate (0-to-1), not maintain-and-optimize.
Sectors: Healthcare B2B SaaS (bonus), enterprise SaaS, regulated industries.
Disqualifiers: PE-backed, developer-as-customer without enterprise motion, NRR-first framing.
