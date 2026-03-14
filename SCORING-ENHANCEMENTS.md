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

## False Positive: Spellbook (Mar 2026)

**Record:**
- Company: Spellbook
- URL: https://www.spellbook.legal
- Tide-Pool Score: High (top 50)
- Source: Unknown

**Stats:**
- ~150 employees
- $84M raised
- Series B

**Issue:** Spellbook is a **Legal Tech** company (AI contract drafting for lawyers) - should hit sector gate.

**Root cause:** No Legal Tech sector gate in pipeline.

**Proposed fix:** Add Legal Tech to excluded sectors
```javascript
const LEGAL_TECH_PATTERNS = [
  /legal.*(?:tech|ai|software)/i,
  /law.*(?:firm|practice).*(?:software|platform)/i,
  /contract.*(?:drafting|management|automation)/i,
  /(?:attorney|lawyer|paralegal).*(?:tool|platform)/i,
  /e.?discovery/i,
  /litigation.*(?:support|software)/i
];
```

---

## False Positive: Kiwibot (Mar 2026)

**Record:**
- Company: Kiwibot
- URL: https://www.kiwibot.com
- Tide-Pool Score: High (top 50)
- Source: Unknown

**Stats:**
- ~100 employees
- $24M raised
- Series A

**Issue:** Kiwibot makes **delivery robots** (physical hardware) - should hit hardware gate.

**Root cause:** Hardware detection missed "robot" pattern.

**Proposed fix:** Add robotics patterns to hardware detection
```javascript
const HARDWARE_PATTERNS = [
  /robot(?:ic)?s?/i,
  /autonomous.*(?:vehicle|delivery)/i,
  /(?:delivery|warehouse).*robot/i,
  // existing patterns...
];
```

---

## False Positive: Earnin (Mar 2026)

**Record:**
- Company: Earnin
- URL: https://www.earnin.com
- Tide-Pool Score: High (top 50)
- Source: Unknown

**Stats:**
- 300+ employees
- $190M raised
- Series C+

**Issue:** Earnin is **consumer fintech** (earned wage access app for individuals) - should hit consumer/B2C gate.

**Root cause:** Consumer detection missed "earned wage access" pattern. Also should fail employee cap (>200).

**Proposed fix:** Add EWA patterns to consumer detection
```javascript
const CONSUMER_FINTECH_PATTERNS = [
  /earned.?wage.?access/i,
  /pay.?advance/i,
  /paycheck.?advance/i,
  /(?:personal|consumer).*(?:finance|loan|credit)/i,
  /(?:app|mobile).*(?:bank|wallet|pay)/i,
  // existing patterns...
];
```

---

## False Positive: Brainbase (Mar 2026)

**Record:**
- Company: Brainbase
- URL: https://brainbase.com
- Tide-Pool Score: High (top 50)
- Source: Unknown

**Why this is wrong:**
- **Acquired by Jonas Software (Constellation/Volaris PE) in September 2022**
- No longer an independent company
- PE-backed post-acquisition

**Root cause:** Acquisition detection failed. Company was acquired 3+ years ago.

**Proposed fix:** Add Jonas Software to PE acquirer list
```javascript
const PE_ACQUIRERS = [
  'Jonas Software', 'Constellation Software', 'Volaris Group',
  'Harris Computer', 'Total Specific Solutions',
  // existing list...
];
```

Also: Add acquisition year check - if acquired >1 year ago, auto-DQ.

---

## False Positive: VoltServer (Mar 2026)

**Record:**
- Company: VoltServer
- URL: https://voltserver.com
- Tide-Pool Score: High (top 50)
- Source: Unknown

**Stats:**
- 57 employees
- $40M raised
- Series B
- Founded 2011 (15 years old)

**Issue:** VoltServer is a **hardware company** making Digital Electricity transmission products (Fault Managed Power systems). Physical manufacturing company.

**Root cause:** Hardware detection missed "electricity transmission products" and "power distribution" patterns.

**Proposed fix:** Add power/energy hardware patterns
```javascript
const HARDWARE_PATTERNS = [
  /(?:power|electricity).*(?:distribution|transmission)/i,
  /energy.*(?:device|hardware|equipment)/i,
  /manufacturing.*(?:product|equipment)/i,
  // existing patterns...
];
```

---

## False Positive: Mighty Networks (Mar 2026)

