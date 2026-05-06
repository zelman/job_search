# Job Search Scraper Backlog

## Pipeline Enhancements

### VC Backed Bypass for Nonprofit Filters
**Status:** Open
**Added:** 2026-04-10
**Affected:** Enrich & Evaluate Pipeline (`rcMNDrfZR6csHRsYKFn0W`)

**Problem:** Companies from VC portfolio scrapers are incorrectly flagged as invalid entities when:
- Company URL uses `.org` TLD (e.g., MIDAO → midao.org)
- Company name contains "foundation" (e.g., Foundation AI)

**Solution:** Add bypass logic in pipeline's invalid entity detection:
```javascript
// Skip nonprofit entity checks for VC-backed companies
if (item.json['VC Backed'] === true) {
  // bypass .org / "foundation" filters
}
```

**Scrapers now tagging `VC Backed: true`:**
- VC Scraper - LegalTech Fund v1

**TODO:** Update all other VC scrapers in Enterprise v28 to also tag `VC Backed: true`

---

## Scraper Additions

(none pending)

---

## Known Issues

### Phase 1 Enrichment: Stale Data Producing False APPLY Signals
**Severity:** High — false positives cluster at top of score distribution
**Filed:** 2026-05-05
**Affected:** Enrich & Evaluate Pipeline v10.2 (internal name `v10.0`, version stamp `v9.18`), Parse Enrichment node + Build CS Readiness Prompt node

**Root cause (verified against v10.2 source):**

