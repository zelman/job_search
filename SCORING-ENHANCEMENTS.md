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

## False Positive: SnapLogic (Mar 2026)

**Record:**
- Company: SnapLogic
- URL: https://www.snaplogic.com/
- Tide-Pool Score: High (top 25)
- Source: Unknown

**Why this is wrong:**
- 343-366 employees (well above 150 cap)
- $397-460M raised (above $450M cap)
- Series H funding (should DQ at Series D+)
- $1B valuation (unicorn)
- Enterprise integration platform - mature CS function exists

**What should have caught this:**

| Gate | Expected | Actual | Issue |
|------|----------|--------|-------|
| Employee cap (>150) | FAIL | PASS | Enrichment missed 350+ employees |
| Funding cap (>$450M) | FAIL | PASS | Enrichment missed $400M+ funding |
| Series D+ stage | FAIL | PASS | Series H not detected |
| Unicorn valuation | FAIL | PASS | No valuation gate exists |

**Root cause:** Enrichment failure - Brave Search didn't return any data for SnapLogic.

**Fix:** Add to KNOWN_LARGE_COMPANIES blocklist.

---

## False Positive: Modern Treasury (Mar 2026)

**Record:**
- Company: Modern Treasury
- URL: https://www.moderntreasury.com
- Tide-Pool Score: High (top 25)
- Source: Unknown

**Stats:**
- 137-155 employees (borderline on 150 cap)
- $183M raised
- Series D (latest Mar 2022)
- **$2B valuation (unicorn)**

**Issue:** Right at employee threshold, but unicorn valuation should trigger DQ.

**Root cause:** No unicorn/valuation gate in pipeline.

**Proposed fix:** Add valuation gate
```javascript
// Unicorn gate - $1B+ valuation
if (valuation_numeric >= 1000000000) {
  disqualify('Unicorn valuation (>$1B)');
}
```

---

## False Positive: Contra (Mar 2026)

**Record:**
- Company: Contra
- URL: https://contra.com
- Tide-Pool Score: High (top 25)
- Source: Unknown

**Stats:**
- 34 employees
- $45-59M raised
- Series B

**Issue:** Contra is a **freelancer marketplace** - should hit sector gate.

**Root cause:** Marketplace detection pattern didn't fire.

**Proposed fix:** Add to marketplace patterns
```javascript
const MARKETPLACE_PATTERNS = [
  /freelance.*(?:platform|marketplace|network)/i,
  /gig.*(?:platform|economy)/i,
  /(?:connect|match).*freelancers?/i,
  // existing patterns...
];
```

---

## False Positive: Soona (Mar 2026)

**Record:**
- Company: Soona
- URL: https://www.soona.co
- Tide-Pool Score: High (top 25)
- Source: Unknown

**Stats:**
- 100-250 employees
- $54M raised
- Series B

**Issue:** Soona is a **services business** (photo/video content creation for e-commerce) - should hit software-first gate.

**Root cause:** Services detection didn't catch "content creation studio" pattern.

**Proposed fix:** Add content services patterns
```javascript
const SERVICES_SIGNALS = [
  /content.*(?:creation|studio|production)/i,
  /photo(?:graphy)?.*(?:studio|service)/i,
  /video.*production/i,
  /creative.*(?:studio|agency|services)/i,
  // existing patterns...
];
```

---

## Developer Persona Review (Mar 2026)

Several developer-tool companies in top 25 may be correctly auto-passing via persona gate:

| Company | Product | Employees | Concern |
|---------|---------|-----------|---------|
| Coder | Dev workspaces | ~100 | OK if <50 or no enterprise signals |
| Educative | Dev education | ~100 | Likely OK - developer education |
| Zuplo | API gateway | Small | OK - pure developer tool |
| Kusari | Supply chain security | Small | Check for enterprise signals |
| Readyset | Database caching | Small | OK - pure developer tool |

**Review needed:** Verify persona gate is correctly requiring 3+ enterprise signals for companies >50 employees. Current threshold may be too permissive.

---

## Backlog

### Critical (Top 25 fixes)
- [ ] Add SnapLogic, Zapier to KNOWN_LARGE_COMPANIES blocklist
- [ ] Add unicorn valuation gate (>$1B)
- [ ] Add Contra-style marketplace patterns
- [ ] Add Soona-style content services patterns

### High Priority
- [ ] Fix YC batch → stage mapping
- [ ] Add company age gate from YC batch year
- [ ] Review developer persona threshold (3+ enterprise signals)

### Medium Priority
- [ ] Enrichment retry for missing data
- [ ] Flag companies where enrichment returns nothing
- [ ] Add Modern Treasury + other unicorns to watchlist

### Low Priority
- [ ] Secondary enrichment source (Crunchbase API?)

---

*Last updated: Mar 2026*