**Record:**
- Company: Mighty Networks
- URL: https://www.mightynetworks.com
- Tide-Pool Score: High (top 50)
- Source: Unknown

**Stats:**
- 79-148 employees
- $71.8M raised
- Series B
- Founded 2010 (16 years old)

**Issues:**
1. **Creator economy/marketplace** - Connects creators to audiences (B2B2C platform)
2. **Company age** - Founded 2010, 16 years old, well past growth phase
3. **Funding borderline** - $71.8M just under $75M soft cap

**Root cause:** Community platform pattern not caught by marketplace gate. Age gate not implemented.

**Proposed fix:** Add creator economy patterns to marketplace detection
```javascript
const MARKETPLACE_PATTERNS = [
  /creator.*(?:economy|platform|network)/i,
  /(?:community|membership).*platform/i,
  /connect.*(?:creators?|influencers?)/i,
  // existing patterns...
];
```

Also: Founded 2010 should trigger age gate (>10 years = auto-DQ or heavy penalty).

---

## False Positive: Thinkful (Mar 2026)

**Record:**
- Company: Thinkful
- URL: https://www.thinkful.com
- Source: Unknown

**Issue:** **Acquired by Chegg in October 2019** for $80M. Rebranded to "Chegg Skills" in 2023. No longer an independent company.

**Root cause:** Acquisition detection failed for older acquisition (2019).

---

## False Positive: Athena Security (Mar 2026)

**Record:**
- Company: Athena Security
- URL: https://www.athena-security.com
- Source: Unknown

**Stats:**
- 45-100 employees
- $18.5M raised
- Seed (latest Aug 2024)

**Issue:** **Physical security hardware** - Weapons detection systems for schools, casinos, hospitals. High-distance domain.

**Root cause:** Physical security sector gate exists in v9 but may not have fired.

---

## False Positive: InternMatch (Mar 2026)

**Record:**
- Company: InternMatch
- URL: Kapor Capital portfolio
- Source: Unknown

**Stats:**
- Founded 2009
- Last funding 2013 (Series A, $4M)
- Total raised ~$6M

**Issues:**
1. **HR Tech / Recruiting platform** - Should hit HR Tech sector gate
2. **Stale company** - Last funding 13+ years ago (2013)
3. **Company age** - Founded 2009, 17 years old

**Root cause:** HR Tech gate may not have detected "intern matching" pattern. Stale company gate didn't fire.

---

## False Positive: Ebb Carbon (Mar 2026)

**Record:**
- Company: Ebb Carbon
- URL: https://www.ebbcarbon.com
- Source: Congruent VC portfolio

**Stats:**
- ~25 employees
- $24.8M raised
- Series A

**Issue:** **Climate tech hardware** - Electrochemical carbon capture systems (physical hardware in shipping containers). Not software.

**Root cause:** Climate tech hardware gate should catch this.

---

## False Positive: Helcim (Mar 2026)

**Record:**
- Company: Helcim
- URL: https://www.helcim.com
- Source: Unknown

**Stats:**
- 152 employees
- $32.7M raised (CAD)
- Series B
- Founded 2006 (20 years old)
- **HQ: Calgary, Canada**

**Issues:**
1. **Non-US primary market** - Canadian HQ
2. **Company age** - Founded 2006, 20 years old
3. **Employee count borderline** - 152 (just above 150 cap)

**Root cause:** Geography gate (non-US) should catch this. Age gate should also fire.

---

## False Positive: Mazama Energy (Mar 2026)

**Record:**
- Company: Mazama Energy
- URL: https://mazamaenergy.com
- Source: Unknown

**Stats:**
- Founded 2023
- $36M Series A + $20M DOE grant
- Based in Plano, Texas

**Issue:** **Climate tech / Energy infrastructure** - Geothermal drilling (superhot rock). Physical infrastructure, not software.

**Root cause:** Climate tech hardware gate should catch geothermal drilling.

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
- [x] Add SnapLogic, Zapier to KNOWN_LARGE_COMPANIES blocklist ✅ **Done in v9.2**
- [ ] Add unicorn valuation gate (>$1B)
- [ ] Add Contra-style marketplace patterns
- [ ] Add Soona-style content services patterns

