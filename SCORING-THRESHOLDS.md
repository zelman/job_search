# SCORING-THRESHOLDS.md -- Single Source of Truth

**Last updated:** April 11, 2026
**Pipeline version at last update:** v10.0 / Rescore v5.0
**Owner:** Eric Zelman

This file is the canonical reference for every threshold, gate, cap, and business rule in the Tide Pool scoring pipeline. When code and this file disagree, this file wins. Every pipeline change that touches thresholds MUST update this file first.

**Config-Driven Architecture (v4.13+):** Rescore thresholds are stored in Airtable Config table (`tblofzQpzGEN8igVS`). To modify thresholds, edit the Config table - no code changes needed.

**Consumed by:**
- Enrich & Evaluate Pipeline (n8n) -- `Parse Enrichment` node
- Funding Alerts Rescore (n8n) -- `Parse Enrich` node (reads from Config table via Config Fetcher)
- Claude Code during implementation and review
- Business Logic Audit prompt (see AUDIT-PROMPT.md)

---

## Target Profile (the "why" behind every number)

| Criterion | Target | Rationale |
|---|---|---|
| Company stage | Series A / Series B / Early Series C | Sweet spot where CS playbook doesn't exist yet |
| Employee count | 20-200 (sweet spot), 200-300 (acceptable) | Small enough that founder-led CS is breaking down |
| Total funding | Under ~$200M | Above seed (real revenue), below growth stage (established functions) |
| Role type | Builder (0-to-1) | Not manage-and-optimize |
| Customer persona | Business users / employees | Not developer-as-customer (under ~50 employees) |
| GTM motion | Enterprise or hybrid | Not PLG-dominant |
| Business model | B2B SaaS | Not services, hardware, marketplace, consumer |
| Geography | US-based preferred | Non-US = soft penalty, not DQ |

---

## Hard DQ Gates (auto-disqualify, no scoring)

These fire in Phase 2 (Pre-Evaluation Gates). If ANY condition is true, the company is DQ'd and never reaches Claude for scoring.

| Gate | Threshold | DQ Reason String |
|---|---|---|
| Employee count (hard cap) | > 1000 | `Too large (>1000 employees: {n})` |
| Total funding (hard cap) | > $200M | `>$200M funding ({amount})` |
| Unicorn valuation | >= $1B | `Unicorn valuation (>$1B: {amount})` |
| High valuation | > $500M (and < $1B) | `>$500M valuation ({amount})` |
| PE-backed | Any PE firm match | `PE-backed ({firm})` |
| Public company | IPO detected | `Public company` |
| Late stage | Series D or later | `Late stage ({stage})` |
| Acquired | Acquisition detected | `Acquired (by {acquirer})` |
| Fortune 500 subsidiary | Parent company match | `Fortune 500 subsidiary ({parent})` |
| Known large company | Hardcoded list match | `Known large company (enrichment bypass)` |
| Company too mature | > 12 years since founding | `Company founded {year} — too mature` |
| IC title at 300+ company | IC role (Specialist, Associate, Coordinator) at 300+ emp | `IC title at large company (auto-DQ)` |

### Series C Gate (v10 - Manual Review Path)

Series C companies are NO LONGER auto-DQ'd. Instead:

1. **Series C + <300 employees** → Flag for MANUAL_REVIEW, proceed to scoring
   - Reason: `Series C but small ({employees} emp) — manual review`
   - These companies often need CS rebuild/transformation

2. **Series C + 300+ employees** → auto-PASS (soft DQ)
   - Reason: `Series C at scale (>{employees} employees)`

3. **Series D or later** → Hard DQ (no change)
   - Reason: `Late stage ({stage})`

### Data Quality Gate (v10 - No More Zero Scores)

**Previous behavior:** Companies with <2/5 data points → auto-DQ with score 0

**New behavior (v10):**
- **<2/5 data points** → Score 40-45 (WATCH), flag `NEEDS MANUAL REVIEW`
- **Conflicting data** (e.g., 16 employees + $475M funding) → Score 40-45 (WATCH), flag `DATA CONFLICT - VERIFY`
- Do NOT apply dealbreaker penalties when underlying data is clearly wrong or missing
- Incomplete data is not disqualifying; it requires human judgment

### Sector Gates (hard DQ - unchanged)

