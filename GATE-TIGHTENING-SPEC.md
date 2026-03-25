# Gate Tightening Spec: Threshold Alignment + Data Sufficiency Gate

**Date:** March 24, 2026
**Scope:** Enrich & Evaluate Pipeline v9.13, Funding Alerts Rescore v4.9.2
**Priority:** P0 -- these misalignments produce false signal at scale

---

## Problem Statement

The pipeline's hard DQ thresholds are dramatically more permissive than the actual target criteria. Companies with 200+ employees or $100M+ funding pass all gates, get scored by Haiku at 70-78, and land in APPLY/Monitor status despite being obvious mismatches. A separate rescore workflow uses the same permissive thresholds. The result: 25+ companies sitting at Score 78 + Status "Auto-Disqualified" because manual review caught what the gates missed.

Root causes:
1. Hard DQ thresholds (350 employees, $500M funding) are ~2-3x the actual criteria (~150 employees, ~$75M funding)
2. No data sufficiency gate -- companies with null employee count, null funding, and null founded year pass all gates by default and get fully scored
3. Haiku converges on ~78 for sparse-data companies in target sectors (healthcare B2B SaaS + enterprise GTM = default high score)
4. CS Readiness scores exceed the 25-point maximum (26-27 observed), meaning the prompt ceiling isn't enforced in code
5. The rescore workflow (v4.9.2) has its own independent copy of thresholds that must be updated in lockstep

---

## Change 1: Tighten Hard DQ Thresholds (v9.13 Parse Enrichment)

**File:** Enrich & Evaluate Pipeline v9.13
**Node:** `Parse Enrichment`
**Location:** Lines ~101-108 (threshold constants)

### Current values:
```javascript
const MAX_BELIEVABLE_FUNDING = 5000000000;
const HARD_FUNDING_CAP = 500000000;
const SOFT_FUNDING_CAP = 75000000;
const MAX_VALUATION = 500000000;
const MIN_EMPLOYEES = 15;
const HARD_EMPLOYEE_CAP = 350;
const SOFT_EMPLOYEE_CAP = 200;
const MIN_FOUNDED_YEAR = 2016;
```

### New values:
```javascript
const MAX_BELIEVABLE_FUNDING = 5000000000;
const HARD_FUNDING_CAP = 150000000;    // Was 500M. Companies over $150M total funding are too mature.
const SOFT_FUNDING_CAP = 75000000;     // Unchanged. $75M-$150M gets warning + score penalty.
const MAX_VALUATION = 500000000;       // Unchanged. Unicorn gate handles >$1B separately.
const MIN_EMPLOYEES = 15;             // Unchanged
const HARD_EMPLOYEE_CAP = 200;        // Was 350. Over 200 employees = auto-DQ.
const SOFT_EMPLOYEE_CAP = 150;        // Was 200. 150-200 employees = warning + score penalty.
const MIN_FOUNDED_YEAR = 2016;        // Unchanged
```

### Rationale:
- Target profile is 20-100 employees, under ~$75M raised
- Previous HARD caps (350 employees, $500M funding) were set during early pipeline development when the priority was avoiding false negatives. The pipeline is now mature enough that false positives are the bigger problem.
- The soft cap zone (150-200 employees, $75M-$150M funding) preserves flexibility for exceptional companies while applying score penalties

### Also update in the same node:
The DQ reason messages reference the cap values. After changing thresholds, verify that the `autoDisqualifiers.push()` messages on lines ~680-681 still make sense. They use template literals that reference the constants, so they should auto-update:
```javascript
// Line ~680 - uses HARD_EMPLOYEE_CAP, will auto-update
if (employeeCount && employeeCount > HARD_EMPLOYEE_CAP) autoDisqualifiers.push(`Too large (>${HARD_EMPLOYEE_CAP} employees: ${employeeCount})`);
// Line ~681 - uses HARD_FUNDING_CAP, will auto-update  
if (totalFunding && totalFunding > HARD_FUNDING_CAP) autoDisqualifiers.push(`>$150M funding (${totalFundingRaw})`);
```