### Critical (Top 50 fixes)
- [x] ~~Add Legal Tech sector gate (Spellbook)~~ **REMOVED** — Legal Tech is target sector (Paxton.ai). See correction above.
- [ ] Add robotics/autonomous patterns to hardware gate (Kiwibot)
- [ ] Add EWA/pay-advance patterns to consumer gate (Earnin)
- [x] Add Jonas Software to PE acquirer list (Brainbase) ✅ **Already in v9.1 PE list**
- [x] Add acquisition age check (acquired >1 year ago → auto-DQ) ✅ **Done in v9.2** — knownAcquired list
- [ ] Add power/energy hardware patterns to hardware gate (VoltServer)
- [ ] Add creator economy/community platform patterns to marketplace gate (Mighty Networks)
- [ ] Add company age gate (>10 years = auto-DQ or heavy penalty)

### Critical (Rows 53-78 fixes)
- [x] Improve acquisition detection for older acquisitions (Thinkful → Chegg 2019) ✅ **Done in v9.2** — knownAcquired list
- [ ] Verify physical security sector gate firing (Athena Security)
- [ ] Add "intern matching" to HR Tech patterns (InternMatch)
- [ ] Verify stale company gate (InternMatch - no funding since 2013)
- [ ] Verify climate tech hardware gate (Ebb Carbon, Mazama Energy)
- [x] Verify geography gate for non-US HQ (Helcim - Canada) ✅ **Done in v9.2** — Added Calgary, Vancouver, Montreal

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

---

# Batch 1 & 2 Manual Review — Pattern Analysis (Rows 1–52, Mar 12 2026)

_~52 companies reviewed manually. False positive rate: ~40% Batch 1 (rows 1–26, scores 72–78), ~65% Batch 2 (rows 27–52, scores 62–72). Signal rate: ~4–6 genuine Monitor candidates per 25 companies._

---

## Correction to Existing Entry: Spellbook

The existing Spellbook entry proposes adding a Legal Tech sector gate to excluded sectors. **This is wrong.** Paxton.ai — Eric's current top pipeline candidate — is also legal AI SaaS. Legal Tech is a target sector, not an excluded one.

The actual Spellbook problem: Spellbook already has a **built-out CS function** (4,000 customers, multiple CSMs visible on LinkedIn, VP Customer Success in place). It should have been caught by a CS Hire Readiness check, not a sector gate.

**Remove the Legal Tech sector gate proposal. Add instead:**
- During CS Hire Readiness evaluation, check LinkedIn for "[company] customer success" titles
- If VP/Head/Director of CS is currently employed: CS Hire Readiness = 0, flag as "manage-and-optimize"
- If 3+ IC CSM titles found with no leadership gap: flag as "CS function established, not a build"

---

## New False Positive Pattern: CS Tooling / CS Platform as the Product

**Companies affected:** HeySam (Afore Capital, Series B), Nooks.ai

**Pattern:** Companies that build CS or sales automation software score well on "enterprise B2B SaaS" and "business-user persona" because their customers are CS/sales teams. But these are functional mismatches — Eric would be a buyer, not a hire.

**Root cause:** No gate exists for "product IS the CS tooling."

**Proposed fix:**
```javascript
const CS_TOOLING_PATTERNS = [
  /customer success (?:platform|software|tool|automation)/i,
  /(?:cs|csm) (?:platform|tool|workflow)/i,
  /customer health (?:score|scoring)/i,
  /digital customer success/i,
  /sales (?:engagement|automation) platform/i,
  /revenue intelligence/i,
];
// If matched: disqualify as functional mismatch — "product is CS tooling"
```

---

## New False Positive Pattern: Carbon Credits as Primary Revenue

**Companies affected:** Ebb Carbon (already documented above), Carbonrun (Golden Ventures)

**Pattern:** Climate tech companies selling carbon removal credits to hyperscalers score as "enterprise B2B SaaS" because they have Fortune 500 customers and strong VC backing. Carbon credit procurement is a commodity transaction, not a software subscription.

**Root cause:** Carbon credit revenue model not filtered. "Enterprise customers" heuristic too broad.

**Proposed fix:**
```javascript
const CARBON_CREDIT_PATTERNS = [
  /carbon (?:credit|removal credit|offset)/i,
  /(?:sell|purchase) (?:carbon|co2) (?:credit|removal)/i,
  /ocean (?:carbon|co2) removal/i,
  /electrochemical.*carbon/i,
  /direct air capture/i,
];
// Carbon credits as primary revenue = not SaaS, hard disqualify
```

---

## New False Positive Pattern: DOE Grants as Negative SaaS Signal

**Companies affected:** Mazama Energy ($20M DOE grant alongside $36M Series A)