| Sector | Gate Variable |
|---|---|
| Biotech/pharma | `isBiotech` |
| Hardware/physical product | `isHardware`, `isClimateHardware` |
| AgTech/aquaculture | `isAgTech` |
| Crypto/Web3 | `isCrypto` |
| HR Tech/DEI | `isHRTech` |
| Consumer/B2C/telehealth | `isConsumer` |
| Marketplace | `isMarketplace` |
| IoT/connected devices | `isIoT` |
| Materials/manufacturing | `isMaterials` |
| Healthcare care delivery | `isHealthcareCareDelivery` |
| Medical device | `isMedicalDevice` |
| Cybersecurity | `isCybersecurity` |
| Legal tech | `isLegalTech` |
| Ed-tech | `isEdTech` |
| Property management | `isPropertyManagement` |
| Tax automation | `isTaxTech` |
| Sales tools | `isSalesTools` |
| Veterinary | `isVeterinary` |
| Fintech/banking | `isFintech` |
| Construction tech | `isConstructionTech` |
| Food science/CPG | `isFoodBiotech` |
| Physical security | `isPhysicalSecurity` |
| Insurtech | `isInsurtech` |
| SaaS management/IT spend | `isSaaSManagement` |
| Consumer digital health | `isConsumerDigitalHealth` |
| AI calling/voice agent | `isAICalling` |
| Services business | `isServicesBusiness` |
| Hardware masquerading | `isHardwareMasquerading` |
| PLG-dominant | `isPLGDominant` |
| Pre-sales company | `isPresalesCompany` |
| Developer-as-customer (small) | `isDeveloperCustomerDQ` |
| Stale funding (no enterprise) | `isStaleFunding && !hasEnterpriseMotion` |
| Shrinking headcount | `hasShrinkingSignals` |

### VC Category Gates (unchanged)

| Category | Gate Variable |
|---|---|
| Water tech | `isVCWaterTech` |
| Climate tech (non-SaaS) | `isVCClimateTechNonSaaS` |
| Life sciences | `isVCLifeSci` |
| Nuclear energy | `isVCNuclear` |
| Logistics (non-SaaS) | `isVCLogisticsNonSaaS` |
| DTC/beauty/consumer | `isVCDTC` |
| Investment/financial AI | `isVCInvestmentAI` |
| Headless commerce/Shopify | `isVCHeadlessCommerce` |

---

## Title Gate (v10 NEW - Context-Dependent by Company Size)

**Previous behavior:** -15 pt penalty for non-Director/VP/Head titles across all companies.

**New behavior (v10):** Tiered penalties based on company size. The same title means different things at different company sizes.

### Title Penalty Matrix

| Title Tier | <50 employees | 50-150 employees | 150-300 employees | 300+ employees |
|---|---|---|---|---|
| VP / Head of / Director | 0 | 0 | 0 | 0 |
| Senior Manager / Lead | 0 | 0 | -5 pts | -10 pts |
| Manager / CSM | 0 | -5 pts | -10 pts | -15 pts |
| IC titles (Specialist, Associate, Coordinator) | -5 pts | -10 pts | -15 pts | **auto-DQ** |

**Title detection patterns:**
- VP / Head / Director: `/\b(VP|Vice President|Head of|Director)\b/i`
- Senior Manager / Lead: `/\b(Senior Manager|Lead|Principal)\b/i`
- Manager / CSM: `/\b(Manager|CSM|Customer Success Manager)\b/i` (without Senior)
- IC: `/\b(Specialist|Associate|Coordinator|Representative|Agent|Analyst)\b/i`

### Builder Phrase Override (v10 NEW)

If job description contains ANY builder signal phrase, **add +15 pts AND override any title penalty entirely**, regardless of company size:

**Builder signal phrases:**
- "build from scratch" / "build from the ground up"
- "first hire" / "founding"
- "greenfield" / "0 to 1" / "zero to one"
- "stand up the function" / "establish the team"
- "no existing team" / "first customer-facing hire"
- "define the playbook" / "create the process"

**Detection pattern:**
```javascript
const BUILDER_PHRASES = [
  /build\s+from\s+(scratch|the\s+ground\s+up)/i,
  /first\s+(hire|cs|customer\s+success|support)/i,
  /\bfounding\b/i,
  /\bgreenfield\b/i,
  /\b(0|zero)\s*(-|to)\s*(1|one)\b/i,
  /stand\s+up\s+(the\s+)?(function|team|org)/i,
  /establish\s+(the\s+)?(team|function|org)/i,
  /no\s+existing\s+(cs\s+)?team/i,
  /first\s+customer[- ]facing\s+hire/i,
  /define\s+(the\s+)?playbook/i,
  /create\s+(the\s+)?process/i
];
```

This is the single strongest positive signal in the pipeline.

---

## Company Size Gates (v10 - Widened)

