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

(none pending)