**Pattern:** Companies receiving DOE or ARPA-E grants are typically hardware/research-stage infrastructure companies, not enterprise SaaS. The grant is a reliable negative signal for SaaS classification.

**Proposed fix:** During enrichment, if funding sources include a DOE grant or ARPA-E award, add flag: "likely hardware/research-stage — verify SaaS before scoring."

---

## New False Positive Pattern: Acquired Companies from Stale VC Portfolio Pages

**Companies affected:** Tempus-ex (acquired by EXOS Oct 2025), Brainbase (Jonas Software Sept 2022 — already documented), Thinkful (Chegg 2019 — already documented)

**New acquisition to add to blocklist:**
```javascript
const KNOWN_ACQUIRED = [
  { name: 'Tempus-ex', acquirer: 'EXOS', date: '2025-10' },
  { name: 'Tempus Ex Machina', acquirer: 'EXOS', date: '2025-10' },
  // existing entries...
];
```

**Structural observation:** VC firms don't reliably remove acquired companies from portfolio pages. Acquisition detection must be a **required enrichment step** before scoring — not an optional check. Every company should be searched "[company name] acquired" before the scoring pipeline continues.

---

## New False Positive Pattern: "Manage-and-Optimize" CS Roles Misidentified as Build Opportunities

**Companies affected:** Spellbook (VP CS in place, 4,000 customers), Rimsys (Senior CSM already on staff, open IC CSM role with renewal language), Nooks.ai (VP Customer Success hired Jan 2025)

**Pattern:** Companies score well on CS Hire Readiness due to stage and sector, but already have functioning CS teams. Open roles have NRR/renewal/expansion language indicating manage-and-optimize mandates.

**Root cause:** CS Hire Readiness scoring doesn't distinguish "no CS function exists" from "CS function exists and is hiring."

**Proposed fix — two-tier CS readiness check:**

- **Tier 1 (25 pts):** No CS function at all — founder-led customers, zero CS titles on LinkedIn
- **Tier 2 (10 pts):** CS function exists but no leader above IC level — CSMs with no VP/Head/Director above them
- **0 pts + flag:** CS leadership (VP CS, Head of CS, Director of CS) currently employed

**Role language check:** If open job posting includes NRR, GRR, renewal ownership, expansion quota, or upsell targets → subtract 15 pts and flag as manage-and-optimize regardless of title.

---

## New False Positive Pattern: B2B2C Consumer-Benefit Products

**Companies affected:** Marble Health (B2C patient-to-clinician routing), Earnin (already documented above), Hint Health (direct primary care sold through employer benefits)

**Pattern:** Companies with employer-channel distribution score as B2B because "employers pay." The actual product is a consumer benefit — the employer is a distribution channel, not an enterprise software procurement buyer.

**Proposed fix:**
```javascript
const B2B2C_CONSUMER_SIGNALS = [
  /direct primary care/i,
  /(?:mental health|therapy|wellness) (?:app|platform) for (?:employees|teams)/i,
  /earned.?wage.?access/i,
  /financial wellness.*employees/i,
  /employee benefit.*(?:app|platform)/i,
];
// Flag for human review: B2B2C requires manual assessment.
// Key question: does CS manage the employer relationship (procurement/adoption)
// or the consumer/employee experience? Only the former is a fit.
```

---

## New False Positive Pattern: Non-US HQ Without US Presence

**Companies affected:** Defacto (Paris, French RBF fintech), Carbonrun (Canadian), Helcim (already documented above)

**Exception — Limbic:** London HQ but actively hiring a Director of CS specifically for US expansion. Valid Monitor candidate. Geography gate should allow companies with documented US expansion roles.

**Proposed fix:**
```javascript
// If HQ is non-US:
// - Check for US office on website or LinkedIn
// - Check whether open roles are US-based
// - No US presence: score = 0, disqualify
// - US expansion roles documented: retain as Monitor only (not Apply)
```

---

## Scoring Weight Issue: VC Brand Heuristic Overweighted

**Observation:** Khosla Ventures (Mazama Energy), Congruent Ventures (Ebb Carbon, Renderedai), Golden Ventures (Carbonrun) all caused false positives by inflating scores via VC brand — even for hardware and process-chemistry companies.

**Root cause:** VC quality is a first-tier score component, not a tiebreaker. It's rescuing companies that should have failed business model gates.

