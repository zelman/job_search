# Scoring Enhancements Backlog

Tracking false positives and scoring issues for pipeline improvements.

---

## False Positive: Zapier (Mar 2026)

**Record:**
- Company: Zapier
- URL: https://www.ycombinator.com/companies/zapier
- Tide-Pool Score: 82.0
- Stage: Seed (WRONG)
- Source: YC scraper

**Why this is wrong:**
- Zapier is a massive company (800+ employees per LinkedIn)
- Founded 2011 (YC S12) - 15 years old
- Raised $1.3B+ valuation, significant funding rounds
- Definitely NOT Seed stage - data enrichment failed
- No CS leadership hiring need at this scale

**What should have caught this:**

| Gate | Expected | Actual | Issue |
|------|----------|--------|-------|
| Employee cap (>150) | FAIL | PASS | Enrichment didn't find employee count |
| Funding cap (>$450M) | FAIL | PASS | Enrichment didn't find funding data |
| Stale company (>3yr since funding) | FAIL | PASS | No funding date extracted |
| Series D+ stage | FAIL | PASS | Stage from source was "Seed" (YC batch), not current |

**Root causes:**

1. **YC source data quality** - YC company pages show batch info (S12) which gets misinterpreted as "Seed" stage. The scraper isn't distinguishing between "YC batch" and "current funding stage."

2. **Enrichment failure** - Brave Search didn't return employee count or funding data for Zapier, so gates couldn't fire.

3. **Well-known company list missing Zapier** - The Fortune 500 / large company blocklist doesn't include Zapier.

**Proposed fixes:**

### Fix 1: Add Zapier to known large companies list
```javascript
const KNOWN_LARGE_COMPANIES = [
  'Zapier', 'Stripe', 'Notion', 'Figma', 'Canva',
  'Airtable', 'Webflow', 'Monday.com', 'Asana',
  // ... existing list
];
```

### Fix 2: YC batch != funding stage
In YC scraper, don't use batch (S12, W24) as funding stage. Either:
- Leave stage blank for enrichment to fill
- Map old batches (pre-2020) to "Unknown - verify"

### Fix 3: Enrichment fallback for well-known companies
If Brave Search returns no employee/funding data AND company name matches common tech companies, flag for manual review or auto-DQ.

### Fix 4: Company age gate from YC batch
YC S12 = Summer 2012 = 14 years ago. Add gate:
```javascript
// If YC batch is >5 years old, likely too mature
const batchYear = extractYearFromBatch(batch); // S12 -> 2012
const companyAge = currentYear - batchYear;
if (companyAge > 5) {
  // Flag as potentially too mature
}
```

---

## Backlog

### High Priority
- [ ] Fix YC batch → stage mapping
- [ ] Add Zapier + other unicorns to blocklist
- [ ] Add company age gate from YC batch year

### Medium Priority
- [ ] Enrichment retry for missing data
- [ ] Flag companies where enrichment returns nothing

### Low Priority
- [ ] Secondary enrichment source (Crunchbase API?)

---

*Last updated: Mar 2026*