| Gate | v9.18 Value | v10 Value | Effect |
|---|---|---|---|
| Employee hard cap (auto-DQ) | 150 | **1000** | Above 1000 = auto-DQ |
| Employee heavy penalty zone | N/A | **300-1000** | -10 pts |
| Employee soft penalty zone | 100-150 | **200-300** | -5 pts |
| Target sweet spot (full bonus) | 0-150 | **0-200** | Full positive signal |
| Target extended (half bonus) | N/A | **200-300** | Half positive signal |
| Minimum employees | 15 | 15 (no change) | Below 15 = auto-DQ |

**Rationale:** Opens the "rebuild/transform" category — companies 150-300 employees that have a CS function but need someone to fix it. These were previously filtered out entirely.

**Code constants:**
```javascript
const HARD_EMPLOYEE_CAP = 1000;        // v10: Was 150. Above 1000 = auto-DQ
const HEAVY_PENALTY_EMPLOYEE = 300;   // v10 NEW: 300-1000 gets -10 pts
const SOFT_EMPLOYEE_CAP = 200;        // v10: Was 100. 200-300 gets -5 pts
const MIN_EMPLOYEES = 15;             // No change
```

---

## Funding Gates (v10 - Widened)

| Gate | v9.18 Value | v10 Value | Effect |
|---|---|---|---|
| Funding hard cap (auto-DQ) | $75M | **$200M** | Above $200M = auto-DQ |
| Funding soft penalty zone | $50M-$75M | **$200M-$500M** | -10 pts, warning logged |
| Target sweet spot | Under $75M | **Under $200M** | No penalty |

**Rationale:** Series B rounds in 2025-2026 are regularly $40-80M. A company that raised $120M total across Seed + A + B is not late-stage. The $75M cap was filtering these out incorrectly.

**Code constants:**
```javascript
const HARD_FUNDING_CAP = 200000000;    // v10: Was $75M. Above $200M = auto-DQ
const SOFT_FUNDING_CAP = 200000000;    // v10: $200M-$500M gets -10 pts and warning
const HEAVY_FUNDING_CAP = 500000000;   // v10 NEW: Above $500M = major penalty
const MAX_VALUATION = 500000000;       // No change - $500M+ valuation is DQ
```

---

## Function Widening (v10 NEW)

The following function titles should score as positively as CS/Support titles:

| Function | Notes |
|---|---|
| Customer Success | Already included |
| Implementation / Onboarding | First-hire opportunity at many companies |
| Professional Services | Often the build-from-scratch role |
| Solutions Consulting / Solutions Engineering | Customer-facing, post-sales (NOT pre-sales) |
| Client Services / Client Experience | Alternate naming for CS |
| Customer Operations | Ops role that often leads CS |

**Detection patterns:**
```javascript
const VALID_CS_FUNCTIONS = [
  /customer\s*(success|support|experience|service|care)/i,
  /\b(implementation|onboarding)\b/i,
  /professional\s*services/i,
  /solutions?\s*(consulting|engineer)/i,  // Post-sales only
  /client\s*(services?|experience)/i,
  /customer\s*operations/i
];
```

**DO NOT INCLUDE:**
- Pre-sales SE / Sales Engineering
- Pure Account Management (AM without CS)
- Marketing
- Product Management

Same title-tier logic from the Title Gate applies to these functions.

---

## Soft Caps (warnings + score penalties, not DQ)

| Condition | Range | Effect |
|---|---|---|
| Employee count (soft zone) | 200-300 | Warning + -5 pts |
| Employee count (heavy zone) | 300-1000 | Warning + -10 pts |
| Total funding (soft zone) | $200M-$500M | Warning + -10 pts |
| Series C (small) | Series C + <300 employees | Warning, proceed to scoring, flag for review |
| Founded pre-2016 | Founded year < 2016 | Warning logged |
| Aging company | 5-8 years old | Warning (not DQ, review manually) |
| Company too old | > 8 years since founding/batch | Warning + review |
| Non-US based | Geography detection | Warning + soft penalty |
| Contraction signals | Detected in enrichment | Warning logged |
| Stale funding + enterprise | Stale but has enterprise motion | Warning (not DQ) |
| Developer persona (passed gate) | Developer customer but 50+ employees or enterprise motion | Warning logged |
| CX tooling company | Sells TO support teams | Warning logged |
| Suspicious employee count | Cross-ref mismatch | Warning logged |
| Funding staleness | Years since last round | Score modifier (negative) |
| Data incomplete | <2/5 data points | Score 40-45 (WATCH), flag for manual review |
| Data conflicting | Cross-ref mismatch | Score 40-45 (WATCH), flag for verification |

---

## Score Thresholds (Phase 5 bucket assignment)