**Proposed fix:** Move VC quality to a late-stage modifier (max +5 pts), applied only after all binary gates have passed. VC brand should never override a failed business model, hardware, or sector gate.

---

## CS Hire Readiness: Positive Signals That Proved Reliable in Batches 1–2

Every genuine Monitor candidate had at least two of the following. These should drive positive CS Hire Readiness scoring — not stage alone:

| Signal | Companies where observed |
|--------|-------------------------|
| No CS leader visible on LinkedIn (founder-led customers) | First Street, Limbic, Enfi, Alkymi, Paxton.ai |
| First CRO/Head of Sales hired within 6 months, no CS counterpart | Enfi (CRO Jan 2026), First Street |
| Active VP/Head/Director of CS posting with "build" or "founding" language | Limbic (Director of CS, US build) |
| 30–80 employees, Series A, B2B SaaS, no CS role visible at all | Alkymi, Paxton.ai |
| Regulated industry (healthcare, legal, medtech, financial services) | All five top candidates from both batches |
| Provider-side healthcare (hospital, clinic, behavioral health) | Limbic, Paxton.ai, CERTIFY Health |

**Proposed change:** If none of these signals are present in sourced data, CS Hire Readiness defaults to 0. Stage alone ("Series A companies often hire CS") is not evidence and must not generate a positive signal.

---

## Summary Generator Quality Issues (Batch 2)

**Examples of fabricated signals in automated summaries:**
- Mazama Energy: "enterprise energy sector is actively hiring CS talent" — not sourced
- Ebb Carbon: "Series A stage indicates likely upcoming scaling in CS/GTM roles" — generic inference
- Renderedai: "enterprise climate tech space presents moderate CS hiring potential" — no evidence found

**Pattern:** Generator uses stage-based reasoning ("Series A = CS hiring likely") as a positive CS Hire Likelihood signal. This is a primary driver of the ~65% false positive rate in Batch 2.

**Fix:** Summary generator should only assert positive CS hire likelihood when at least one of these is confirmed in sourced data:
1. Active job posting for a CS leadership role
2. Recent CRO/VP Sales hire with no corresponding CS leader found
3. Company description or executive statement referencing scaling customer relationships
4. Job board search returns a CS build/founding role

If none found: `CS Hire Likelihood = "low"`. Do not default to "medium." Stage is not evidence.

---

## Backlog Additions from Batches 1 & 2

### Critical (New gates needed)
- [ ] **Correction:** Remove Legal Tech sector gate from Spellbook proposal — Legal Tech is a target sector. Replace with CS function existence check (see correction above)
- [ ] Add CS tooling/platform detection gate — disqualify when product IS the CS tool (HeySam, Nooks.ai)
- [ ] Add carbon credit revenue model as hard disqualifier (Ebb Carbon, Carbonrun)
- [ ] Add DOE/ARPA-E grant as negative SaaS enrichment flag
- [ ] Two-tier CS Hire Readiness: no CS exists (25 pts) vs. CS exists no leader (10 pts) vs. CS leadership in place (0 pts + flag)
- [ ] Role language check: NRR/GRR/renewal/expansion quota in posting = subtract 15 pts + manage-and-optimize flag
- [ ] B2B2C consumer-benefit detection (Marble Health, Hint Health)
- [x] Geography gate: non-US HQ without US presence = disqualify; US expansion roles = Monitor only ✅ **Partially done in v9.2** — Added Canadian cities
- [ ] Demote VC brand signal to late-stage modifier (max +5 pts) — never overrides a failed gate
- [x] Make acquisition search a required enrichment step — run before scoring, not after ✅ **Done in v9.2** — knownAcquired list checks by name
- [x] Add KNOWN_ACQUIRED: Tempus-ex / Tempus Ex Machina (EXOS, Oct 2025) ✅ **Done in v9.2**
- [ ] Summary generator: default CS Hire Likelihood to "low" unless specific evidence found — stage alone is not evidence

---

*Last updated: Mar 12 2026 — Batches 1–3 complete (rows 1–78). v9.2 quick wins implemented.*

---

# Implementation Plan for v9.2

## Overview

Based on review of 78 companies across 3 batches:
- **Signal rate:** ~13-15% (10-12 genuine Monitor candidates)
- **False positive rate:** ~50-60%
- **Expected improvement:** False positives drop to ~20-25% after implementing Phases 1-4

## Pipeline Architecture (Current v9.1)

