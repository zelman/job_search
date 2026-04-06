# Scoring Enhancements Backlog

Tracking remaining scoring improvements. Historical items (v9.2-v9.9) have been implemented and removed from this document.

*Last updated: April 2026*

---

## Open Items

### Summary Generator Quality

**Problem:** Summary generator uses stage-based reasoning ("Series A = CS hiring likely") as positive signal without sourced evidence. Primary driver of false positives.

**Status:** Partially addressed via CS Readiness prompt changes. May need further tuning if false positive rate remains high.

**Fix if needed:** Summary generator should only assert positive CS hire likelihood when at least one is confirmed:
1. Active job posting for CS leadership role
2. Recent CRO/VP Sales hire with no CS leader found
3. Company statement about scaling customer relationships
4. Job board search returns CS build/founding role

If none found: `CS Hire Likelihood = "low"`. Stage alone is not evidence.

---

### VC Brand Modifier Weight

**Problem:** VC quality can over-contribute to scores, rescuing companies that should fail business model gates.

**Current state:** Partially addressed. Verify VC brand is a late-stage modifier (+5 pts max), not overriding failed gates.

**Verification needed:** Confirm Khosla/Sequoia-backed hardware companies still DQ correctly.

---

### LinkedIn CS Function Check (Optional Enhancement)

**Problem:** CS Hire Readiness scoring could be more accurate with direct LinkedIn data.

**Options:**
1. Brave Search: `"[company] customer success" site:linkedin.com`
2. Proxycurl API ($50-100/mo) - direct LinkedIn search
3. Skip - rely on prompt inference

**Status:** Deferred. Revisit if signal rate doesn't improve enough.

---

## Verification Checklist

Periodic checks to ensure gates are working:

- [ ] PE-backed companies (Vista, Thoma Bravo, WCAS) → DQ
- [ ] Unicorns (>$1B valuation) → DQ
- [ ] Old companies (>8 years, YC batch pre-2018) → DQ
- [ ] Healthcare care delivery (not SaaS) → DQ
- [ ] CX tooling vendors (sell TO CS teams) → low score
- [ ] Stale funding (>3 years, early stage) → score penalty
- [ ] Non-US HQ without US expansion → DQ

---

## Implementation History

| Version | Date | Key Changes |
|---------|------|-------------|
| v9.2 | Mar 12 | knownLargeCompanies, knownAcquired, Canadian cities |
| v9.6 | Mar 15 | Healthcare care delivery, medical device, expanded sector gates |
| v9.7 | Mar 15 | Fintech, construction, insurtech, AI calling, developer persona |
| v9.8 | Mar 15 | Unicorn gate, company age gate, YC batch extraction |
| v9.9 | Mar 16 | Employee cross-reference, funding recency, CX tooling, score caps |
| v9.10+ | Mar-Apr | Merger/rebrand detection, PE pattern expansion |

See git history for full implementation details.