| Score Range | Bucket | Airtable Status |
|---|---|---|
| >= 70 | APPLY | Apply |
| 40-69 | WATCH | Monitor |
| < 40 | PASS | Passed |

**Overrides:**
- CX Job Posting found OR Network Connection found: Status escalated to `Apply` regardless of score
- Builder phrase detected: +15 pts added before bucket assignment

---

## Scoring Weights (100-point scale)

| Category | Max Points | Weight |
|---|---|---|
| CS Hire Readiness | 25 | 25% |
| Stage & Size Fit | 25 | 25% |
| Role Mandate | 20 | 20% |
| Sector & Mission | 15 | 15% |
| Outreach Feasibility | 15 | 15% |

**Domain distance modifier:** +5 (healthcare B2B SaaS) to -10 (physical security)

---

## CS Readiness Scoring (Phase 4)

| Tier | Score | Condition |
|---|---|---|
| No CS function + active build signal | 25 | All evidence-based, no inference from stage |
| CS exists but no leader | 10 | IC CSMs visible, no VP/Head/Director |
| CS leadership in place | 0 | VP/Head/Director CS currently employed |
| No evidence found | 0 | Default. "No evidence" != "medium likelihood" |

**Hard ceiling:** 25 points. Code MUST cap at 25 regardless of what Claude returns.

**Role language disqualifier:** -15 points if NRR/GRR/renewal quota/expansion quota language found.

---

## Score Modifiers (applied post-scoring)

| Modifier | Condition | Effect |
|---|---|---|
| Builder phrase bonus | Builder signal phrase detected | **+15 points** (v10 NEW) |
| Title penalty | Based on title tier + company size | 0 to -15 pts (see Title Gate) |
| Rebuild bonus | `rebuild_signal` detected | +20 points (applied before caps) |
| CS likelihood cap (unlikely) | `cs_hire_likelihood === 'unlikely'` | Score capped at 65 |
| CS likelihood cap (low) | `cs_hire_likelihood === 'low'` | Score capped at 75 |
| Headcount penalty (heavy) | 300-1000 employees, no rebuild signal | -10 points |
| Headcount penalty (soft) | 200-300 employees, no rebuild signal | -5 points |
| Funding penalty (soft) | $200M-$500M funding | -10 points |
| Funding staleness | Years since last round | Negative modifier from enrichment |
| Default score detection | Score 55-65, cs_readiness <= 10, likelihood low/unlikely | Safety-cap to 30, force PASS |
| Incomplete data | <2/5 data points | Score 40-45 (WATCH), no DQ |

---

## Data Sufficiency Requirements

| Data Point | Source |
|---|---|
| Employee count | Brave Search extraction |
| Funding stage | Brave Search extraction |
| Total funding (numeric) | Brave Search extraction |
| Founded year or YC batch | Brave Search extraction |
| Description | VC scraper or Airtable (>50 chars) |

**v10 Behavior:**
- **<2/5 data points** → Score 40-45 (WATCH), flag `NEEDS MANUAL REVIEW`
- **2-3/5 data points** → Proceeds normally, may score low due to missing signals
- **Data conflict detected** → Score 40-45 (WATCH), flag `DATA CONFLICT - VERIFY`
- Do NOT auto-DQ for insufficient data

---

## Enrichment Sanity Bounds

| Field | Believable Range | Action if Out of Range |
|---|---|---|
| Total funding | $100K - $5B | Discard extracted value |
| Employee count | 1 - 50,000 | Discard extracted value |
| Founded year | 2000 - current year | Discard extracted value |
| Valuation | $100K - $50B | Discard extracted value |