The pipeline already has the right structure:
1. **Entity Validation** (Phase 0) - catches podcasts, nonprofits
2. **Brave Search Enrichment** (Phase 1)
3. **Parse Enrichment** - extracts data from search results
4. **IF: Auto-Disqualify** (Phase 2) - gate checks
5. **Classify Persona** (Phase 3) - business-user vs developer
6. **Check CS Hire Readiness** (Phase 4) - Claude call
7. **Full Evaluation** (Phase 5) - 100-point scoring

Changes are modifications to existing nodes, not new architecture.

---

## Phase 1: Parse Enrichment Patterns

**Node:** `Parse Enrichment` (Code node after Brave Search)
**Effort:** 2-3 hours
**Impact:** Catches ~15 false positives

### New Pattern Groups to Add

```javascript
// =============================================
// REQUIRED ACQUISITION SEARCH (not optional)
// =============================================
const ACQUISITION_PATTERNS = [
  /acquired by ([A-Z][a-z]+)/i,
  /bought by|merged with|now part of/i,
  /subsidiary of|portfolio company of/i,
  /joined ([A-Z][a-z]+) family/i,
];

const KNOWN_ACQUIRED = [
  { name: 'Tempus-ex', acquirer: 'EXOS', date: '2025-10' },
  { name: 'Tempus Ex Machina', acquirer: 'EXOS', date: '2025-10' },
  { name: 'Brainbase', acquirer: 'Jonas Software', date: '2022-09' },
  { name: 'Thinkful', acquirer: 'Chegg', date: '2019-10' },
];

// =============================================
// GEOGRAPHY DETECTION
// =============================================
const NON_US_HQ_PATTERNS = [
  /(?:headquartered|based|hq) in (?!.*(?:US|USA|United States))/i,
  /London|Berlin|Paris|Singapore|Toronto|Tel Aviv|Calgary/i,
  /UK-based|European|EMEA|APAC/i,
];

const US_EXPANSION_SIGNALS = [
  /us expansion|expanding to (?:the )?us/i,
  /hiring.*(?:us|united states|america)/i,
  /director.*us|us.*director/i,
];

// Output: is_non_us_hq, has_us_expansion_signal
// Gate logic: DQ if is_non_us_hq && !has_us_expansion_signal

// =============================================
// CARBON CREDIT / CLIMATE HARDWARE
// =============================================
const CARBON_CREDIT_PATTERNS = [
  /carbon (?:credit|removal credit|offset)/i,
  /(?:sell|purchase) (?:carbon|co2) (?:credit|removal)/i,
  /ocean (?:carbon|co2) removal/i,
  /electrochemical.*carbon/i,
  /direct air capture/i,
];

const DOE_GRANT_SIGNAL = /doe grant|arpa-e|department of energy/i;

// Output: is_carbon_credit_revenue, has_doe_grant
// Gate logic: Hard DQ for carbon credits; flag for DOE grant

// =============================================
// CS TOOLING AS PRODUCT (functional mismatch)
// =============================================
const CS_TOOLING_PATTERNS = [
  /customer success (?:platform|software|tool|automation)/i,
  /(?:cs|csm) (?:platform|tool|workflow)/i,
  /customer health (?:score|scoring)/i,
  /digital customer success/i,
  /sales (?:engagement|automation) platform/i,
  /revenue intelligence/i,
];

// Output: is_cs_tooling_product
// Gate logic: Hard DQ — "product is CS tooling, functional mismatch"

// =============================================
// B2B2C CONSUMER-BENEFIT
// =============================================
const B2B2C_CONSUMER_PATTERNS = [
  /direct primary care/i,
  /(?:mental health|therapy|wellness) (?:app|platform) for (?:employees|teams)/i,
  /earned.?wage.?access/i,
  /financial wellness.*employees/i,
  /employee benefit.*(?:app|platform)/i,
];

// Output: is_b2b2c_consumer
// Gate logic: Flag for human review, not hard DQ

// =============================================
// EXPANDED MARKETPLACE PATTERNS
// =============================================
const MARKETPLACE_PATTERNS = [
  /freelance.*(?:platform|marketplace|network)/i,
  /creator.*(?:economy|platform|network)/i,
  /(?:community|membership).*platform/i,
  /connect.*(?:creators?|influencers?)/i,
  /bankruptcy.*(?:claims|marketplace)/i,
  /gig.*(?:platform|economy)/i,
];

// Output: is_marketplace
// Gate logic: Hard DQ
```

