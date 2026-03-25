# Claude Code Project Instructions

## File Location

All workflow JSON files are stored in:
```
/Users/zelman/Desktop/Quarantine/Side Projects/Job Search/
```

**Also follow instructions in `./code-review-skill.md`** for code review via external model.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              VC SCRAPERS                                     │
│  Healthcare, Climate Tech, Social Justice, Micro-VC, Enterprise, Lightspeed │
│                                    │                                         │
│                                    ▼                                         │
│                    ┌───────────────────────────────┐                        │
│                    │ Enrich & Evaluate Pipeline v9.14  │◄── UPDATE_AFTER_IMPORT
│                    │   (100-point company scoring) │    (UPDATE after import)
│                    └───────────────┬───────────────┘                        │
│                                    │                                         │
│              ┌─────────────────────┼─────────────────────┐                  │
│              ▼                     ▼                     ▼                  │
│   ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐          │
│   │ Dedup Check     │   │ Brave Search    │   │ Claude API      │          │
│   │ bBjeG_RXRI...   │   │ (enrichment)    │   │ (evaluation)    │          │
│   └─────────────────┘   └─────────────────┘   └─────────────────┘          │
│              │                                           │                  │
│              ▼                                           ▼                  │
│   ┌─────────────────┐                         ┌─────────────────┐          │
│   │ Dedup Register  │                         │ Funding Alerts  │          │
│   │ MDzcHPZMyS...   │                         │ (Airtable)      │          │
│   └─────────────────┘                         └─────────────────┘          │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              JOB SCRAPERS                                    │
│  Work at a Startup v12, Job Alert Email Parser v3-43, Indeed v8.1, First Round v1, │
│  Health Tech Nerds v1, Lightspeed Jobs v1                                      │
│                                    │                                         │
│                                    ▼                                         │
│                    ┌───────────────────────────────┐                        │
│                    │  Job Evaluation Pipeline v6.8   │◄── v24qHkIsp8GVCwFkscHP8
│                    │    (100-point job scoring)    │                        │
│                    └───────────────┬───────────────┘                        │
│                                    │                                         │
│              ┌─────────────────────┼─────────────────────┐                  │
│              ▼                     ▼                     ▼                  │
│   ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐          │
│   │ Dedup Check     │   │ JD Fetch        │   │ Claude API      │          │
│   │ bBjeG_RXRI...   │   │ (Browserless)   │   │ (evaluation)    │          │
│   └─────────────────┘   └─────────────────┘   └─────────────────┘          │
│              │                                           │                  │
│              ▼                                           ▼                  │
│   ┌─────────────────┐                         ┌─────────────────┐          │
│   │ Dedup Register  │                         │  Job Listings   │          │
│   │ MDzcHPZMyS...   │                         │  (Airtable)     │          │
│   └─────────────────┘                         └─────────────────┘          │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           BACKFILL / RESCORE                                 │
│                                    │                                         │
│                                    ▼                                         │
│                    ┌───────────────────────────────┐                        │
│                    │  Funding Alerts Rescore v4.13 │ (standalone)           │
│                    │  Config-driven gates          │ (every 2 min)          │
│                    └───────────────┬───────────────┘                        │
│                                    │                                         │
│       ┌────────────────────────────┼────────────────────────────┐           │
│       ▼                            ▼                            ▼           │
│ ┌───────────────┐     ┌─────────────────┐          ┌─────────────────┐     │
│ │ Config Fetcher│     │ Brave Search    │          │ Claude API      │     │
│ │ (thresholds)  │     │ (enrichment)    │          │ (evaluation)    │     │
│ └───────┬───────┘     └────────┬────────┘          └─────────────────┘     │
│         │                      │                                            │
│         └──────────┬───────────┘                                            │
│                    ▼                                                        │
│          ┌─────────────────┐                         ┌─────────────────┐   │
│          │ Parse Enrich    │                         │ HTTP Request    │   │
│          │ (config-driven) │────────────────────────▶│ (Airtable PATCH)│   │
│          └─────────────────┘                         └─────────────────┘   │
│                                                               │             │
│                    ┌──────────────────────────────────────────┘             │
│                    ▼                                                        │
│          ┌─────────────────┐     ┌─────────────────┐                       │
│          │ Config Table    │     │ PE Firms Table  │                       │
│          │ (thresholds)    │     │ (43 firms)      │                       │
│          └─────────────────┘     └─────────────────┘                       │
│                    └──────────────┬─────────────────┘                       │
│                                   ▼                                         │
│                         ┌─────────────────┐                                │
│                         │ Funding Alerts  │                                │
│                         │ (Airtable)      │                                │
│                         └─────────────────┘                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Candidate Profile (Base Resume)