In rescore workflow: if both extracted AND existing Airtable values fail sanity, set to null (don't perpetuate polluted data).

---

## What Stays the Same (Hard Gates - Do Not Touch)

These gates remain unchanged from v9.18:

- PE-backed: auto-disqualify
- 1000+ employees: auto-disqualify (raised from 150)
- Series D+: auto-disqualify
- Developer-as-customer at <50 employees: auto-disqualify
- Valuation >$1B: auto-disqualify
- Valuation >$500M: auto-disqualify
- NRR-first framing as opening mandate: flag (not auto-disqualify, but negative signal)

---

## Sync Contract

The following workflows MUST use identical threshold values. When this file is updated, both must be updated in the same commit/deploy:

| Threshold | v10 Location | v5 Location |
|---|---|---|
| HARD_EMPLOYEE_CAP (1000) | `Parse Enrichment` constants | **Airtable Config table** |
| HEAVY_PENALTY_EMPLOYEE (300) | `Parse Enrichment` constants | **Airtable Config table** |
| SOFT_EMPLOYEE_CAP (200) | `Parse Enrichment` constants | **Airtable Config table** |
| HARD_FUNDING_CAP ($200M) | `Parse Enrichment` constants | **Airtable Config table** |
| SOFT_FUNDING_CAP ($200M) | `Parse Enrichment` constants | **Airtable Config table** |
| Score thresholds (70/40) | `Parse Evaluation` lines ~64-66 | **Airtable Config table** |
| CS Readiness ceiling (25) | `Parse CS Readiness` | **Airtable Config table** |
| PE firm list | `Parse Enrichment` array | **Airtable PE Firms table** |
| Known large companies | `Parse Enrichment` array | `Parse Enrich` array (hardcoded) |
| Sector gate keywords | `Parse Enrichment` | `Parse Enrich` (hardcoded) |
| Title penalty matrix | `Parse Enrichment` | `Parse Enrich` |
| Builder phrases | `Parse Enrichment` | `Parse Enrich` |
| Valid CS functions | `Parse Enrichment` | `Parse Enrich` |

---

## Changelog

| Date | Version | Change | Reason |
|---|---|---|---|
| 2026-04-11 | v10.0 / v5.0 | **MAJOR APERTURE WIDENING**. (1) Title gate now context-dependent by company size - "Manager" at 20-person company gets no penalty. (2) Employee hard cap 150→1000, soft cap 100→200, new heavy penalty zone 300-1000. (3) Funding hard cap $75M→$200M, soft cap $200M-$500M. (4) Series C no longer auto-DQ if <300 employees - goes to manual review. (5) Incomplete data no longer zeros the score - scores 40-45 WATCH. (6) Function widening: Implementation, Professional Services, Solutions Consulting, Client Services, Customer Operations now valid. (7) Builder phrase override: +15 pts and title penalty waiver for "first hire", "greenfield", "0 to 1", etc. | 90-day job search deadline. Pattern analysis Feb-Apr 2026 showed pipeline burying good fits (Assort Health, Castor, PermitFlow, Baselayer) with 0-28 scores despite genuine fit. |
| 2026-03-30 | v4.15 | **isRescore bug fix**. When record was previously DQ'd (score=0, DQ reasons populated), both pre-existing copy AND detection blocks were skipped, leaving disqualifiers empty. Record would go through scoring path, overwriting Status=Auto-Disqualified with Status=Monitor. Fix: Handle isRescore case explicitly to preserve DQ status. | InVision (Series D, unicorn, founded 2011) had 5 DQ reasons but Status=Monitor, Score=62 instead of Auto-Disqualified. |
| 2026-03-30 | v9.18 | **Threshold alignment + stage gate fallback**. HARD_EMPLOYEE_CAP 200->150, HARD_FUNDING_CAP $150M->$75M, soft caps aligned. Stage gate now checks sourceStage (Airtable/source data) as fallback when Brave Search doesn't extract stage. | Companycam (Series C), People.ai (Series D), Reveal (Series E), Twin Health (Series E) passing through to Apply/Monitor despite stage gate existing in v9.15. Gate was blind to non-Brave stage data. Thresholds drifted from spec during v9.14 tightening. |
| 2026-03-29 | v9.15/v4.14 | **Stage Gate + Mature Company Detection**. Series C+ auto-PASS. Scale indicators gate (>500 emp, >$200M, >$500M valuation). Founded >12 years gate. | Bullhorn, Weights & Biases, Gtmhub scoring 52-62 instead of auto-PASS. Stage evaluated as scoring dimension instead of binary disqualifier. |
| 2026-03-25 | v4.13 | **Config-driven architecture**. Thresholds moved to Airtable Config table. PE firms moved to PE Firms table. Employee cap 150, funding cap $75M, soft caps 100/$50M. | Single source of truth, non-engineer editable, no code deploys for threshold changes. |
| 2026-03-25 | v4.12 | DQ duplication fix - detection wrapped in `if (!existing_dq_reasons)` | DQ reasons were accumulating on each rescore run. |
| 2026-03-25 | v4.11 | Gate tightening: employee 150, funding $75M, PE acquisition detection, hardware/deeptech keywords, funding-per-head ratio | False positives: HouseRx ($270M, 170 emp), SmarterDx (PE-backed), Veir (hardware), Gumloop ($70M/24 emp). |
| 2026-03-24 | v9.14 / v4.10 | Employee hard cap 350->200, funding hard cap $500M->$150M, soft caps adjusted, data sufficiency gate added, CS readiness ceiling enforced in code | 25+ false positives at score 78 + Auto-DQ. Gates 2-3x more permissive than actual criteria. |