---

## Phase 2: Gate Logic Updates

**Node:** `IF: Auto-Disqualify` (IF node after Parse Enrichment)
**Effort:** 1 hour
**Impact:** Enforces new patterns

### Updated Gate Conditions

```javascript
// TIER 1: HARD GATES (existing)
const tier1Disqualify =
  is_acquired ||
  pe_backed ||
  is_public ||
  is_fortune500 ||
  employee_count > 150 ||
  total_funding_numeric > 450000000 ||
  valuation_numeric > 1000000000 ||  // Unicorn gate
  /series d|series e|growth/i.test(funding_stage);

// TIER 2: SECTOR GATES (existing + new)
const tier2Disqualify =
  is_biotech ||
  is_hardware ||
  is_crypto ||
  is_consumer ||
  is_hrtech ||
  is_marketplace ||
  is_cs_tooling_product ||      // NEW
  is_carbon_credit_revenue;      // NEW

// TIER 3: GEOGRAPHY GATE (NEW)
const tier3Disqualify =
  is_non_us_hq && !has_us_expansion_signal;

// TIER 4: SOFT FLAGS (proceed but flag)
const tier4Flags = {
  has_doe_grant: has_doe_grant,           // NEW
  is_b2b2c_consumer: is_b2b2c_consumer,   // NEW
  is_borderline_employees: employee_count >= 100 && employee_count <= 150,
};

// Combined disqualification
const isAutoDisqualified = tier1Disqualify || tier2Disqualify || tier3Disqualify;
```

---

## Phase 3: CS Hire Readiness Prompt

**Node:** `Build CS Readiness Prompt` (Code node before Claude call)
**Effort:** 1-2 hours
**Impact:** Fixes stage-inference false positives

### Updated Prompt Template

```
You are evaluating whether a company is actively building a post-sales Customer Success function.

Company: {company_name}
Description: {description}
Employees: {employee_count}
Funding: {funding_stage}, {total_funding}
Enrichment data: {enrichment_summary}

## SCORING TIERS (use evidence, not inference)

**Tier 1 (25 pts): No CS function exists**
- Founder-led customers, zero CS titles visible
- No mention of customer success team or roles
- Early stage with product-market fit signals but no post-sales motion

**Tier 2 (10 pts): CS exists but no leader**
- IC CSMs visible (1-3 people) but no VP/Head/Director above them
- CS function is nascent, leadership gap exists

**Tier 3 (0 pts): CS leadership in place**
- VP Customer Success, Head of CS, or Director of CS currently employed
- Established CS function with management layer
- Flag as "manage-and-optimize" — not a build opportunity

## EVIDENCE REQUIRED

Do NOT infer CS hiring need from stage alone. "Series A companies often hire CS" is not evidence.

Positive evidence (at least one required for score > 0):
1. Active CS leadership job posting with "build" or "founding" language
2. Recent CRO/VP Sales hire (past 6 months) with no CS counterpart found
3. Company statement about scaling customer relationships or post-sales
4. 30-80 employees, B2B SaaS, regulated industry, no CS role visible

If no evidence found: score = 0, reasoning = "No evidence of CS build need found"

## ROLE LANGUAGE CHECK

If job posting contains: NRR, GRR, renewal ownership, expansion quota, upsell targets
→ Subtract 15 pts and flag as "manage-and-optimize role, not a build"

## OUTPUT

Return JSON:
{
  "cs_readiness_score": N,        // 0-25
  "cs_function_tier": 1|2|3,
  "evidence_found": ["list of specific evidence"],
  "is_manage_and_optimize": true|false,
  "reasoning": "brief explanation with citations"
}
```

---

## Phase 4: Evaluation Prompt (VC Brand Demotion)

**Node:** `Build Evaluation Prompt` (Code node before final Claude call)
**Effort:** 30 minutes
**Impact:** Stops VC brand from rescuing bad fits

### Change to Scoring Instructions

```
## VC BRAND MODIFIER (CHANGED)

VC quality is now a LATE-STAGE MODIFIER, not a base score component.

Apply ONLY after all gates have passed:
- Tier 1 VC (a16z, Sequoia, Khosla, Bessemer, etc.): +5 pts max
- Tier 2 VC (established but smaller): +3 pts max
- Unknown/Angel: +0 pts

IMPORTANT: This modifier NEVER overrides a failed business model,
hardware, or sector gate. A carbon capture company backed by Khosla
is still a carbon capture company.

Previous weight: VC brand could contribute 10-15 pts to base score
New weight: VC brand contributes 0-5 pts as final modifier
```

