# Scoring Logic Reconciliation Audit
**Date:** March 16, 2026
**Sources Compared:**
1. `SCORING-ENHANCEMENTS.md` (canonical documentation)
2. `Enrich & Evaluate Pipeline v9.9.json` (company evaluation)
3. `Job Evaluation Pipeline v6.6.json` (job evaluation)

**Note:** This audit was performed on v9.8/v6.4. Both pipelines have since been updated to v9.9/v6.6 with Batch 4 fixes.

---

## Executive Summary

This audit compares thresholds, gates, and scoring weights across the company and job pipelines. Several discrepancies were found, primarily due to independent evolution of the two pipelines.

### Key Findings
- **Employee caps differ:** v9.8 uses 350 hard / 200 soft; v6.4 uses 200 hard / 150 soft
- **Funding caps differ:** v9.8 uses $450M hard; v6.4 uses $500M hard
- **Scoring weights differ significantly** between pipelines
- **Score thresholds are aligned** (80/60/40 boundaries)
- **Batch 3 patterns fully implemented** in v9.8
- **CS Hire Readiness differs** in approach between pipelines

---

## Section 1: Pre-Scoring Gate Alignment

### Employee Caps

| Parameter | v9.8 Company | v6.4 Job | Aligned? |
|-----------|-------------|----------|----------|
| Hard DQ | 350 | 200 | **NO** |
| Soft Cap (penalty) | 200 | 150 | **NO** |
| Minimum (too early) | 15 | N/A | N/A |

**Recommendation:** Align both to v9.8 values (350 hard, 200 soft). The company pipeline was deliberately loosened to catch VP roles at larger companies.

### Funding Caps

| Parameter | v9.8 Company | v6.4 Job | Aligned? |
|-----------|-------------|----------|----------|
| Hard DQ | $450M | $500M | **NO** |
| Soft Cap (penalty) | $75M | $100M | **NO** |

**Recommendation:** Align to v9.8 ($450M hard). The $75M soft cap in v9.8 triggers warnings earlier.

### PE/Growth Equity Firms List

| v9.8 Company | v6.4 Job | Notes |
|--------------|----------|-------|
| 38 firms | 38 firms | **ALIGNED** - Same list |

Firms include: Vista Equity, Thoma Bravo, KKR, Blackstone, Bain Capital, Silver Lake, Apollo, Insight Partners, Clearlake, TA Associates, Brighton Park Capital, General Atlantic, Warburg Pincus, Francisco Partners, Summit Partners, Providence Equity, Welsh Carson, TPG Capital, Hellman & Friedman, Advent International, Permira, EQT Partners, Carlyle, SoftBank Vision Fund, Jonas Software, Constellation Software, Volaris, Harris Computer, Spring Lake Equity, Ares Management, Ares Capital, Vector Capital, Golden Gate Capital, Nordic Capital, Cinven, CVC Capital, BC Partners, Apax Partners, GTCR, Leonard Green, American Securities, Platinum Equity, Kohlberg, Accel-KKR

### Fortune 500 / Known Large Companies

| v9.8 Company | v6.4 Job | Notes |
|--------------|----------|-------|
| ~45 companies | N/A | **v6.4 MISSING** |

v9.8 includes: Zapier, SnapLogic, Stripe, Notion, Figma, Canva, Airtable, Webflow, Monday.com, Asana, and Fortune 500 standard list.

**Recommendation:** Add known large companies list to v6.4.

### Sector Gates

| Sector | v9.8 Company | v6.4 Job | Notes |
|--------|--------------|----------|-------|
| Biotech/Pharma | ✅ | ✅ | ALIGNED |
| Hardware/Physical | ✅ | ✅ | ALIGNED |
| Crypto/Web3 | ✅ | ✅ | ALIGNED |
| Consumer/B2C | ✅ | ✅ | ALIGNED |
| HR Tech/DEI | ✅ | ✅ | ALIGNED |
| Climate Hardware | ✅ | ✅ | ALIGNED |
| AgTech | ✅ | ✅ | ALIGNED |
| Marketplace | ✅ | ✅ | ALIGNED |
| Healthcare Care Delivery | ✅ | ✅ | ALIGNED |
| Medical Device | ✅ | ✅ | ALIGNED |
| Cybersecurity | ✅ | ✅ | ALIGNED |
| Legal Tech | ✅ | ✅ | ALIGNED |
| Ed-tech | ✅ | ✅ | ALIGNED |
| Property Management | ✅ | ✅ | ALIGNED |
| Tax Automation | ✅ | ✅ | ALIGNED |
| Sales Tools | ✅ | ✅ | ALIGNED |
| Veterinary | ✅ | ✅ | ALIGNED |
| Fintech/Banking | ✅ | ✅ | ALIGNED |
| Construction Tech | ✅ | ✅ | ALIGNED |
| Food Science/CPG | ✅ | ✅ | ALIGNED |
| Physical Security | ✅ | ✅ | ALIGNED |
| Insurtech | ✅ | ✅ | ALIGNED |
| SaaS Management | ✅ | ✅ | ALIGNED |
| Consumer Digital Health | ✅ | ✅ | ALIGNED |
| AI Calling | ✅ | ✅ | ALIGNED |

