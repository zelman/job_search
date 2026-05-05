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