### Warning zone updates needed:
The warning zone logic on lines ~754-758 uses SOFT_EMPLOYEE_CAP and SOFT_FUNDING_CAP. With the new values:
- Employees 150-200: warning (was 200-350)
- Funding $75M-$150M: warning (was $75M-$500M)

These should auto-update via the constants, but verify the warning messages still read correctly.

---

## Change 2: Tighten Hard DQ Thresholds (v4.9.2 Parse Enrich)

**File:** Funding Alerts Rescore v4.9.2
**Node:** `Parse Enrich`
**Location:** Lines ~459-465 (hardcoded values, not constants)

### Current values (hardcoded):
```javascript
if (employeeCount && employeeCount > 350) {
  disqualifiers.push('Too large (>' + 350 + ' employees: ' + employeeCount + ')');
}
// ...
if (totalFunding && totalFunding > 450000000) disqualifiers.push('>$450M funding (' + totalFundingRaw + ')');
```

### New values:
```javascript
if (employeeCount && employeeCount > 200) {
  disqualifiers.push('Too large (>200 employees: ' + employeeCount + ')');
}
// ...
if (totalFunding && totalFunding > 150000000) disqualifiers.push('>$150M funding (' + totalFundingRaw + ')');
```

### Also update:
- **Headcount penalty zone** (lines ~498-509): Currently applies -10 for 200-350 employees, -5 for 150-200. With the new hard cap at 200, the 200-350 penalty zone is now fully inside the DQ zone and will never fire. Remove that dead code branch. Keep the 150-200 penalty:
```javascript
// Headcount penalty modifier (only fires in soft cap zone, 150-200)
let headcountPenaltyModifier = 0;
if (employeeCount && employeeCount >= 150 && employeeCount <= 200) {
  if (rebuildSignal) {
    headcountPenaltyModifier = 0;
  } else {
    headcountPenaltyModifier = -10;
  }
}
```

- **Warning zone** (line ~516): Currently warns for 200-350 employees. Update to 150-200:
```javascript
if (employeeCount && employeeCount >= 150 && employeeCount <= 200) {
```

### CRITICAL: These thresholds are hardcoded in v4.9.2, not using constants.
This is a tech debt issue. Consider extracting to constants at the top of the node for maintainability, matching the v9.13 pattern.

---

## Change 3: Add Data Sufficiency Gate (v9.13)

**File:** Enrich & Evaluate Pipeline v9.13
**Node:** `Parse Enrichment`
**Location:** After the existing DQ list (after line ~750), before the return statement

### New logic:
```javascript
// === DATA SUFFICIENCY GATE ===
// Companies with no employee count, no funding data, and no founded year
// lack the minimum data needed for meaningful scoring.
// Route to Manual Review instead of full evaluation.
const hasEmployeeData = employeeCount !== null && employeeCount > 0;
const hasFundingData = (totalFunding !== null && totalFunding > 0) || fundingStage;
const hasAgeData = foundedYear !== null || ycBatchYear !== null;
const dataPointCount = [hasEmployeeData, hasFundingData, hasAgeData].filter(Boolean).length;

const isDataInsufficient = dataPointCount === 0;
const isDataSparse = dataPointCount === 1;
```

Then add to the output object (inside the return statement):
```javascript
is_data_insufficient: isDataInsufficient,
is_data_sparse: isDataSparse,
data_point_count: dataPointCount,
```

### New routing logic:
This requires a new IF node after `Parse Enrichment` (or modification of the existing `IF: Auto-Disqualify` node).

**Option A (simpler): Add data insufficiency as a DQ reason**
Add before the existing DQ list:
```javascript
if (isDataInsufficient && autoDisqualifiers.length === 0) {
  autoDisqualifiers.push('Insufficient data for scoring (no employees, funding, or age data found)');
}
```
This routes data-insufficient companies through the existing Auto-Disqualified path. The score gets set to -1 and Status to Auto-Disqualified. When enrichment improves (e.g., Brave Search returns better results), the rescore workflow can re-evaluate.