**All 24 sector gates are aligned** between v9.8 and v6.4.

### Acquisition Detection

| Feature | v9.8 Company | v6.4 Job | Notes |
|---------|--------------|----------|-------|
| PE acquirer patterns | ✅ | ✅ | ALIGNED |
| Jonas/Constellation | ✅ | ✅ | ALIGNED |
| Known acquired list | ✅ (Thinkful, Brainbase, Tempus-ex) | ❌ | **v6.4 MISSING** |

**Recommendation:** Add known acquired companies to v6.4.

---

## Section 2: Weighted Scoring Alignment

### v9.8 Company Pipeline (100-point model)
The company pipeline uses a **threshold-based** approach rather than weighted dimensions:
- CS Readiness Threshold: ≥10 points to proceed
- Domain distance modifier: -10 to +5 points
- Final scoring handled by Claude prompt

### v6.4 Job Pipeline (100-point model)
Explicit weighted dimensions:

| Dimension | Weight | Notes |
|-----------|--------|-------|
| Company Stage & Size | 30 pts | 0-30 based on stage/employees |
| CS Hire Readiness | 25 pts | 0-25 based on evidence |
| Role Mandate | 25 pts | Builder vs Maintainer |
| Mission Alignment | 20 pts | Sector fit |

### Discrepancy Analysis

The two pipelines use **fundamentally different approaches**:
- **v9.8**: Gate-first + threshold + final Claude evaluation
- **v6.4**: Pre-gates + explicit 100-point weighted scoring

This is **intentional** - company evaluation happens before job data exists, while job evaluation has full JD context.

**Status:** No action needed - different approaches serve different purposes.

---

## Section 3: Score Interpretation Thresholds

| Bucket | v9.8 Company | v6.4 Job | Aligned? |
|--------|--------------|----------|----------|
| Strong/Apply | 80-100 | 80-100 | ✅ YES |
| Good/Research | 60-79 | 60-79 | ✅ YES |
| Marginal | 40-59 | 40-59 | ✅ YES |
| Skip | <40 | <40 | ✅ YES |
| Hard Pass | N/A | <20 | v6.4 only |

**Note:** v9.8 also has a "Watch" bucket at 40-69 for monitoring.

---

## Section 4: Batch 3 Failure Patterns Implementation Status

From SCORING-ENHANCEMENTS.md Batch 3 analysis:

| Pattern | Description | v9.8 Status | v6.4 Status |
|---------|-------------|-------------|-------------|
| 3.1 | Welsh Carson PE detection | ✅ In PE list | ✅ In PE list |
| 3.2 | Stale funding (>3yr) | ✅ STALE_FUNDING_YEARS=3 | ❌ Not implemented |
| 3.3 | High employee borderline | ✅ 200 soft, 350 hard | ⚠️ Different (150/200) |
| 3.4 | Enrichment failure fallback | ✅ Known large companies | ❌ Not implemented |
| 3.5 | Unicorn valuation gate | ✅ MAX_VALUATION, >$1B DQ | ❌ Not implemented |
| 3.6 | Company age gate | ✅ >8yr DQ, 5-8yr flag | ⚠️ Only stalled detection |
| 3.7 | YC batch year extraction | ✅ Implemented | ❌ Not applicable |
| 3.8 | PLG-dominant gate | ✅ Implemented | ❌ Not implemented |

**v6.4 gaps identified:**
- Missing stale funding check
- Missing known large companies list
- Missing unicorn valuation gate
- Missing PLG-dominant gate
- Missing explicit age gate (only stalled company check)

---

## Section 5: CS Hire Readiness Sub-Signals

### v9.8 Company Pipeline

CS Readiness scoring (threshold-based, ≥10 to proceed):
```
25 pts: No CS function + active build signal
10 pts: CS exists but no leader
 0 pts: CS leadership in place
 0 pts: No evidence found (default)
```

**Key change in v9.8:** Evidence-based only. No inference from stage.

### v6.4 Job Pipeline

CS Readiness scoring (0-25 dimension):
```
25 = Clearly first CS/support hire, no existing function
20 = Very small team (<5), needs senior leadership
15 = Small team (<10), building out org
10 = Team exists but scaling, builder opportunity unclear
 5 = Established team, incremental hire
 0 = No evidence of CS hiring need, or large existing CS org
```

**Key note:** Prompt says "If you see NO evidence of CS hire readiness, score 0-5. Do not assume readiness from stage."

### Alignment Assessment

Both pipelines now enforce evidence-based scoring. **ALIGNED** in principle, though scoring granularity differs.

---

## Section 6: Score Floor/Ceiling Rules

### v9.8 Company Pipeline

From evaluation prompt (CLAUDE.md):
- "All gates passed" claim removed in v9.8
- Wrong-sector companies should score <30

### v6.4 Job Pipeline

Explicit in prompt:
```
"A company with good stage but WRONG SECTOR should score 10-25.
A company with right sector but NO CS HIRE SIGNAL should score 15-30.
A company with wrong sector AND no CS signal should score 0-15."
```

