# AUDIT-PROMPT.md -- Business Logic Audit for Tide Pool Pipeline

**Purpose:** Run this prompt against pipeline code to catch specification drift. This is NOT a code review. This checks whether the code's behavior matches the business rules in SCORING-THRESHOLDS.md.

**When to run:**
- After every pipeline code change before deploying
- Monthly as a drift check even if no changes were made
- After updating SCORING-THRESHOLDS.md to verify code alignment

---

## How to Use

In Claude Code, after implementing changes to either workflow:

```
Run a business logic audit on the pipeline code I just changed.

Reference file: SCORING-THRESHOLDS.md (in this repo)
Target files: [the n8n workflow JSON files you changed]

Follow the audit procedure in AUDIT-PROMPT.md exactly.
```

---

## Audit Procedure

### Step 1: Extract All Numeric Thresholds from Code

For each workflow JSON file provided, extract every hardcoded number and named constant that serves as a gate, cap, threshold, or scoring boundary. Present them in a table:

```
| Variable/Context | Value in Code | Location (node + line) |
```

Include at minimum:
- Employee count caps (hard and soft)
- Funding caps (hard and soft)
- Valuation caps
- Min employee floor
- Min founded year
- Score bucket boundaries (APPLY/WATCH/PASS)
- CS Readiness point ceiling
- CS likelihood score caps
- Default score detection range
- Headcount penalty ranges and values
- Any hardcoded array lengths (PE firms, known large companies)

### Step 2: Compare Against SCORING-THRESHOLDS.md

For each extracted value, compare against the corresponding entry in SCORING-THRESHOLDS.md. Flag mismatches:

```
| Threshold | SCORING-THRESHOLDS.md | Code Value | MATCH/MISMATCH | Severity |
```

Severity levels:
- **CRITICAL:** A hard DQ gate that is more permissive than spec (companies pass that shouldn't)
- **HIGH:** A soft cap or penalty that doesn't match spec (scoring is miscalibrated)
- **MEDIUM:** A scoring weight or modifier that differs from spec
- **LOW:** A message string or variable name inconsistency

### Step 3: Cross-Workflow Sync Check

If both workflow files are provided, compare every threshold between them:

```
| Threshold | v9.x Value | Rescore Value | MATCH/MISMATCH |
```

Flag any case where the two workflows use different values for the same business rule. This is always at least HIGH severity because it means the rescore workflow will produce different results than the main pipeline for the same company.

### Step 4: Gate Coverage Check

For each Hard DQ Gate listed in SCORING-THRESHOLDS.md, verify:
1. The gate condition exists in code
2. It fires BEFORE the company reaches Claude for scoring
3. It produces a DQ reason string
4. The DQ routes the company to Auto-Disqualified status
5. The score is set to -1 (not left at whatever Claude assigned)

Present as:

```
| Gate | Exists in Code | Fires Before Scoring | Sets Score -1 | PASS/FAIL |
```

### Step 5: Data Flow Check

Verify that enrichment data actually reaches the gates:
- Does the employee count from Brave Search get passed to the employee cap check?
- Does funding data get passed to the funding cap check?
- If a data field is null, does the gate fail open (company passes) or fail closed (company gets flagged)?

For each gate, state: "Null data behavior: fails OPEN / fails CLOSED"

If a gate fails open on null data and there is no data sufficiency gate catching it, flag as CRITICAL.

### Step 6: Summary

Produce a single summary:

```
AUDIT RESULT: PASS / FAIL

Critical issues: [count]
High issues: [count]
Medium issues: [count]
Low issues: [count]

Top issues requiring immediate fix:
1. [description]
2. [description]
...
```

---

## Example Output (abbreviated)

```
AUDIT RESULT: FAIL

Critical issues: 2
High issues: 1

Issue 1 (CRITICAL): Employee hard cap in code (350) is more permissive than spec (200).
  - SCORING-THRESHOLDS.md says: > 200 = DQ
  - Parse Enrichment line 107: HARD_EMPLOYEE_CAP = 350
  - Impact: Companies with 201-350 employees pass gates and get scored

Issue 2 (CRITICAL): Funding hard cap in code ($500M) is more permissive than spec ($150M).
  - SCORING-THRESHOLDS.md says: > $150M = DQ
  - Parse Enrichment line 103: HARD_FUNDING_CAP = 500000000
  - Impact: Companies with $150M-$500M funding pass gates and get scored

Issue 3 (HIGH): Rescore workflow uses $450M funding cap vs main pipeline $500M.
  - Parse Enrich line 465: > 450000000
  - Parse Enrichment line 103: > 500000000
  - Impact: Same company may be DQ'd by rescore but not by main pipeline
```

---

## What This Audit Does NOT Cover

- Code correctness (syntax, logic errors, null handling)
- Performance (API call efficiency, Airtable rate limits)
- Prompt quality (whether Claude's scoring prompts are well-written)
- Data quality (whether Brave Search returns good results)

Those are separate review concerns. This audit is strictly: do the business rules in code match the business rules in the spec?
