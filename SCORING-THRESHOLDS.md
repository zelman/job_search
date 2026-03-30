# SCORING-THRESHOLDS.md -- Single Source of Truth

**Last updated:** March 30, 2026
**Pipeline version at last update:** v9.16 / Rescore v4.15
**Owner:** Eric Zelman

This file is the canonical reference for every threshold, gate, cap, and business rule in the Tide Pool scoring pipeline. When code and this file disagree, this file wins. Every pipeline change that touches thresholds MUST update this file first.

**Config-Driven Architecture (v4.13):** Rescore thresholds are now stored in Airtable Config table (`tblofzQpzGEN8igVS`). To modify thresholds, edit the Config table - no code changes needed.

**Consumed by:**
- Enrich & Evaluate Pipeline (n8n) -- `Parse Enrichment` node
- Funding Alerts Rescore (n8n) -- `Parse Enrich` node (reads from Config table via Config Fetcher)
- Claude Code during implementation and review
- Business Logic Audit prompt (see AUDIT-PROMPT.md)

---

## Target Profile (the "why" behind every number)

| Criterion | Target | Rationale |
|---|---|---|
| Company stage | Series A / Series B | Sweet spot where CS playbook doesn't exist yet |
| Employee count | 20-100 | Small enough that founder-led CS is breaking down |
| Total funding | Under ~$75M | Above seed (real revenue), below growth stage (established functions) |
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
| Employee count (hard cap) | > 150 | `Too large (>150 employees: {n})` |
| Total funding (hard cap) | > $75M | `>$75M funding ({amount})` |
| Unicorn valuation | >= $1B | `Unicorn valuation (>$1B: {amount})` |
| High valuation | > $500M (and < $1B) | `>$500M valuation ({amount})` |
| PE-backed | Any PE firm match | `PE-backed ({firm})` |
| Public company | IPO detected | `Public company` |
| **Stage gate (NEW)** | Series C or later | `Past target stage ({stage})` |
| **Mature scale indicators** | employees > 500 OR funding > $200M OR valuation > $500M (when stage unknown) | `Scale indicators exceed target range` |
| Late stage | Series D or Series E | `Late stage ({stage})` |
| Acquired | Acquisition detected | `Acquired (by {acquirer})` |
| Fortune 500 subsidiary | Parent company match | `Fortune 500 subsidiary ({parent})` |
| Known large company | Hardcoded list match | `Known large company (enrichment bypass)` |
| Company too old | > 8 years since founding/batch | `Company too old ({age} years)` |
| **Company too mature** | > 12 years since founding | `Company founded {year} — too mature` |
| Too early | < 15 employees | `Too early (<15 employees)` |
| Data insufficient | < 2 of 5 data points | `Insufficient enrichment data (N/5 data points)` |

### Stage Gate (Tier 1 Hard Gate) - NEW v9.15/v4.14

Series C and later-stage companies are auto-PASSed before scoring begins.

**Gate Logic:**

1. **Stage is Series C or later** → auto-PASS
   - Matches: `series c`, `series d`, `series e`, `series f`, `growth`, `late stage`, `late-stage`, `ipo`, `pre-ipo`, `public`, `publicly traded`
   - Reason: `Past target stage ({stage})`

2. **Stage unknown but scale indicators exceed target** → auto-PASS
   - Triggers when ANY of: employees > 500 OR total_raised > $200M OR valuation > $500M
   - Reason: `Scale indicators exceed target range despite unknown stage`

3. **Founded more than 12 years ago** → auto-PASS
   - Uses current year - founded_year calculation
   - Reason: `Company founded {year} — too mature for founding hire opportunity`

4. **Exception: Series C + small + active CS hire + no existing CS team** → MANUAL_REVIEW (rare)
   - All conditions must be true: Series C, under 150 employees, active CS leadership posting detected, no existing CS team identified
   - Reason: `Series C but small with active CS leadership hire — manual review`

### Sector Gates (also hard DQ)

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

### VC Category Gates

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

## Soft Caps (warnings + score penalties, not DQ)

| Condition | Range | Effect |
|---|---|---|
| Employee count (soft zone) | 100-150 | Warning + headcount penalty modifier (-10, or 0 if rebuild signal) |
| Total funding (soft zone) | $50M-$75M | Warning logged |
| Founded pre-2016 | Founded year < 2016 | Warning logged |
| Aging company | 5-8 years old | Warning (not DQ, review manually) |
| Non-US based | Geography detection | Warning + soft penalty |
| Contraction signals | Detected in enrichment | Warning logged |
| Stale funding + enterprise | Stale but has enterprise motion | Warning (not DQ) |
| Developer persona (passed gate) | Developer customer but 50+ employees or enterprise motion | Warning logged |
| CX tooling company | Sells TO support teams | Warning logged |
| Suspicious employee count | Cross-ref mismatch | Warning logged |
| Funding staleness | Years since last round | Score modifier (negative) |

---

## Score Thresholds (Phase 5 bucket assignment)

| Score Range | Bucket | Airtable Status |
|---|---|---|
| >= 70 | APPLY | Apply |
| 40-69 | WATCH | Monitor |
| < 40 | PASS | Passed |