1. **VC Firm is never re-fetched.** Line 170 of Parse Enrichment: `source: companyDataItem.source || companyDataItem['VC Firm'] || 'Unknown'`. Field is inherited from upstream scraper at scrape time and never touched by Brave. Acquisitions and new lead investors invisible to pipeline indefinitely.
2. **No `Last Enriched` timestamp** anywhere in pipeline or rescore workflow. Prerequisite for any re-enrichment job.
3. **Single-source enrichment.** All extractions (employee count, funding stage, valuation, founded year, acquisition status, sector) regex against one `allText` blob from one Brave query (10 results).
4. **Sector classification mixes VC portfolio description with company text.** Line 659: `descAndEnrichment = ((companyData.description || '') + ' ' + allText).toLowerCase()`. VC's portfolio tag (e.g. "Leadout Capital portfolio company healthcare/femtech") leaks into sector classification.
5. **PE acquirer list is incomplete.** ESW Capital (Influitive's acquirer Dec 2023) was not in the 38-firm `peFirms` list. *Partially shipped in commit `71fed4a` — added ESW Capital + Symphony Technology Group, removed Insight Partners (separate venture/buyout arms make blanket entry unsafe). Total now 39 firms.* Per-acquisition-context recency logic still pending — see Suggested fix #3.
6. **CS leadership "evidence" prompt accepts stage-based inference.** Build CS Readiness Prompt declares "EVIDENCE OVER INFERENCE" but lists "30-80 employees, B2B SaaS, regulated industry, zero CS roles visible" as a 25-point signal. Prompt also receives no team/Brave data — only `company_name + description + job_title + employee_count` — so Claude has no factual basis to detect existing VP CS. Structural false-positive risk.

**Verified false positives (2026-05-05, top of Funding Alerts distribution, scores 72-74):**

| Company | Record ID | Failure |
|---------|-----------|---------|
| theCut | `reckhv3MnWjKlnsdO` | Sector inherited from VC; D2C consumer marketplace tagged as healthcare/femtech |
| Influitive | `receDBJCFvHzp1tWG` | Acquired by ESW Capital Dec 2023; PE detection missed (acquirer not in list) |
| Cadence | `recbfkGI3rU2mDedp` | VC firm wrong, employee count stale by 4x, sector wrong |
| HouseRx | `rec4iBl0GH7Gq1pj6` | Lead VC wrong, employee count stale by 5x |
| Brellium | `recYjK2jkBgEe2M5n` | Leadership gap heuristic flagged "no CS leader"; VP CS exists (verified 2026-03-12) |

**Suggested fixes (priority order):**

1. **Add `Last Enriched` timestamp field** to Funding Alerts. Prerequisite for re-enrichment.
2. **Re-enrichment job for records >60 days old** — re-run Phase 1 on stale records, refreshing VC Firm, Employee Count, recent funding events, acquisition status. Scheduled (weekly) or trigger-on-review.
3. **Acquisition / PE ownership detection in Phase 1** — *Safety patch shipped in commit `71fed4a` (added ESW Capital + Symphony Technology Group; removed Insight Partners as blanket entry).* Remaining work: (a) explicit `"<company> acquired by"` Brave query in last 24 months for active acquisition detection, not just acquirer name in stale snippets; (b) per-acquisition-context recency logic — gate the PE flag on `acquisition year > now-3y` so growth-stage equity from firms with mixed venture/buyout arms (Insight, General Atlantic, Summit, Battery, similar) doesn't auto-DQ legitimate portfolio companies; (c) move `peFirms` source-of-truth to Airtable PE Firms table (`tblU2izcb0wnCNMuV`, base `appFEzXvPWvRtXgRY`, 43 active records — already populated, just not read by pipeline) via lookup node at workflow start so additions don't require redeploy. If recent acquisition detected: force-route to PASS with Status "Acquired - Hard Pass".
4. **Leadership gap heuristic rebuild** — require explicit evidence (active VP/Head CS posting, LinkedIn search for current title holders, team page named-title detection). Until rebuilt, down-weight or require `Has CX Job Posting = true`. Remove the "30-80 employees... zero CS roles visible" inference clause from the prompt.
5. **Sector source-of-truth** — extract from company homepage/About page, not VC portfolio tag. VC tag becomes tiebreaker only.

**Priority justification:** Above all four open SCORING-ENHANCEMENTS items (extract-thresholds, headcount penalty range, valuation tiers, hardcoded thresholds). Threshold tuning makes the scorer more precise; this bug means the scorer is acting on wrong inputs. Upstream fix compounds.

**Until fix ships — manual cleanup plan (do NOT blanket-PASS):**
- *Category A (clean PASS w/ Disqualify Reasons):* theCut (D2C consumer, persona gate), Influitive (PE-owned post-acquisition)
- *Category B (correct fields, leave Status for re-scoring):* Cadence (employees → 200+, VC → General Catalyst/Thrive/Coatue, sector → remote patient monitoring), HouseRx (employees → ~250, VC → NEA/Town Hall lead, total → $100M, Series B Nov 2025)
- *Category C (verify):* Brellium — should already be Pass per 2026-03-12 verification; if shows Apply, correct with Note pointing to Work Search Activities `recbGIvCrzihJvrkS` and `recO8fUZW4Jw0FaQg`

**Test cases for fix validation:** theCut → PASS, Influitive → PASS, Cadence → APPLY/WATCH at later-stage tier, HouseRx → APPLY/WATCH at rebuilder tier, Brellium → PASS via correct leadership detection.

**Doc inconsistencies caught while triaging:**
- File `Enrich & Evaluate Pipeline v10.2.json` has internal `name: "v10.0"` and writes `Last Scored Version: "v9.18"` to Airtable. Three version stamps disagree.
- `CONTEXT-job-search.md` (lives in Claude.ai Job Search 2 knowledge, not local repo) references v9 / `ENHANCEMENT-IDEAS.md` — refresh to v10.2 / `SCORING-ENHANCEMENTS.md` in next Claude.ai session.

---

### Credential Management Hygiene (n8n)
**Severity:** Low (operational)
**Filed:** 2026-05-06

**Lesson learned:** When n8n credentials need rotation, **always update the existing credential's value in place. Never delete and recreate.** Recreating generates a new internal entity ID, orphaning all node references that pointed at the old one.

**Symptom when violated:** Workflow appears active, schedule fires every cycle, but every execution fails at credential-using nodes with `Authorization failed - please check your credentials` (initially) or `Credential with ID "<old_id>" does not exist for type "<type>"` (more diagnostic). Read-side workings nodes (Airtable native nodes using `airtableTokenApi`) are unaffected since they reference a different credential entity; only HTTP-based write nodes break. Result is silent partial-failure: reads work, writes don't, no records get updated, schedule runs forever.

**Verified by today's troubleshooting:** Rescorer workflow `Funding Alerts Rescore v5.0 (Standalone)` was silently dead since at least 2026-04-25 due to orphaned credential reference (ID `LCYvQYofV9XXnPrk` no longer existed). Three iterations of token rotation + Bearer prefix addition all failed with the same symptom until the actual fix — re-linking the three HTTP write nodes (`Update DQ`, `Update Dev`, `Update Eval`) to the working credential in n8n UI.

**If recreation is unavoidable:** every consuming node must be re-linked. Audit by searching the workflow JSON for the old credential ID and updating references via `update_workflow` MCP or UI.

---

### Score Variability Across Rescore Runs
**Severity:** Medium (affects validation methodology)
**Filed:** 2026-05-06

**Symptom:** Same record produces different scores across consecutive rescores with no input change.

**Verified instance:** Influitive (`receDBJCFvHzp1tWG`) scored **72 → 58 → 62** across three rescores in 24h. CS Hire Likelihood shifted between `high`, `medium`, and back. Summary text varied each time.

**Implication:** Scoring is not deterministic. Means "did this config edit improve scoring?" is hard to test rigorously when the control is itself unstable. Validation tests can be confounded by run-to-run drift indistinguishable from actual config-edit effects. A 14-point drift on a single record across runs is not noise floor — it's the difference between APPLY and WATCH bucket assignment.

**Investigate (next session):**
- Temperature setting on `Evaluate via Anthropic API` HTTP node's request body (likely missing → using model default which has some randomness).
- Prompt non-determinism: are any timestamp / random / batch-order values leaking into the eval prompt?
- Brave Search result variance: does Brave return stably ordered top-10 results for the same query? If not, `allText` differs run-to-run, feeding different inputs to Claude.
- Airtable record fetch order: rescorer fetches "next stale" via filterByFormula — order isn't guaranteed across runs.

**Mitigation pending fix:** When validating config edits, run each test record through 3 rescores and look at score median/range, not single-point comparisons.

---

### PE Backed False Positives
**Severity:** High (affects top of score distribution decisions)
**Filed:** 2026-05-06

**Symptom:** `PE Backed = true` is set on records whose actual investors are VC firms, not PE firms. Confirmed for HouseRx (First Round Capital lead), Brellium (First Round Capital), Cadence (Oak HC/FT, then General Catalyst per bug doc verification), Influitive (Golden Ventures historically; Influitive was acquired by ESW Capital Dec 2023 but that's a separate detection failure).

**Likely cause:** Parse Enrich's `isPEBacked` detection runs `peRegex.test(allText)` where `allText` is the concatenation of Brave Search results for the company. If any PE firm name appears anywhere in the search snippets (e.g., a news article mentioning a PE firm in unrelated context, a competitor comparison, an industry analysis), the test passes — without verifying whether the firm has any actual investor relationship with the company.

**Examples of how this fires falsely:**
- "Battery Ventures" (in PE Firms table) is a VC firm by most definitions; mention of it in any tech-news context flags non-portfolio companies.
- "Insight Partners" appears in many SaaS investment news articles; any company mentioned in the same article gets flagged.
- "NEA" (in PE Firms table as "New Enterprise Associates" — debatable whether NEA belongs there at all) is a major VC; references in startup news flag countless companies.

**Implication:** The rescorer's hard PE-DQ gate is firing on these false positives. **Some legitimate VC-funded targets may have been auto-disqualified silently.** Worth a retrospective query of records with `Status: Auto-Disqualified` and `Disqualify Reasons LIKE 'PE-backed%'` to estimate the false-positive rate.

**Fix direction:** Detection needs investor-context matching, not bare name presence. Candidates:
- Require proximity to investor-relationship phrases: "led by", "investment from", "backed by", "raised from", "round led by", "participated in", "co-led".
- Use a small Claude classification call instead of regex: pass the snippet and the candidate firm name, ask "is this firm an investor in [company]?" before flagging.
- Maintain a structured investor list per company in Airtable (populated during enrichment) rather than text-presence detection.

**Related to and partially blocked by:** Phase 1 enrichment staleness — even with better detection, if Brave Search returns outdated snippets, current investor relationships won't be visible.

**Verified by 2026-05-06 rescore validation:** 4 of 5 test records showed `PE Backed: true` post-rescore despite none being actually PE-backed. theCut correctly flipped to `false` on this rescore — suggesting the detection is brittle even when functioning, not consistently wrong.
