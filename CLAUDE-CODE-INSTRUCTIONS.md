# CLAUDE-CODE-INSTRUCTIONS.md -- Pipeline Engineering Workflow

**Purpose:** Standard operating procedure for Claude Code when working on Tide Pool pipeline code. Read this BEFORE writing or reviewing any pipeline code.

---

## The Three-File Contract

Every pipeline engineering session must reference these three files:

1. **SCORING-THRESHOLDS.md** -- What the pipeline SHOULD do (business rules)
2. **GATE-TIGHTENING-SPEC.md** (or current change spec) -- What you're changing and why
3. **The workflow JSON** -- What the pipeline ACTUALLY does (code)

If SCORING-THRESHOLDS.md doesn't exist in the repo yet, stop and create it first. No pipeline code changes without the spec file present.

---

## Before Writing Any Code

1. Read SCORING-THRESHOLDS.md in full
2. Read the change spec (e.g., GATE-TIGHTENING-SPEC.md)
3. Verify the change spec is consistent with SCORING-THRESHOLDS.md
4. If there's a conflict between the spec and the thresholds doc, ask Eric which is correct. Do not guess.

---

## Implementation Checklist

For every code change:

- [ ] Change implemented in main pipeline (Enrich & Evaluate)
- [ ] Same change implemented in rescore workflow (Funding Alerts Rescore)
- [ ] Threshold values match SCORING-THRESHOLDS.md exactly
- [ ] SCORING-THRESHOLDS.md updated if thresholds changed (update it FIRST, then code)
- [ ] Version numbers incremented in both workflows
- [ ] Version numbers updated in SCORING-THRESHOLDS.md header
- [ ] `Last Scored Version` string updated in Airtable write nodes
- [ ] CONTEXT-job-search.md version table updated

---

## After Writing Code: Mandatory Audit

After implementing changes, before presenting the result to Eric, run the audit procedure from AUDIT-PROMPT.md against your own changes. Specifically:

1. Extract all numeric thresholds from the code you wrote/changed
2. Compare each one against SCORING-THRESHOLDS.md
3. If any threshold in your code doesn't match the spec, fix it before showing Eric

This is self-review, not optional. The audit catches the exact class of bug (specification drift) that code review misses.

---

## The Two-Workflow Problem

The Tide Pool pipeline has TWO n8n workflows that score companies independently:

| Workflow | Purpose | Runs When |
|---|---|---|
| Enrich & Evaluate Pipeline (v9.x) | Scores new companies from scrapers | Triggered by scraper workflows |
| Funding Alerts Rescore (v4.x / v5.x) | Re-scores existing Airtable records | Scheduled (every 2 min), filters by Last Scored Version |

**These workflows have independent copies of threshold logic.** They are NOT shared code. When you change a threshold in one, you MUST change it in the other. The Sync Contract table in SCORING-THRESHOLDS.md lists every threshold that must stay aligned.

### Known Divergence Patterns

The rescore workflow (v4.x) uses HARDCODED values instead of named constants:
```javascript
// Rescore: hardcoded
if (employeeCount && employeeCount > 200) {
// Main pipeline: uses constant
if (employeeCount && employeeCount > HARD_EMPLOYEE_CAP) {
```

When updating the rescore workflow, search for the raw number (e.g., `200`, `150000000`) rather than a variable name. These are easy to miss.

### Recommended Long-Term Fix

Extract shared thresholds into a config object at the top of each enrichment node. Even though n8n doesn't support shared imports between workflows, having a clearly labeled config block at the top of each node makes it obvious where the values live:

```javascript
// === SHARED THRESHOLDS (must match SCORING-THRESHOLDS.md) ===
// Last synced: 2026-03-24, pipeline v9.14 / rescore v4.10
const THRESHOLDS = {
  HARD_EMPLOYEE_CAP: 200,
  SOFT_EMPLOYEE_CAP: 150,
  HARD_FUNDING_CAP: 150000000,
  SOFT_FUNDING_CAP: 75000000,
  MAX_VALUATION: 500000000,
  MIN_EMPLOYEES: 15,
  MIN_FOUNDED_YEAR: 2016,
  SCORE_APPLY: 70,
  SCORE_WATCH: 40,
  CS_READINESS_CEILING: 25,
};
// === END SHARED THRESHOLDS ===
```

Put this identical block at the top of BOTH `Parse Enrichment` (main pipeline) and `Parse Enrich` (rescore). The "Last synced" comment is a human-readable audit trail.

---

## Threshold Change Procedure

When Eric asks to change a threshold:

1. Update SCORING-THRESHOLDS.md first (the spec is the source of truth)
2. Update the THRESHOLDS config block in the main pipeline
3. Update the THRESHOLDS config block in the rescore workflow
4. Update any downstream references that use the old value
5. Run the audit procedure from AUDIT-PROMPT.md
6. Update changelog in SCORING-THRESHOLDS.md
7. Update version numbers everywhere

---

## Common Mistakes to Avoid

**"The code is correct"**
The code can be syntactically perfect and still wrong. A gate set to 350 instead of 200 is correct code that implements the wrong business rule. Always check values against SCORING-THRESHOLDS.md, not just against JavaScript syntax.

**"I updated the main pipeline"**
Did you also update the rescore workflow? Check the Sync Contract.

**"Null data passes the gate, that's fine"**
No. If employee count is null, `employeeCount > 200` evaluates to false, and the company passes the gate. This is the data sufficiency problem. Every gate that checks a numeric field must have a corresponding null-data handling strategy documented in SCORING-THRESHOLDS.md.

**"Haiku scored it at 78 so it must be good"**
Haiku converges on ~78 for sparse-data companies in target sectors. This is a known pattern, not a signal. If the enrichment data is thin, the score is unreliable regardless of what Haiku returns. The data sufficiency gate exists to catch this.

**"The CS Readiness prompt says max 25 points"**
Prompts are suggestions. Haiku returns 26-27 routinely. Always enforce ceilings in code with `Math.min()`. Never trust an LLM to respect a numeric boundary in a prompt.