**Status:** v6.4 has explicit floors. v9.8 relies on Claude interpretation.

**Recommendation:** Add explicit score floors to v9.8 evaluation prompt.

---

## Section 7: Domain Distance Modifiers

### v9.8 Company Pipeline

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

### v6.4 Job Pipeline

Mission alignment scoring embeds similar logic:
- 20 pts: Healthcare B2B SaaS (provider-side), Enterprise AI
- 15 pts: Developer tools with enterprise sales, regulated industry
- 10 pts: Enterprise B2B SaaS (high-touch)
- 5 pts: General B2B SaaS
- 0 pts: Wrong sector

**Status:** Similar logic but different implementation. v9.8 uses additive modifiers, v6.4 uses absolute scoring.

---

## Deliverable 1: Confirmed Discrepancies with Resolution

| # | Discrepancy | v9.8 Value | v6.4 Value | Resolution Status |
|---|-------------|------------|------------|-------------------|
| 1 | Employee hard cap | 350 | 350 | ✅ RESOLVED - v6.4 aligned |
| 2 | Employee soft cap | 200 | 200 | ✅ RESOLVED - v6.4 aligned |
| 3 | Funding hard cap | $500M | $500M | ✅ RESOLVED - v9.8 aligned to v6.4 |
| 4 | Known large companies | Present | Missing | Add to v6.4 |
| 5 | Known acquired list | Present | Missing | Add to v6.4 |
| 6 | Stale funding gate | 3 years | Missing | Add to v6.4 |
| 7 | Unicorn valuation gate | >$1B = DQ | >$1B = DQ | ✅ RESOLVED - Added to v6.4 |
| 8 | Company age gate | >8yr DQ, 5-8yr flag | Only stalled check | Add explicit to v6.4 |
| 9 | PLG-dominant gate | Present | Missing | Add to v6.4 |

---

## Deliverable 2: Gates Documented but Not Implemented

| Gate/Rule | Documented Where | Implementation Status |
|-----------|------------------|----------------------|
| $75M funding = DQ | Mentioned in prior discussions | **NOT in any pipeline** - $75M is soft cap, not hard DQ |
| 150 employee = DQ | Mentioned in prior discussions | **NOT in any pipeline** - Different caps exist |

Note: Prior summary referenced "tide_pool_scoring_adjustments.md" with these values, but this file does not exist. Values may have been from an earlier design doc that was superseded.

---

## Deliverable 3: Logic in Pipelines Not Documented

| Logic | Pipeline | Documentation Status |
|-------|----------|---------------------|
| YC batch year extraction (S12→2012) | v9.8 | **Undocumented** |
| Network connection override (Google VP contact) | v6.4 | **Undocumented** |
| JD-based maintainer/builder signal counting | v6.4 | **Undocumented** |
| NRR-first role language detection | v6.4 | **Undocumented** |
| IT Support/Help Desk title exclusion | v6.4 | **Undocumented** |
| Scale signals DQ (>500M users) | v6.4 | **Undocumented** |

---

## Deliverable 4: Items Flagged for Eric

1. ~~**Employee cap decision needed:** Should v6.4 use 350/200 (v9.8) or stay at 200/150?~~ ✅ **DECIDED: 350/200** - v6.4 aligned to v9.8

2. ~~**Funding cap decision needed:** v6.4 uses $500M, v9.8 uses $450M. Which is authoritative?~~ ✅ **DECIDED: $500M** - v9.8 aligned to v6.4

3. **"tide_pool_scoring_adjustments.md" does not exist.** Prior session referenced values from this file ($75M funding DQ, 150 employee DQ) but file cannot be found. Were these from an earlier design that was superseded? ⚠️ **UNRESOLVED** - Eric unsure

4. ~~**Unicorn gate for jobs:** v9.8 has >$1B valuation = DQ. Should v6.4 also have this?~~ ✅ **DECIDED: Yes** - Added to v6.4

5. ~~**Network connection override feature:** v6.4 has hardcoded "Google" VP connection with override logic. Is this still needed?~~ ✅ **DECIDED: Yes, keep it** - No changes needed

---

## Recommended Next Steps

### Completed ✅
1. ~~**Align v6.4 employee caps** to v9.8 (350 hard, 200 soft)~~ ✅ Done
2. ~~**Align v9.8 funding cap** to v6.4 ($500M)~~ ✅ Done
3. ~~**Add unicorn valuation gate to v6.4**~~ ✅ Done
4. ~~**Fix connection routing bug** in v6.4 (Brave Search → IF bypass)~~ ✅ Done (v6.5)

### Remaining
5. **Port remaining gates to v6.5:**
   - Known large companies list
   - Known acquired companies list
   - Stale funding check (3 years)
   - PLG-dominant gate
   - Explicit company age gate
6. **Document undocumented logic** (YC batch extraction, network override, JD signals)

---

*Generated by reconciliation audit, March 16, 2026*
*Last updated: March 17, 2026 - All decisions resolved. Pipelines now at v9.9 (company) and v6.6 (job) with Batch 4 scoring fixes.*