The pipeline evaluates companies and jobs against this candidate profile:

**File:** `/Users/zelman/Desktop/eric_zelman_resume.md`

| Attribute | Value |
|-----------|-------|
| **Target Role** | Founding CS Leader, VP/Director Customer Success & Support |
| **Experience** | 13 years at Bigtincan (founding CS hire to VP), built 0-to-25 person global team |
| **Domain Expertise** | Enterprise B2B SaaS, Healthcare Tech, AI-powered platforms, Regulated industries |
| **Key Strengths** | Function building from scratch, hypergrowth scaling, distributed team leadership |
| **Team Scale** | Managed 25+ across 3 continents, $2M budget, 24/7 coverage |
| **Customer Scale** | 250+ Fortune 1000 accounts, 2M+ users, 15K+ annual cases, 93%+ CSAT |
| **Tools** | Salesforce Service Cloud, Zendesk, AI agent tools |

**Hard Rules (never claim):**
- No 25% cost-per-contact reduction (false metric)
- No Lean/Six Sigma (no training)
- No "3 data centers" (Bigtincan was not self-hosted)
- KB/self-service deflection was weak (no deflection wins)

---

## FigJam Diagrams

Interactive diagrams for the Job Search system architecture (updated Mar 25, 2026):

| Diagram | Purpose | Link |
|---------|---------|------|
| **System Architecture v9.5** | Overview of all scrapers, pipelines, and Airtable tables | [View in FigJam](https://www.figma.com/online-whiteboard/create-diagram/b857c91d-d47d-4e6b-a2ff-352e76022940) |
| **v9.5 Pipeline Gate Flow** | 5-phase gate architecture with decision points | [View in FigJam](https://www.figma.com/online-whiteboard/create-diagram/8f8d33b6-7b5f-44ce-b606-45a74ef3e2d8) |
| **v9.5 Scoring Architecture** | 100-point scoring breakdown with domain distance modifiers | [View in FigJam](https://www.figma.com/online-whiteboard/create-diagram/916baf11-8e56-4d7a-a2f7-5def6b74042f) |
| **v4.13 Config Architecture** | Config-driven gates with Airtable Config + PE Firms tables | [View in FigJam](https://www.figma.com/online-whiteboard/create-diagram/0c04ac94-2bd5-471c-b6fe-3f91a1194a8e) |

**Note:** Mermaid Chart diagrams are deprecated. FigJam is the canonical diagram platform. Delete outdated Mermaid Chart diagrams in the "Job Search" project (keep only Feedback-Loop-Rejected-Jobs).

---

## n8n Workflow IDs

These IDs are assigned by n8n on import. Update Execute Workflow nodes when replacing subworkflows.

| Workflow | ID | Used By |
|----------|-----|---------|
| **Enrich & Evaluate Pipeline v9** | `UPDATE_AFTER_IMPORT` | All VC scrapers |
| **Job Evaluation Pipeline** | `v24qHkIsp8GVCwFkscHP8` | WaaS, Job Alert Parser, Indeed, First Round |
| **Dedup Check Subworkflow** | `bBjeG_RXRI10eAA5TiN7n` | Both pipelines |
| **Dedup Register Subworkflow** | `MDzcHPZMySqn1DrGh8J0-` | Both pipelines |
| **Config Fetcher Subworkflow** | `aCym9UVO8b7Lz2Lt` | Rescore v4.13 |

**After importing a new pipeline version:**
1. Note the new workflow ID from n8n
2. Update the Execute Workflow nodes in parent workflows
3. Update this table

---

## Airtable Reference

**Base ID:** `appFEzXvPWvRtXgRY` (Job Search)

| Table | ID | Description |
|-------|-----|-------------|
| **Funding Alerts** | `tbl7yU6QYfIFSC2nD` | Company evaluations from VC scrapers |
| **Job Listings** | `tbl6ZV2rHjWz56pP3` | Job evaluations from job scrapers |
| **LinkedIn Connections** | `tbliKHRPEVI6SceJX` | Imported from LinkedIn CSV |
| **Seen Opportunities** | `tbll8igHTftSqsTtQ` | Cross-source dedup registry |
| **Config** | `tblofzQpzGEN8igVS` | Gate thresholds (config-driven architecture) |
| **PE Firms** | `tblU2izcb0wnCNMuV` | 43 PE/Growth Equity firms with aliases |

**MCP Limitation:** The Airtable MCP does not have a delete tool. To delete records, use the Airtable API directly:
```bash
curl -X DELETE "https://api.airtable.com/v0/{baseId}/{tableId}/{recordId}" \
  -H "Authorization: Bearer {pat_token}"
```

---

## Config-Driven Architecture (v4.13)

Gate thresholds are stored in Airtable instead of hardcoded in JavaScript. This allows non-engineer editing and single-source-of-truth management.

**Config Table (`tblofzQpzGEN8igVS`):**

| Key | Value | Purpose |
|-----|-------|---------|
| EMPLOYEE_HARD_CAP | 150 | DQ if employee count exceeds |
| EMPLOYEE_SOFT_CAP | 100 | Penalty zone starts |
| FUNDING_HARD_CAP | 75000000 | DQ if funding exceeds $75M |
| FUNDING_SOFT_CAP | 50000000 | Soft warning zone |
| FUNDING_PER_HEAD_THRESHOLD | 2000000 | DQ if >$2M/employee |
| FUNDING_PER_HEAD_MIN_EMPLOYEES | 50 | Funding ratio only applies below this |
| CS_READINESS_CAP | 25 | Max CS readiness score |
| SCORE_APPLY_THRESHOLD | 70 | Score >= this = Apply bucket |
| SCORE_WATCH_THRESHOLD | 40 | Score >= this = Monitor bucket |
| HEADCOUNT_PENALTY | -10 | Penalty in soft zone |
| REBUILD_BONUS | 20 | Bonus for rebuild signal detected |
| COMPANY_AGE_HARD_CAP | 8 | DQ if older than 8 years |
| COMPANY_AGE_SOFT_CAP | 5 | Warning if 5-8 years |
| VALUATION_UNICORN | 1000000000 | DQ at $1B+ valuation |
| VALUATION_HIGH | 500000000 | DQ at $500M+ valuation |

**PE Firms Table (`tblU2izcb0wnCNMuV`):**

43 PE/Growth Equity firms with:
- `Firm Name` - Canonical name (e.g., "New Mountain Capital")
- `Aliases` - Comma-separated alternatives (e.g., "New Mountain")
- `Active` - Checkbox for filtering

**Config Fetcher Subworkflow (`aCym9UVO8b7Lz2Lt`):**

Fetches both tables and transforms to a config object:
```javascript
{
  config: { EMPLOYEE_HARD_CAP: 150, ... },
  peFirms: ["Vista Equity", "Thoma Bravo", ...],
  peAliasMap: { "new mountain": "New Mountain Capital", ... },
  peRegexPattern: "\\b(Vista Equity|Thoma Bravo|...)\\b"
}
```

**To modify thresholds:**
1. Edit the Config table in Airtable
2. Changes take effect on next workflow run (no code deploy needed)

---

## n8n Credential IDs

Use these IDs in workflow JSON files so credentials auto-map on import:

| Credential | ID | Type |
|------------|-----|------|
| Airtable Personal Access Token | `svcspqcZ9yGYzqGm` | airtableTokenApi |
| Brave Search API | `AzmU2a7s7eN8MFvE` | httpHeaderAuth |
| Anthropic API | `bR8vmR2cZDLoP5W6` | httpHeaderAuth |
| Gmail OAuth2 | `vUMmpPTSbHvfz72M` | gmailOAuth2 |
| Browserless | `iatzkTu30nb6GVd9` | httpHeaderAuth |

---

## Version Numbering

**Always iterate version numbers when modifying workflows.**

When editing any n8n workflow JSON file:
1. Update the version number in the workflow `name` field
2. Update the filename to match (e.g., `v23` → `v24`)
3. Keep the previous version file if the user wants to preserve it

Current versions (as of Mar 2026):
- `Job Alert Email Parser v3-43.json` - v3-43: OmniJobs scraping, Gmail labeling, title extraction improvements.
- `Work at a Startup Scraper v12.json`
- `Indeed Job Scraper v8.1.json` - v8.1: **Fixed staticData API**. v8 used `$workflow.staticData` which is undefined in n8n Cloud task runner. v8.1 uses correct API: `$getWorkflowStaticData('global')`. Architecture unchanged: Parse & Store writes to staticData, All Done? checks noItemsLeft, Extract All Jobs retrieves when loop complete.
- `First Round Jobs Scraper v1.json` - v1: API-based scraper for First Round Capital talent network. Fetches from `jobs.firstround.com/api-boards/search-jobs` with session cookie auth. Filters for CX-relevant roles, includes salary data. Runs Tue/Fri 7am. **Note:** Session cookies expire; refresh from Chrome DevTools when 401 errors occur.
- `Lightspeed Jobs Scraper v1.json` - v1: API-based scraper for Lightspeed portfolio jobs (jobs.lsvp.com). Consider platform. Board ID: `lightspeed`. Filters: US, Seed/Series A/Growth, 1-1000 employees, CX job types. Runs Tue/Fri 7am.
- `Health Tech Nerds Scraper v1.json` - v1: Static JSON scraper for jobs.healthtechnerds.com. Fetches `/data/transformed_job_data.json` directly (no auth needed). Filters for CX leadership roles. Rich data includes job_description, company_description, salary, experience_level, function, keywords. Runs every 6 hours.
- `VC Scraper - Healthcare.json` (v27) - 14 VC portfolios: Flare Capital, 7wireVentures, Oak HC/FT, Digitalis, a16z Bio+Health, Healthworx, Cade, Hustle Fund, Martin Ventures, Town Hall Ventures, Transformation Capital, Brewer Lane, Mainsail Partners, Five Elms. v27: Added Tier 2 healthcare VCs (Transformation Capital, Brewer Lane) and vertical SaaS VCs (Mainsail, Five Elms). Removed Optum Ventures (timeout). Uses token in URL - find/replace `YOUR_BROWSERLESS_TOKEN` before importing.
- `VC Scraper - Enterprise v27.json` - v27: Removed 3 low-signal VCs (Essence VC, Costanoa Ventures, Golden Ventures) due to developer-tools focus and Canadian geography mismatch. Streamlined merge tree. 15 VCs: Unusual, First Round, Khosla, Kapor, WhatIf, WXR, Leadout, Notable, Headline, PSL, Trilogy, K9, Precursor, M25, GoAhead.
- `VC Scraper - Climate Tech.json` (v23)
- `VC Scraper - Social Justice.json` (v25) - Backstage uses /headliners/ links
- `VC Scraper - Micro-VC v15.json` (v15) - Pear VC, Afore, Unshackled, 2048, **Y Combinator** (sorted by launch date, extracts batch from cards). v15: Removed Floodgate (mixed dev/consumer portfolio, low CS signal). v14: reduced 2048 scroll iterations to prevent timeout.
- `VC Scraper - Lightspeed v1.json` - v1: Browserless scraper for Lightspeed Venture Partners (jobs.lsvp.com/companies). URL filters: Seed/Series A/Growth stages, 1-100 employees. Runs Tue/Fri 8am. **Note:** Update Enrich & Evaluate Pipeline workflow ID after import.
- `Enrich & Evaluate Pipeline v9.11.json` (**CURRENT** shared subworkflow - companies). **v9.11: P0 FIX (Mar 20, 2026)** - Fixed critical bug where merger detection code used `allTextLower` before it was defined. Moved merger detection block to after `const allTextLower = allText.toLowerCase();`. **v9.10: MERGER/REBRAND DETECTION (Mar 20, 2026)** - Added PE merger/rebrand detection (pe-merger-detection-v1.1): 45+ merger keywords (roll-up, rebrand, PE portfolio language), expanded acquisition patterns (f/k/a, powered by, portfolio company of), predecessor name extraction, MERGER_DETECTED disqualifier. Fixes false negative where Illumia (Transact Campus + CBORD, PE-backed by GTCR) scored 72. **v9.9: BATCH 4 SCORING FIXES (Mar 16, 2026)** - 4 fixes targeting false positives (Fullview.io) and false negatives (Browserbase): (1) **Employee Count Corroboration** - Uses median of multiple employee mentions; flags suspicious counts (low count with Series A+/high funding). (2) **Funding Recency Graduated Penalty** - Years since last round: 2+ = -5pts, 3+ = -10pts, 4+ = -15pts (catches zombie startups). (3) **CS Hire Readiness Score Capping** - unlikely = max 65, low = max 75 (prevents sector/stage inflation). (4) **CX Tooling Company Detection** - Companies selling helpdesk/ticketing/chatbot software don't get sector bonus (they sell TO CS teams, don't need CS leadership). **v9.8: UNICORN + AGE GATES + CS EVIDENCE (Mar 15, 2026)** - 3 fixes targeting last high-impact scoring gaps: (1) **Unicorn Valuation Gate** - >$1B valuation = DQ (catches Modern Treasury). (2) **Company Age Gate + YC Batch Fix** - >8 years old = DQ, 5-8 years = flag; extracts founding year from YC batch (S12=2012); no longer uses batch as funding stage. (3) **CS Readiness Prompt Overhaul** - Now requires EVIDENCE, not inference from stage; "Series A often hires CS" is NOT evidence; default to 0 if no sourced signals found. **v9.7: EXPANDED SECTOR GATES + DEVELOPER PERSONA** - Added 8 more sector gates: (1) Fintech/Banking - neobank, lending, payment processing, BaaS. (2) Construction Tech - job site, BIM, AEC. (3) Food Science/CPG - fermentation, alternative protein, beverage brands. (4) Physical Security - access control, surveillance, weapon detection. (5) Insurtech - policy management, claims, underwriting. (6) SaaS Management - IT asset management, shadow IT, software spend. (7) Consumer Digital Health - patient-facing apps, therapy apps, wellness, DTx. (8) AI Calling - voice agents, robocall, phone bots. **NEW: Developer-as-Customer Persona Gate** - DQs developer-focused companies with <50 employees and no enterprise sales motion. **CRITICAL FIX: Evaluation prompt score floor** - Removed false "all gates passed" claim; explicitly instructs Claude to score wrong-sector companies below 30. **v9.6: BATCH 4 FEEDBACK FIXES** - 9 sector gates (Healthcare Care Delivery, Medical Device, Cybersecurity, Legal Tech, Ed-tech, Property Management, Tax Automation, Sales Tools, Veterinary). **v9.5: STATUS FALLBACK FIX** - Fixed bug where Status field was empty for some records. Added 'Research' fallback to both Create and Update paths when status is undefined. **v9.4: FIELD CONSOLIDATION** - Removed Next Steps field, consolidated to Status only. Status mapping: APPLY→Apply, WATCH→Monitor, PASS→Passed. Merged Skip into Passed. **v9.3: LOOSENED GATES** to widen opportunity funnel: (a) Employee cap raised 150 → 350 (VP roles exist at larger companies). (b) Soft employee cap raised 150 → 200 (penalty zone starts later). (c) Non-US HQ demoted from hard gate to soft penalty (remote work = HQ irrelevant). (d) WATCH bucket widened 55-69 → 40-69 (catch "not perfect but good" roles). v9.2: Added knownLargeCompanies list (Zapier, SnapLogic), knownAcquired list (Thinkful, Brainbase, Tempus-ex), Canadian cities to non-US geography (Calgary, Vancouver, Montreal). v9: **FULL REDESIGN** addressing 4% signal rate. New features: (1) **Phase 0: Entity Validation** - catches non-companies (podcasts, media, nonprofits) before enrichment. (2) **Enhanced Acquisition Detection** - PE portfolio company patterns, Jonas/Constellation detection. (3) **GTM Motion Gates** - PLG-dominant auto-DQ, pre-sales function company detection. (4) **Stale Company Gates** - 3+ years since funding, shrinking headcount signals. (5) **Software-First Check** - services businesses and hardware-masquerading-as-SaaS detection. (6) **CS Hire Readiness Threshold** - Claude call to check CS need before full evaluation, must score >= 10. (7) **Domain Distance Scoring** - penalty for high-distance domains (ITSM, Legal Tech, Real Estate), bonus for target domains (Healthcare B2B SaaS). **v9.1 batch evaluation fixes (Mar 2026):** (a) Added PE firms: Ares Management, Ares Capital, Spring Lake Equity, Vector Capital. (b) Tightened employee cap: 200 → 150. (c) Tightened funding cap: $500M → $450M. (d) Enhanced healthcare services detection: direct care services, virtual care providers, insurance brokerage patterns.
- `Enrich & Evaluate Pipeline v8.5.json` (rollback version). v8.5: 8 scoring fixes including employee-user persona, stricter SaaS gate, geography gate, age gate.
- `Job Evaluation Pipeline v6.8.json` (**CURRENT** shared subworkflow - jobs). **v6.8: P0 FIX (Mar 20, 2026)** - Fixed critical bug where `enrichment.isPEBacked` was checked before it was computed. Moved mergerDQReason generation to after `isPEBacked` calculation. **v6.7: MERGER/REBRAND DETECTION (Mar 20, 2026)** - Added PE merger/rebrand detection (pe-merger-detection-v1.1): 45+ merger keywords, expanded acquisition patterns, predecessor name extraction, MERGER_DETECTED disqualifier. **v6.6: BATCH 4 SCORING FIXES (Mar 16, 2026)** - 4 fixes ported from company pipeline: (1) Employee count corroboration with median. (2) Funding recency graduated penalties. (3) CS Hire Readiness score capping (unlikely=65, low=75). (4) CX Tooling company detection (no sector bonus for CX vendors). **v6.5: OPUS CODE REVIEW FIXES (Mar 16, 2026)** - Fixed 3 issues from Opus code review: (1) **Connection routing bug** - Removed incorrect Brave Search → IF: HTTP Success connection that bypassed JD fetch and triggered unnecessary Browserless fallbacks. (2) **Stalled company threshold** - Aligned to 350 employees (was 200). (3) **Network override filter** - Fixed string interpolation in filter condition. **v6.4: CODE REVIEW FIXES (Mar 15, 2026)** - Fixed 2 critical issues from Sonnet code review: (1) HTML truncation before regex matching (50K char limit) to prevent catastrophic backtracking on long job descriptions. (2) Added console.error() logging to all try-catch blocks that were silently swallowing errors. **v6.3: MAJOR OVERHAUL** - Aligned thresholds to agent lens v2.13. (1) Employee hard DQ: 1000 → 200. (2) Added 24 sector detection patterns (ported from company pipeline v9.7). (3) Added developer-as-customer persona gate. (4) Added JD-based pre-scoring: NRR detection, IT support detection, scale signals, maintainer density. (5) Focused scoring prompt (3K tokens vs 15K). (6) Added CS Hire Readiness as 25-point dimension (was missing!). (7) Rebalanced scoring: Stage 30pts (was 50), CS Readiness 25pts (new), Role 25pts (was 30). (8) Explicit wrong-sector score floor guidance. v6.2: Reduced scoring penalties. v6.1: Source field fix.
- `Dedup Check Subworkflow.json` (cross-source deduplication lookup)
- `Dedup Register Subworkflow.json` (cross-source deduplication registration)
- `Feedback Loop - Not a Fit.json` (weekly pattern analysis)
- `Feedback Loop - Applied.json` (weekly calibration analysis)
- `Funding Alerts Rescore v4.13-standalone.json` (**ACTIVE** - Config-driven standalone workflow. Runs every 2 min. **v4.13: CONFIG-DRIVEN ARCHITECTURE (Mar 25, 2026)** - All gate thresholds fetched from Airtable Config table. PE firms list fetched from PE Firms table. No hardcoded magic numbers. Uses Config Fetcher subworkflow (`aCym9UVO8b7Lz2Lt`). **v4.12: DQ DUPLICATION FIX** - Wrapped detection logic in `if (!existing_dq_reasons)` to prevent duplicate DQ reasons accumulating on rescore. **v4.11: GATE TIGHTENING** - Employee cap 150, funding cap $75M, PE acquisition detection, hardware/deeptech keywords, funding-per-head ratio gate. **v4.10: GATE TIGHTENING + FIXES** - Aligned with SCORING-THRESHOLDS.md. **v4.5: Job & Network Cross-Reference** - Cross-reference against Job Listings and LinkedIn Connections tables.)

## Workflow Architecture

**Company evaluation (VC scrapers):**
All VC scrapers use the shared `Enrich & Evaluate Pipeline v9.json` subworkflow via Execute Workflow node.

**Job evaluation:**
All job workflows use the shared `Job Evaluation Pipeline v6.8.json` subworkflow:
- Work at a Startup Scraper v12
- Job Alert Email Parser v3-43 (includes OmniJobs scraping, Gmail limit: 2)
- First Round Jobs Scraper v1 (API-based, session cookie auth, CX roles only)
- Lightspeed Jobs Scraper v1 (API-based, session cookie auth, CX roles only)
- Health Tech Nerds Scraper v1 (static JSON, no auth)

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

## Network Match Alerts (v5 feature) - DISABLED IN v9

**Status:** This feature is currently **disabled in v9** to fix a duplicate record bug. The two parallel merge paths (Job Check + LinkedIn Check) both fed into the downstream node, causing duplicate Airtable records. A re-architecture with a single merge path is needed to re-enable this feature.

The Enrich & Evaluate Pipeline v5 introduced cross-referencing companies against your LinkedIn Connections table.

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

## Pre-Filter Disqualification (v8.4 gates)

The Enrich & Evaluate Pipeline v8.4 implements a **multi-tier disqualification architecture** that evaluates hard gates and customer persona before any weighted scoring begins.

### Tier 1: HARD GATES (binary pass/fail, score = 0, no Claude call)
- Acquired, merged, shut down, or defunct
- PE/Growth Equity backed
- Fortune 500 subsidiary
- Employee count > 200 (CS function already exists)
- Total funding > $500M
- Valuation > $500M (unicorn scale)
- Public company
- Series D+ stage

### Tier 2: SECTOR GATES (also hard DQ)
- Biotech/pharma (drug development, clinical trials)
- Hardware/Physical product (sensors, devices, manufacturing)
- AgTech/Aquaculture (farming, fishery, livestock)
- Climate tech hardware (solar panels, EV infrastructure, carbon capture)
- Crypto/Web3 (blockchain, DeFi, NFT)
- HR Tech/DEI (workforce analytics, recruiting platforms)
- Consumer/B2C/Telehealth (DTC, patient apps, e-commerce)

### Tier 3: SOFT GATES (flag but still evaluate)
- Employee count < 15 (too early, pre-CS inflection)

### Tier 4: WARNING FLAGS (don't disqualify, flag for human review)
- Employee count 150-200 (penalty zone - CS function may exist)
- Data inconsistencies:
  - Seed stage with > $20M funding
  - Series C/D with < 10 employees
  - Series D with < $20M funding

### Tier 5: CUSTOMER PERSONA GATE (v8.4)
After passing Tiers 1-4, companies are classified by customer persona:
- **business-user**: End users are non-technical (sales, marketing, HR, finance, healthcare providers, legal)
- **developer**: End users are developers, engineers, DevOps, SRE, data engineers
- **mixed**: Both personas are equally important

**Developer-as-customer auto-pass logic:**
- Developer persona + <50 employees → Auto-pass (not at enterprise scale)
- Developer persona + 50+ employees + <2 enterprise signals → Auto-pass
- Developer persona + 50+ employees + 2+ enterprise signals → **Proceed** (enterprise exception)
- Business-user or mixed → **Proceed** to weighted scoring

**Enterprise signals that grant exception:**
- SOC 2, HIPAA, compliance mentions
- Fortune 500/1000 customers
- Enterprise sales team, account executives
- SSO, SAML, multi-tenant
- Self-hosted, on-premise options
- Contract value, ACV, ARR mentions
- Procurement, vendor management

**New Airtable field:** `Customer Persona` (single-select: business-user, developer, mixed)

**Expanded PE/Growth Equity firm list** (v2):
Vista Equity, Thoma Bravo, KKR, Blackstone, Bain Capital, Silver Lake, Apollo, Insight Partners, Clearlake, TA Associates, Brighton Park Capital, General Atlantic, Warburg Pincus, Francisco Partners, Summit Partners, Providence Equity, Welsh Carson, TPG Capital, Hellman & Friedman, Advent International, Permira, EQT Partners, Carlyle, SoftBank Vision Fund

**Disqualified records**:
- Score set to 0, Status to "Auto-Disqualified"
- `Disqualify Reasons` field populated with specific reasons
- `Summary` field shows "Auto-disqualified: {reasons}"
- Enriched fields (Stage, Funding, Employee Count) still updated

**Workflow flow**:
```
Enrich → Pre-Filter → Check DQ?
  ├── Yes (disqualified) → Update (score=0, no evaluation)
  └── No → Classify Persona → Check Developer Auto-Pass?
           ├── Yes (developer, no enterprise exception) → Update (score=0, developer-as-customer)
           └── No → Prompt → Claude → Parse → Update (scored)
```

**Expected savings**: ~50-60% reduction in Claude API calls (hard gates + persona gate)

---

## v9 Full Redesign (Mar 2026)

The v9 pipeline addresses a 4% signal rate (1/25 companies worth pursuing) by adding multiple new gates and enhanced detection patterns.

### v9 Architecture Overview

```
INPUT (company from scraper)
    ↓
PHASE 0: ENTITY VALIDATION (NEW)
    • Catches non-companies (podcasts, media, nonprofits)
    ↓
PHASE 1: ENRICHMENT (Brave Search)
    • Enhanced acquisition detection (PE portfolio patterns)
    • GTM motion extraction (PLG vs enterprise signals)
    • Software-first check (not services/hardware)
    • Stale company detection (shrinking headcount)
    ↓
PHASE 2: PRE-EVALUATION GATES
    • Tier 1: Hard gates (acquired, PE, >200 emp, >$500M, public, Series D+, non-US)
    • Tier 2: Sector gates (biotech, hardware, crypto, consumer, HR, not software-first)
    • Tier 3: GTM motion gates (PLG-dominant, pre-sales function)
    • Tier 4: Stale company gate (3+ years since funding, shrinking signals)
    • Tier 5: Soft gates (too early <15 employees)
    ↓
PHASE 3: PERSONA CLASSIFICATION
    • business-user, employee-user, developer, mixed
    • Developer/employee-user auto-pass (unless enterprise exception)
    ↓
PHASE 4: CS HIRE READINESS THRESHOLD (NEW)
    • Quick Claude call to check CS hire need
    • Must score >= 10 to proceed
    ↓
PHASE 5: FULL EVALUATION
    • 100-point scoring with domain distance modifier (-10 to +5)
    • APPLY/WATCH/PASS bucketing
    ↓
OUTPUT (Airtable record with score + status)
```

### v9 New Disqualification Reasons

- `Invalid entity (media/podcast/nonprofit)`
- `Non-US primary market`
- `Not software-first (services business)`
- `Not software-first (hardware with software)`
- `PLG-dominant (no enterprise CS need)`
- `Pre-sales function company`
- `Stale company (3+ years since funding)`
- `Shrinking headcount signals`
- `CS Hire Readiness below threshold`

### v9 Domain Distance Scoring

Applied as a modifier after base scoring:

**High-distance domains** (subtract 5-10 points):
- IT Operations/ITSM: -8
- Physical Security: -10
- Vertical Retail POS: -8
- Financial Compliance/RegTech: -6
- Legal Tech: -6
- Real Estate Tech: -7
- Construction Tech: -7

**Target domains** (add 0-5 points):
- Healthcare B2B SaaS (provider-side): +5
- Patient Engagement (B2B2C): +3
- Clinical Operations: +5
- Care Coordination: +4
- Developer Tools/DevOps: +2

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

---

## n8n Airtable Node Bug (Mar 2026)

**Problem:** The n8n Airtable node exhibits data scrambling when updating records in batch or via Execute Workflow. The `_updateRecordId` field is cached or evaluated incorrectly, causing the wrong record to be updated.

**Symptoms:**
- Input shows Record A, but Record B gets updated
- All records update the same (first) row
- Set nodes and `first()` accessors don't fix the issue
- Execute Workflow subworkflows make it worse due to state leakage

**Root Cause:** n8n's Airtable node expression evaluation appears to cache record IDs or evaluate them incorrectly when processing multiple items. This is exacerbated by Execute Workflow state leakage.

**Solution: HTTP Request Bypass**

Instead of using the Airtable node for updates, use HTTP Request with the record ID embedded directly in the URL:

```javascript
// URL pattern (RECORD_ID in path, not body)
https://api.airtable.com/v0/{baseId}/{tableName}/{RECORD_ID}

// Example expression
https://api.airtable.com/v0/appFEzXvPWvRtXgRY/Funding%20Alerts/{{ $json.RECORD_ID }}
```

**HTTP Request Configuration:**
- Method: PATCH
- Authentication: Header Auth
  - Name: `Authorization`
  - Value: `Bearer {your_pat_token}`
- Body Content Type: JSON
- Body: `{ "fields": { ... } }` (no `id` field needed - it's in the URL)

**Workflow Status (Mar 2026):**
| Workflow | Status | Notes |
|----------|--------|-------|
| Funding Alerts Rescore v4.10 | **ACTIVE** | v4.10: Gate tightening (employee 200, funding $150M), data sufficiency, duplicate output fix. v4.9.2: DQ tripling fix |
| Enrich & Evaluate Pipeline v9.14 | **ACTIVE** | v9.14: Bucket enforcement, VC category labels, score floor detection, business model classification |
| Job Evaluation Pipeline v6.8 | **ACTIVE** | v6.8: P0 fix (isPEBacked order). v6.7: Merger/rebrand detection |
| Enrich & Evaluate Pipeline v8.5 | **ROLLBACK** | Keep for rollback if needed |

---

## Session Hygiene

At the end of any substantive session, generate a wrap-up before the user disconnects. This prevents knowledge from dying in the terminal.

### End-of-Session Checklist

1. **Artifacts:** List every file created or modified this session with version numbers (before → after). New files need an Artifact Registry entry in Airtable (base appFO5zLT7ZehXaBo, table tblcE723hIH692lSy).

2. **Decisions:** Bullet any architectural, strategic, or design decisions made. One sentence each: what was decided and why.

3. **CONTEXT update:** Draft the specific text to add or replace in this repo's CONTEXT file. Write the actual paragraph, not a vague reminder. For job_search, update CONTEXT-job-search.md (in Claude.ai Job Search 2 knowledge).

4. **Commit:** Stage and commit with a descriptive message. Group related changes. Don't bundle unrelated work.

5. **Memory flag:** If anything changed that should persist in Claude.ai memory (stable facts, tool configs, project structure), note it explicitly so the user can add it in their next Claude.ai session.

### Versioning

All artifacts use semantic versioning (v1.0, v1.1, v2.0). Track in filenames or internal version constants. Bump on every meaningful change.

### What Goes Where

- **Git (this repo):** Code, workflow JSON, specs, config, strategy docs
- **Airtable Artifact Registry:** Row for every versioned artifact with location and git status
- **Claude.ai CONTEXT files:** Living state summaries, updated via session wrap-up
- **Claude.ai memory:** Stable personal facts, tool configs, project structure (slow-changing)
- **Local only (gitignored):** Signed legal documents, credentials, API keys