---

## Phase 5: LinkedIn CS Function Check (Optional)

**Effort:** 3-4 hours (requires API integration)
**Impact:** Nice-to-have, improves CS Readiness accuracy

### Options

1. **Brave Search approach (free)**
   - Add `"[company] customer success" site:linkedin.com` to search query
   - Parse results for VP/Head/Director titles
   - Limitation: Brave may not return LinkedIn results reliably

2. **Proxycurl API ($50-100/mo)**
   - Direct LinkedIn company employee search
   - Filter by title containing "customer success"
   - Most accurate but adds cost

3. **Skip for now**
   - Rely on CS Readiness prompt inference
   - Accept some false positives in exchange for simplicity
   - Revisit if signal rate doesn't improve enough

### Recommendation

Start with Phases 1-4. If signal rate improves to 25%+, Phase 5 is optional. If still below 20%, implement Phase 5 with Proxycurl.

---

## Implementation Summary

| Phase | Node to Modify | Effort | Impact |
|-------|----------------|--------|--------|
| 1 | Parse Enrichment | 2-3 hrs | Catches ~15 FPs via pattern matching |
| 2 | IF: Auto-Disqualify | 1 hr | Enforces new patterns as gates |
| 3 | Build CS Readiness Prompt | 1-2 hrs | Fixes stage-inference problem |
| 4 | Build Evaluation Prompt | 30 min | Demotes VC brand to modifier |
| 5 | New enrichment step (optional) | 3-4 hrs | LinkedIn CS function check |

**Total for Phases 1-4:** ~5-7 hours
**Expected outcome:** False positive rate drops from ~55% to ~20-25%

---

## Testing Plan

After implementing v9.2:

1. **Rerun Batch 1-3 companies** (78 total) through new pipeline
2. **Compare scores** — false positives should now DQ or score lower
3. **Verify genuine candidates** still score well (Limbic, Alkymi, Paxton.ai)
4. **Spot check** 10-20 new companies from live scraper runs

### Expected Results by Company

| Company | v9.1 Result | v9.2 Expected |
|---------|-------------|---------------|
| Ebb Carbon | Scored high | DQ: carbon credit revenue |
| Mazama Energy | Scored high | DQ: climate hardware + DOE grant flag |
| Helcim | Scored high | DQ: non-US HQ (Canada) |
| Fieldguide | Scored high | DQ or low: CS function established |
| Spellbook | Scored high | DQ: CS leadership in place |
| Nooks.ai | Scored high | DQ: CS tooling as product |
| Limbic | Scored high | Still high (US expansion exception) |
| Alkymi | Scored high | Still high (genuine candidate) |

---

*Implementation plan documented: Mar 12 2026*

---

# v9.2 Changelog (Implemented Mar 12 2026)

## Quick Wins Implemented

These were simple array additions requiring no logic changes:

### 1. Known Large Companies List (NEW)
```javascript
const knownLargeCompanies = [
  'Zapier', 'SnapLogic', 'Stripe', 'Notion', 'Figma', 'Canva',
  'Airtable', 'Webflow', 'Monday.com', 'Asana'
];
```
- Auto-DQ if company name matches
- Bypasses enrichment failures for well-known large companies

### 2. Known Acquired Companies List (NEW)
```javascript
const knownAcquired = [
  { name: 'Thinkful', acquirer: 'Chegg', year: 2019 },
  { name: 'Brainbase', acquirer: 'Jonas Software', year: 2022 },
  { name: 'Tempus-ex', acquirer: 'EXOS', year: 2025 },
  { name: 'Tempus Ex Machina', acquirer: 'EXOS', year: 2025 }
];
```
- Auto-DQ if company name matches
- Catches stale VC portfolio entries

### 3. Canadian Cities Added to Non-US Geography
```javascript
// Added to nonUSHQPatterns and nonUSSignals:
Calgary, Vancouver, Montreal, Canadian
```
- Catches Helcim and other Canadian HQ companies

## Files Changed
- `Enrich & Evaluate Pipeline v9.1.json` → renamed to `v9.2.json`
- `CLAUDE.md` → updated version references

## Remaining Work
See Implementation Plan above for Phases 1-5 (~5-7 hours total)