**Option B (better but more work): Route to Manual Review status**
Add a new IF node after `IF: Auto-Disqualify` that checks `isDataInsufficient`. If true, write to Airtable with Status = "Manual Review" and Score = 0. This preserves the distinction between "we know this is wrong" (Auto-DQ) and "we don't know enough to score" (Manual Review).

**Recommendation:** Start with Option A. It's minimal code change, uses existing routing, and immediately stops the 78-score-from-nothing problem. Option B is a refinement for a future version.

### Also add in v4.9.2:
Apply the same data sufficiency check in the rescore workflow's `Parse Enrich` node. Same logic, same position (after DQ list, before return).

---

## Change 4: Cap CS Readiness Score in Code (Both Workflows)

**Problem:** Haiku returns CS Readiness scores of 26-27 despite the prompt defining a 25-point maximum. The score is passed through without validation.

### v9.13 -- Node: `Parse CS Readiness`
Find where `cs_readiness_score` is extracted from the Claude response and add:
```javascript
// Enforce 25-point ceiling on CS Readiness
const rawCsReadiness = evaluation.cs_readiness_score || 0;
const csReadinessScore = Math.min(rawCsReadiness, 25);
```

### v4.9.2 -- Node: `Parse Eval`
The rescore workflow gets CS Readiness from the full evaluation response. Find where `csReadinessFromEval` is extracted (currently line in Parse Eval):
```javascript
const csReadinessFromEval = evaluation.scores?.cs_hire_readiness || 0;
```
Add ceiling:
```javascript
const csReadinessFromEval = Math.min(evaluation.scores?.cs_hire_readiness || 0, 25);
```

---

## Change 5: Set Last Scored Version in Main Pipeline (v9.13)

**Problem:** The main pipeline does not set `Last Scored Version` in Airtable. This means the rescore workflow (which filters on `{Last Scored Version}!='4.9.2'`) will re-process every record the main pipeline creates, potentially overwriting good evaluations.

### Node: `Prep for Airtable Update`
Add to the return object:
```javascript
'Last Scored Version': 'v9.14',  // Increment version with this release
```

This prevents the rescore workflow from re-processing records that were scored by the updated main pipeline.

---

## Change 6: Auto-Zero Scores on DQ Status (Both Workflows)

**Problem:** When the pipeline sets Status = "Auto-Disqualified", the score field retains whatever Haiku assigned (e.g., 78). This creates confusing Airtable views.

### v9.13 -- Nodes: `Airtable: Auto-Disqualified` and `Airtable: Update Auto-Disqualified`
Verify that both nodes set `Tide-Pool Score` to -1 when writing DQ records. Looking at the v4.9.2 `Update DQ (HTTP)` node, it correctly sets `"Tide-Pool Score": -1`. Confirm the main pipeline does the same.

### Existing Manual DQ Records:
The 25+ records currently showing Score 78 + Status Auto-Disqualified in Airtable need cleanup. After deploying the gate changes, run a one-time Airtable update to set Score = -1 for all records where Status = "Auto-Disqualified" and Score > 0.

---

## Validation Checklist

After implementing all changes, verify with these test cases:

1. **Company with 250 employees, $80M funding** -> Should be hard DQ'd by employee cap (>200)
2. **Company with 170 employees, $60M funding** -> Should pass gates but get -10 headcount penalty and funding warning
3. **Company with null employees, null funding, null age** -> Should be DQ'd (data insufficient) or routed to Manual Review
4. **Company with 50 employees, $20M Series A, healthcare SaaS** -> Should pass all gates and proceed to scoring normally
5. **CS Readiness score returned as 27** -> Should be capped to 25 in code
6. **Main pipeline scored record** -> Should have Last Scored Version set, preventing rescore workflow from re-processing

## Version Notes

After deploying:
- Main pipeline version: v9.14
- Rescore version: v4.10 (or v5.0 given scope of threshold changes)
- Update CONTEXT-job-search.md with new version numbers
- Consider running the rescore workflow once across all existing records to re-evaluate with new thresholds