**Overrides:**
- CX Job Posting found OR Network Connection found: Status escalated to `Apply` regardless of score

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
| Rebuild bonus | `rebuild_signal` detected | +20 points (applied before caps) |
| CS likelihood cap (unlikely) | `cs_hire_likelihood === 'unlikely'` | Score capped at 65 |
| CS likelihood cap (low) | `cs_hire_likelihood === 'low'` | Score capped at 75 |
| Headcount penalty | 150-200 employees, no rebuild signal | -10 points |
| Funding staleness | Years since last round | Negative modifier from enrichment |
| Default score detection | Score 55-65, cs_readiness <= 10, likelihood low/unlikely | Safety-cap to 30, force PASS |

---

## Data Sufficiency Requirements

| Data Point | Source |
|---|---|
| Employee count | Brave Search extraction |
| Funding stage | Brave Search extraction |
| Total funding (numeric) | Brave Search extraction |
| Founded year or YC batch | Brave Search extraction |
| Description | VC scraper or Airtable (>50 chars) |

**Minimum:** At least 2 of 5 data points present to proceed to scoring.
**< 2 of 5 = DQ** with reason "Insufficient enrichment data (N/5 data points)."
**2-3 of 5 = sparse data** (proceeds but may score low due to missing signals).

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

## Sync Contract

The following workflows MUST use identical threshold values. When this file is updated, both must be updated in the same commit/deploy:

| Threshold | v9.16 Location | v4.15 Location |
|---|---|---|
| HARD_EMPLOYEE_CAP (150) | `Parse Enrichment` constants (v9.16 aligned) | **Airtable Config table** |
| HARD_FUNDING_CAP ($75M) | `Parse Enrichment` constants (v9.16 aligned) | **Airtable Config table** |
| SOFT_EMPLOYEE_CAP (100) | `Parse Enrichment` constants (v9.16 aligned) | **Airtable Config table** |
| SOFT_FUNDING_CAP ($50M) | `Parse Enrichment` constants (v9.16 aligned) | **Airtable Config table** |
| Score thresholds (70/40) | `Parse Evaluation` lines ~64-66 | **Airtable Config table** |
| CS Readiness ceiling (25) | `Parse CS Readiness` | **Airtable Config table** |
| PE firm list | `Parse Enrichment` array | **Airtable PE Firms table** |
| Known large companies | `Parse Enrichment` array | `Parse Enrich` array (hardcoded) |
| Sector gate keywords | `Parse Enrichment` | `Parse Enrich` (hardcoded) |

**Note:** v4.15 Rescore is config-driven. Edit Airtable Config table (`tblofzQpzGEN8igVS`) to change thresholds. Enrich & Evaluate Pipeline v9.16 hardcoded values are now aligned with Config table as of Mar 30, 2026.

---

## Changelog

| Date | Version | Change | Reason |
|---|---|---|---|
| 2026-03-30 | v4.15 | **isRescore bug fix**. When record was previously DQ'd (score=0, DQ reasons populated), both pre-existing copy AND detection blocks were skipped, leaving disqualifiers empty. Record would go through scoring path, overwriting Status=Auto-Disqualified with Status=Monitor. Fix: Handle isRescore case explicitly to preserve DQ status. | InVision (Series D, unicorn, founded 2011) had 5 DQ reasons but Status=Monitor, Score=62 instead of Auto-Disqualified. |
| 2026-03-30 | v9.16 | **Threshold alignment + stage gate fallback**. HARD_EMPLOYEE_CAP 200->150, HARD_FUNDING_CAP $150M->$75M, soft caps aligned. Stage gate now checks sourceStage (Airtable/source data) as fallback when Brave Search doesn't extract stage. | Companycam (Series C), People.ai (Series D), Reveal (Series E), Twin Health (Series E) passing through to Apply/Monitor despite stage gate existing in v9.15. Gate was blind to non-Brave stage data. Thresholds drifted from spec during v9.14 tightening. |
| 2026-03-29 | v9.15/v4.14 | **Stage Gate + Mature Company Detection**. Series C+ auto-PASS. Scale indicators gate (>500 emp, >$200M, >$500M valuation). Founded >12 years gate. | Bullhorn, Weights & Biases, Gtmhub scoring 52-62 instead of auto-PASS. Stage evaluated as scoring dimension instead of binary disqualifier. |
| 2026-03-25 | v4.13 | **Config-driven architecture**. Thresholds moved to Airtable Config table. PE firms moved to PE Firms table. Employee cap 150, funding cap $75M, soft caps 100/$50M. | Single source of truth, non-engineer editable, no code deploys for threshold changes. |
| 2026-03-25 | v4.12 | DQ duplication fix - detection wrapped in `if (!existing_dq_reasons)` | DQ reasons were accumulating on each rescore run. |
| 2026-03-25 | v4.11 | Gate tightening: employee 150, funding $75M, PE acquisition detection, hardware/deeptech keywords, funding-per-head ratio | False positives: HouseRx ($270M, 170 emp), SmarterDx (PE-backed), Veir (hardware), Gumloop ($70M/24 emp). |
| 2026-03-24 | v9.14 / v4.10 | Employee hard cap 350->200, funding hard cap $500M->$150M, soft caps adjusted, data sufficiency gate added, CS readiness ceiling enforced in code | 25+ false positives at score 78 + Auto-DQ. Gates 2-3x more permissive than actual criteria. |
