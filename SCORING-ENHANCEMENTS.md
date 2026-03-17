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
- [x] Add unicorn valuation gate (>$1B) ✅ **Done in v9.8**
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

## Batch 3: March 11, 2026 Manual Triage (51 companies)

**Signal rate:** ~8% (4/51 Monitor or better)
**False positive rate in scored list:** ~72% (18/25 in "Apply Now" queue were false positives)
**Source:** Manual fit analysis of 51 companies from mixed pipeline sources

### New Failure Patterns

#### 3.1 PE Gate Not Firing on Named PE Firms

**Problem:** Absorb LMS is backed by Welsh Carson Anderson & Stowe (WCAS), a named PE firm. The company would score on SaaS + healthcare adjacency + revenue metrics before the PE gate fires. WCAS may not be in the PE blocklist.

**Fix:** Audit PE blocklist against known PE firms that invest in SaaS. Add at minimum: Welsh Carson (WCAS), Vista Equity Partners, Thoma Bravo, Francisco Partners, Clearlake Capital, Ares Management, Carlyle Group, Hellman & Friedman, Insight Partners (when acting as PE), Silver Lake. The PE gate must run as a binary pre-scoring check, not a weighted factor.

**Status:** [ ] Not implemented

---

#### 3.2 Non-SaaS Services Businesses Passing Sector Gate

**Problem:** Nomi Health (direct healthcare services, 344 employees), Vesta Healthcare (virtual care services, $187M), Nava Benefits (brokerage model, 173 employees) all contain "healthcare" in their description but are services businesses, not SaaS. The sector gate catches the keyword but not the business model.

**Fix:** Add a business model pre-scoring gate that runs before sector scoring. Key disqualifiers: "direct services," "brokerage," "staffing," "consulting," revenue model tied to per-visit/per-procedure/per-member rather than subscription. Look for negative signals: no "platform" or "software" in company description, presence of "services" as primary descriptor rather than modifier.

**Status:** [ ] Not implemented

---

#### 3.3 Consumer Products Scoring as B2B

**Problem:** Aavia (consumer health/femtech), Livetinted (beauty/lifestyle), calljoey.ai (consumer AI dating) could score on customer-count or user-count dimensions if the model pulls "customers" or "users" from marketing copy. Consumer apps are not B2B SaaS.

**Fix:** Add a B2B/B2C classification gate in Phase 2 (pre-evaluation). Signals for B2C: "app store," "download," "users" without "enterprise" or "team" qualifier, consumer verticals (beauty, dating, personal finance, fitness). This gate should fire before CS Hire Readiness scoring, which assumes B2B motion.

**Status:** [ ] Not implemented

---

#### 3.4 Grant-Funded Orgs Not Blocked Early

**Problem:** Onc.AI is grant-funded and pre-commercial. No VC signal. The pipeline should not spend scoring cycles on companies that haven't raised institutional VC funding.

**Fix:** Add a funding source validation in Phase 1 (enrichment). If primary funding source is grants (NIH, NSF, SBIR, etc.) with no institutional VC round, flag as "pre-commercial" and auto-pass. The VC-backing binary gate should catch this, but the enrichment phase needs to detect grant-only funding patterns.

**Status:** [ ] Not implemented

---

#### 3.5 Stale Funding Not Penalized

**Problem:** Hint Health ($3.7M revenue after 12 years, no funding since 2022) and Siteline (last round Feb 2022, no activity in 3+ years) passed enough surface criteria to appear in the pipeline. Companies with no funding activity in 2+ years are unlikely to be in a CS hiring window.

**Fix:** Add a funding recency penalty in Phase 2. If last funding round is >24 months ago AND total funding is <$30M, apply a -15 point modifier or auto-flag for manual review. Exception: profitable bootstrapped companies with active job postings (rare but possible).

**Status:** [ ] Not implemented

---

#### 3.6 Services/Consulting Hybrids Mimicking SaaS

**Problem:** Socially Determined presents as analytics/SaaS but operates as a consulting/data services hybrid. Marketing copy passes the sector filter, but the actual business model doesn't qualify. Similar pattern to 3.2 but more subtle: the company has a software product but revenue is primarily services.

**Fix:** Extend the business model gate (3.2) to look for hybrid signals: "consulting," "advisory," "professional services" as revenue line items, team composition heavily weighted toward consultants/analysts rather than engineers/product. This is harder to detect automatically and may need to remain a manual triage flag.

**Status:** [ ] Not implemented

---

#### 3.7 Developer-as-Customer Gate Not Blocking Early Enough

**Problem:** Coder, Zuplo, Kusari, Pinwheel, Jam all have "platform," "SaaS," and "enterprise" in their marketing copy but serve developers as primary customer persona. The customer persona gate runs correctly but may run after CS Hire Readiness scoring has already inflated the score.

**Fix:** Confirm that Phase 3 (Customer Persona Classification) runs BEFORE Phase 4 (CS Hire Readiness Threshold). If a company is classified as developer-as-customer AND has <50 employees, it should be auto-passed before CS Hire Readiness scoring runs. Current pipeline architecture may already handle this, but validate execution order.

**Status:** [ ] Verify pipeline execution order

---

#### 3.8 Company-Level vs. Role-Level Evaluation Gap (By Design)

**Problem:** Candid Health correctly scored as Monitor (provider-side healthcare SaaS, right size, right funding). But the specific role posted was contributor-level into an existing CS team, not a build mandate. The scoring model evaluates the company, not the role. This is working as intended.

**Documentation needed:** The post-score role fit filter is a manual step and should be documented as such. When a company passes company-level scoring but the open role fails the build mandate check, the company stays on Monitor and the role evaluation is noted in the Airtable record. This prevents the company from being passed entirely when a future VP/Head CS opening might appear.

**Status:** [ ] Document as standard operating procedure in pipeline README

---

### Batch 3 Summary

These 8 patterns represent the gap between "company matches keywords" and "company is actually a fit." Patterns 3.1-3.6 are pre-scoring gate failures (things that should be caught before scoring runs). Pattern 3.7 is an execution order question. Pattern 3.8 is a process documentation gap, not a scoring bug.

**Priority order for implementation:**
1. 3.1 (PE blocklist) and 3.7 (persona gate ordering) are quick wins
2. 3.2 (non-SaaS) and 3.3 (B2C) require new classification logic
3. 3.4 (grant-funded) and 3.5 (stale funding) are enrichment-phase additions
4. 3.6 (services hybrids) is hardest to automate, may stay manual
5. 3.8 (role vs. company) is documentation only

*Batch 3 analysis documented: Mar 11 2026*

---

# Batch 4 Analysis — March 15, 2026 (0% Signal Rate)

## Summary

| Metric | Value |
|--------|-------|
| Total evaluated | 50 |
| Auto-Disqualified | 48 |
| Already tracked | 2 (Assort Health, Subscript) |
| Passed (no roles) | 1 (Axuall) |
| **Actionable targets** | **0** |
| **Signal rate** | **0%** |

This batch represents a complete filter failure. Root causes below.

---

## Disqualification Breakdown

### Over Employee Cap (150+) — 11 companies (22%)
| Company | Employees | Funding | Notes |
|---------|-----------|---------|-------|
| Auditboard | 999 | $506M | PE-backed (Hg), acquired for $3B |
| Pipedrive | 800+ | $99M | PE-backed (Vista Equity) |
| Brightside Health | 464 | $114M | Series C |
| Elation Health | 242 | $108M | Over both caps |
| Virtru | 206 | $191M | Over both caps |
| CertifyOS | 194 | $70M | Over employee cap |
| Verato | 184 | $35M | Over employee cap |
| Litify | 174+ | $78M+ | Acquired by Bessemer |
| Sentra | 173 | $103M | Over both caps |
| Fieldguide | 168 | $125M | Over both caps |
| evolvedMD | 101-250 | $53M | Also services model |

### Wrong Business Model (not B2B SaaS) — 16 companies (32%)
| Company | Actual Model |
|---------|-------------|
| Chamber Cardio | Value-based care delivery (payer contracts) |
| YourPath | Clinical substance use disorder services |
| SimpliFed | Telehealth care delivery |
| Flowneuroscience | Medical device (brain stimulation) |
| Everyonemedicines | Biotech/pharma |
| Counsel Health | AI virtual care (employs physicians) |
| Daylight Health | Virtual mental health care delivery |
| Eli Health | Consumer hormone monitoring device |
| Insito Health | Care delivery |
| Osana Salud | Latin American health platform (wrong geo + care delivery) |
| Stylusmedicine | Medical/pharma |
| Stratagen Bio | Biotech |
| Live Chair Health | Community health/care delivery |
| Contra | Freelance marketplace |
| Collagerie | Consumer fashion marketplace |
| Pivotal Health | Success-fee IDR services (hybrid) |

### Wrong Sector (B2B SaaS but wrong domain) — 10 companies (20%)
| Company | Sector |
|---------|--------|
| GetAccept | Sales engagement/digital sales rooms |
| Momentum | Sales/call automation |
| Zylo | SaaS management (IT/procurement) |
| Marker Learning | Ed-tech |
| goformz | Mobile forms/field operations |
| neo.tax | Tax automation/fintech |
| VendorPM | Property management |
| Amicus Law | Legal AI |
| Cyrisma | Cybersecurity |
| Manifest Cyber | Cybersecurity SBOM |

### Other Disqualifications
| Category | Companies |
|----------|-----------|
| Developer-as-Customer | Bigeye, Pack |
| PLG / No Enterprise | Creatify AI |
| Too Early (<15 emp) | Develop Health, Daylight Health, Pivotal Health, Eli Health |
| Clinical AI (not SaaS) | Onc.AI, Ellipsis Health |
| Other | roo.vet (veterinary), AristaMD (hybrid), Ethicos, Colla, Healthnote |

---

## Root Cause Analysis

### 1. "Healthcare" is too broad (32% false positives)
The scraper flags anything with "health" in the name. Care delivery, devices, biotech, and consumer health all surface.

**Fix needed:** Healthcare sector refinement
- PASS: "provider-facing SaaS," "health system software," "clinical workflow automation," "EHR integration"
- FAIL: "care delivery," "our physicians," "our clinicians," "telehealth visits," "clinical services"
- FAIL: Medical devices, diagnostics hardware, consumer health devices

### 2. Employee cap not enforced pre-score (22% false positives)
11 companies exceeded 150 employees but still reached manual review.

**Fix needed:** Hard employee cap in enrichment
- >150 employees → auto-DQ before scoring
- <15 employees → flag "Monitor - Too Early"

### 3. No business model gate (32% false positives)
Medical devices, biotech, consumer marketplaces, care delivery all get through.

**Fix needed:** Business model validation
- PASS: "SaaS," "platform," "software," "subscription," "API," "cloud-based"
- FAIL: "our physicians," "patients can access," "care delivery," "clinical services," "medical device," "biotech," "pharmaceutical," "marketplace," "consumer"

### 4. Non-target sectors persist (20% false positives)
Cybersecurity, sales tools, property management, tax automation, ed-tech all surface.

**Fix needed:** Sector keyword exclusions
- Auto-DQ: "veterinary," "biotech," "pharmaceutical," "freelance," "marketplace," "consumer," "fashion," "e-commerce," "tax credit," "property management," "cybersecurity," "SBOM"

---

## Recommended Pipeline Additions

### New Patterns for Parse Enrichment

```javascript
// =============================================
// HEALTHCARE BUSINESS MODEL (care delivery vs SaaS)
// =============================================
const HEALTHCARE_CARE_DELIVERY_PATTERNS = [
  /our (?:physicians|clinicians|doctors|therapists|providers)/i,
  /patients can (?:access|schedule|receive)/i,
  /(?:telehealth|virtual) (?:visits|appointments|care)/i,
  /(?:clinical|medical) services/i,
  /care delivery/i,
  /value-based care/i,
  /(?:mental health|behavioral health) (?:treatment|services)/i,
  /employs? (?:physicians|clinicians|nurses)/i,
  /board-certified (?:physicians|therapists)/i,
  /direct primary care/i,
];

const HEALTHCARE_SAAS_SIGNALS = [
  /(?:provider|hospital|clinic|health system)-facing/i,
  /(?:EHR|EMR) integration/i,
  /clinical workflow (?:automation|software)/i,
  /healthcare (?:operations|analytics) (?:software|platform)/i,
  /(?:revenue cycle|practice management) software/i,
];

// =============================================
// MEDICAL DEVICE / HARDWARE
// =============================================
const MEDICAL_DEVICE_PATTERNS = [
  /medical device/i,
  /(?:FDA|CE) (?:cleared|approved)/i,
  /(?:wearable|diagnostic|monitoring) device/i,
  /(?:brain|neuro) stimulation/i,
  /hormone (?:monitoring|testing) (?:device|kit)/i,
  /(?:sensor|scanner|imager)/i,
  /physical (?:product|device)/i,
];

// =============================================
// EXPANDED SECTOR EXCLUSIONS
// =============================================
const EXCLUDED_SECTOR_PATTERNS = [
  /veterinary|vet tech/i,
  /biotech|pharmaceutical|pharma|drug discovery/i,
  /cybersecurity|cyber security|infosec|SBOM/i,
  /property management|real estate tech/i,
  /tax (?:automation|credit|software)/i,
  /(?:consumer|fashion) marketplace/i,
  /e-commerce marketplace/i,
  /ed-?tech|learning (?:platform|management)/i,
  /sales (?:engagement|enablement|automation)/i,
  /(?:digital sales|deal) room/i,
];

// =============================================
// PLG / NO ENTERPRISE MOTION
// =============================================
const PLG_ONLY_PATTERNS = [
  /self-serve (?:signup|trial|plan)/i,
  /freemium/i,
  /(?:ai|video|image) generator/i,
  /(?:create|generate) (?:videos?|ads?|images?)/i,
  /no.?touch sales/i,
];

const ENTERPRISE_MOTION_SIGNALS = [
  /enterprise (?:sales|team|customers)/i,
  /(?:account executive|sales rep)/i,
  /(?:implementation|onboarding) (?:team|services)/i,
  /customer success (?:team|manager)/i,
  /\$[\d,]+k.?(?:acv|arr|contract)/i,
  /fortune (?:500|1000)/i,
];

// PLG without enterprise = auto-DQ
```

### Updated Gate Logic

```javascript
// NEW: Business Model Gate
const isHealthcareCareDelivery = HEALTHCARE_CARE_DELIVERY_PATTERNS.some(p => p.test(description)) &&
                                  !HEALTHCARE_SAAS_SIGNALS.some(p => p.test(description));

const isMedicalDevice = MEDICAL_DEVICE_PATTERNS.some(p => p.test(description));

const isExcludedSector = EXCLUDED_SECTOR_PATTERNS.some(p => p.test(description));

const isPLGOnly = PLG_ONLY_PATTERNS.some(p => p.test(description)) &&
                  !ENTERPRISE_MOTION_SIGNALS.some(p => p.test(description));

// Add to tier2Disqualify:
const tier2Disqualify =
  is_biotech ||
  is_hardware ||
  is_crypto ||
  is_consumer ||
  is_hrtech ||
  is_marketplace ||
  is_cs_tooling_product ||
  is_carbon_credit_revenue ||
  isHealthcareCareDelivery ||    // NEW
  isMedicalDevice ||              // NEW
  isExcludedSector ||             // NEW
  isPLGOnly;                      // NEW
```

---

## Projected Impact

If all gates had been active, this batch would have reduced from:
- **50 manual evaluations → ~3-5**
- **~2 hours review time → ~15 minutes**
- **100% false positive rate → ~20-30%**

---

## Scoring Model Observation

Companies scoring 68-78 continue to produce near-zero yield:
- Axuall: Score 78, CS Readiness 26 — no open roles, leadership stable, shrinking headcount
- Helios (prior batch): Score 78 — 11 employees, consultancy model, no open roles

**Pattern:** Weighted score over-indexes on company attributes, under-indexes on CS hire readiness.

**Recommended:** If CS Readiness < 15, hard cap total score at 50 (forces Monitor, not Apply).

---

*Batch 4 analysis documented: Mar 15 2026*

**IMPLEMENTATION STATUS: COMPLETE (v9.6)**

Implemented in `Enrich & Evaluate Pipeline v9.6.json`:
- ✅ Healthcare care delivery vs SaaS detection (isHealthcareCareDelivery)
- ✅ Medical device detection (isMedicalDevice)
- ✅ Cybersecurity sector gate (isCybersecurity)
- ✅ Legal Tech sector gate (isLegalTech)
- ✅ Ed-tech sector gate (isEdTech)
- ✅ Property Management / Real Estate Tech gate (isPropertyManagement)
- ✅ Tax automation gate (isTaxTech)
- ✅ Sales tools gate (isSalesTools) - wrong buyer persona
- ✅ Veterinary gate (isVeterinary)

All 9 new sector detections added to isNotB2BSaaS check and TIER 2 disqualification logic.

*Implementation completed: Mar 15 2026*

---

# v9.7 Implementation (Mar 15 2026)

Based on Claude Opus 4.6 recommendations to address remaining false positives.

## New Sector Gates (8 additions)

Implemented in `Enrich & Evaluate Pipeline v9.7.json`:
- ✅ Fintech/Banking (isFintech) - neobank, lending, payment processing, BaaS, core banking
- ✅ Construction Tech (isConstructionTech) - job site, BIM, AEC, contractor management
- ✅ Food Science/CPG (isFoodBiotech) - fermentation, alternative protein, beverage brands
- ✅ Physical Security (isPhysicalSecurity) - access control, surveillance, weapon detection
- ✅ Insurtech (isInsurtech) - policy management, claims processing, underwriting
- ✅ SaaS Management (isSaaSManagement) - IT asset management, shadow IT, software spend
- ✅ Consumer Digital Health (isConsumerDigitalHealth) - patient-facing apps, therapy apps, wellness, DTx
- ✅ AI Calling (isAICalling) - voice agents, robocall, phone bots

## Developer-as-Customer Persona Gate

New persona detection with 15 signal patterns:
- Detects: "for developers", "API-first", "SDK", "DevOps", "CI/CD", "Kubernetes", etc.
- Counter-signals for enterprise dev tools: "enterprise plan", "Fortune 500", "SOC 2", "SSO"
- Gate logic: DQ if developer-customer AND <50 employees AND no enterprise sales motion
- If 50+ employees with enterprise motion, passes gate but gets warning flag

## Evaluation Prompt Score Floor Fix

**Critical change:** Removed false claim that companies passed all gates.

Old prompt said:
> "if company reached this prompt, it passed all gates including CS Hire Readiness >= 10"

New prompt says:
> "automated gates have limited information. You MUST independently verify sector fit and business model. If the company is clearly in the wrong sector... score it below 30 regardless of other factors."

Additional calibration guidance:
- Wrong sector = 0 points in sector scoring
- Wrong sector + no CS hire signal = score 0-20
- Explicit reminder: "do not inflate scores with stage/size points when fundamental sector is wrong"

## Projected Impact

Based on March 15 batch analysis:
- ~16 wrong-business-model companies → caught by broadened care delivery, consumer digital health, food biotech gates
- ~10 wrong-sector companies → caught by fintech, construction, physical security, SaaS management, AI calling gates
- ~2 developer-as-customer companies → caught by persona gate
- Remaining slip-throughs → caught by evaluation score floor (scores 20-35 instead of 72-78)

*Implementation completed: Mar 15 2026*

---

# v9.8 Implementation (Mar 15 2026)

Based on `/Users/zelman/Downloads/v9.8-scoring-fixes.md` spec targeting last high-impact scoring gaps.

## Fix 1: Unicorn Valuation Gate (>$1B)

**Problem:** Modern Treasury ($2B valuation, Series D) slipped through because no valuation gate existed. Employee count was borderline (137-155).

**Solution:**
```javascript
// In Parse Enrichment - gate logic:
if (valuation && valuation >= 1000000000) {
  autoDisqualifiers.push(`Unicorn valuation (>$1B: ${valuationRaw})`);
} else if (valuation && valuation > MAX_VALUATION) {
  autoDisqualifiers.push(`>$450M valuation (${valuationRaw})`);
}
```

**Changes:**
- ✅ Valuation extraction already existed (unicorn keyword + regex patterns)
- ✅ Added unicorn gate as TIER 1 hard gate (>$1B = DQ)
- ✅ Made unicorn and >$450M checks mutually exclusive (unicorn takes priority)
- ✅ Fixed funding cap message: "$500M" → "$450M" to match actual threshold

## Fix 2: Company Age Gate + YC Batch Year Extraction

**Problem:** Zapier (YC S12, founded 2011) scored 82 because YC batch was passed as "Seed" funding stage. 15-year-old companies shouldn't reach scoring.

**Solution:**
```javascript
// In Parse Enrichment - YC batch extraction:
const sourceStage = companyDataItem.stage || companyDataItem.batch ||
                    companyDataItem.funding_stage || companyDataItem.yc_batch ||
                    companyDataItem['YC Batch'] || '';
const batchMatch = sourceStage.match(/\b([SWF])(\d{2})\b/i); // Word boundary, not anchored

if (batchMatch) {
  const twoDigitYear = parseInt(batchMatch[2], 10);
  const candidateYear = 2000 + twoDigitYear;
  // Validate: must be >= 2005 (YC founding) and <= current year
  if (candidateYear >= 2005 && candidateYear <= currentYear) {
    ycBatchYear = candidateYear;
    companyAgeFromBatch = currentYear - ycBatchYear;
  }
}

const companyAge = foundedYear ? (currentYear - foundedYear) : companyAgeFromBatch;

// Age gates:
const isTooOld = companyAge !== null && companyAge > 8;  // >8 years = DQ
const isAgingFlag = companyAge !== null && companyAge > 5 && companyAge <= 8;  // 5-8 years = flag
```

**Changes:**
- ✅ YC batch year extraction from S12/W24/F22 format
- ✅ Word boundary regex (matches "YC S12" not just exact "S12")
- ✅ Checks multiple field names: stage, batch, funding_stage, yc_batch, YC Batch
- ✅ Year validation: >= 2005 (YC founding), <= currentYear
- ✅ Company age calculated from foundedYear OR ycBatchYear
- ✅ >8 years = hard DQ
- ✅ 5-8 years = soft flag (warning)
- ✅ Unknown age = warning flag

**Output fields added:**
- `yc_batch_year` - extracted YC batch year (2012, 2024, etc.)
- `company_age` - years since founding/batch
- `is_too_old` - boolean, >8 years
- `is_aging_flag` - boolean, 5-8 years

## Fix 3: CS Hire Readiness - Evidence Required, No Inference

**Problem:** Summary generator used stage-based reasoning ("Series A = CS hiring likely") as positive signal. Primary driver of ~65% false positive rate in Batch 2. Companies like Mazama Energy got summaries claiming CS hiring need with zero sourced evidence.

**Solution:** Complete CS Readiness prompt overhaul:

```javascript
// Key changes to Build CS Readiness Prompt:

// CRITICAL RULE:
// "Do NOT infer CS hiring need from stage alone."
// "Series A companies often hire CS" is NOT evidence. Do not use it.
// "Enterprise SaaS companies need CS" is NOT evidence. Do not use it.
// "If you cannot point to a specific, sourced fact... the score is 0."

// SCORING TIERS:
// 25 points: No CS function exists + active build signal (all must be true)
// 10 points: CS exists but no leader (IC CSMs with no VP/Head/Director)
// 0 points: CS leadership in place (VP CS, Head of CS, Director of CS)
// 0 points: No evidence found - DEFAULT TO ZERO

// ROLE LANGUAGE DISQUALIFIER:
// NRR, GRR, renewal ownership, expansion quota = subtract 15 pts + manage-and-optimize flag

// OUTPUT:
// - cs_readiness_score (0-25)
// - cs_function_tier (1-3)
// - evidence_found (array)
// - is_manage_and_optimize (boolean)
// - has_role_language_dq (boolean)
```

**Changes:**
- ✅ Prompt explicitly requires EVIDENCE, not inference
- ✅ Default to 0 if no sourced signals found
- ✅ Stage alone is NOT evidence (explicit prohibition)
- ✅ Role language check: NRR/GRR/renewal = subtract 15 pts
- ✅ Added company_age to user prompt for context
- ✅ "False negatives acceptable, false positives not" guidance

## Opus 4.6 Review Findings (Post-Implementation)

Code review via `code-review.mjs --model opus` caught additional issues:

1. **Fixed:** YC batch extraction was reading from undefined `companyData` fields → now reads from `companyDataItem`
2. **Fixed:** Unicorn and >$450M checks both fired for unicorns → now mutually exclusive
3. **Fixed:** Funding cap message said "$500M" but threshold was $450M → corrected
4. **Fixed:** Regex used anchors `^[SWF](\d{2})$` → changed to word boundaries `\b([SWF])(\d{2})\b`
5. **Fixed:** Fellowship batch (F prefix) not supported → added to regex
6. **Fixed:** No warning for unknown company age → added warning flag
7. **Fixed:** Unescaped quotes in comment broke JSON → escaped properly

## Testing Plan

Companies that should now DQ:

| Company | Root Cause | v9.8 Gate | Expected |
|---------|------------|-----------|----------|
| Modern Treasury | $2B valuation | Unicorn gate | DQ |
| Zapier | YC S12, 15 years old | Age gate | DQ |
| Mighty Networks | Founded 2010, 16 years | Age gate | DQ |
| Helcim | Founded 2006, 20 years | Age gate | DQ |
| InternMatch | Founded 2009, 17 years | Age gate | DQ |
| VoltServer | Founded 2011, 15 years | Age gate | DQ |
| Mazama Energy | Fabricated CS signal | CS readiness = 0 | Low score |
| Ebb Carbon | Fabricated CS signal | CS readiness = 0 | Low score |

Genuine candidates should still pass:
- Paxton.ai (24 employees, legal AI SaaS, no CS function)
- Assort Health (healthcare SaaS, provider-facing)
- Subscript (if enrichment finds build signals)

*Implementation completed: Mar 15 2026*

---

# Job Evaluation Pipeline v6.4 (Mar 15 2026)

Code review via `code-review.mjs --model sonnet` found 2 critical issues:

## Fix 1: Regex Backtracking Prevention

**Problem:** Patterns with `([\s\S]*?)` inside complex lookaheads could hang on long HTML strings.

**Solution:**
```javascript
// In Parse Job Description:
const MAX_HTML_LENGTH = 50000;
if (htmlStr.length > MAX_HTML_LENGTH) {
  console.error(`Warning: HTML truncated from ${htmlStr.length} to ${MAX_HTML_LENGTH} chars`);
  htmlStr = htmlStr.substring(0, MAX_HTML_LENGTH);
}
```

## Fix 2: Silent Error Logging

**Problem:** Try-catch blocks failed to empty objects without logging, masking real errors.

**Solution:**
```javascript
// Added console.error() to all try-catch blocks:
try {
  braveData = $('Brave Search Company').item?.json || {};
} catch(e) {
  console.error('Parse JD: Failed to get Brave data:', e.message);
  braveData = {};
}
```

**Changes:**
- ✅ HTML truncation before regex matching (50K char limit)
- ✅ console.error() added to 8 try-catch blocks
- ✅ Descriptive error context in all log messages

*Implementation completed: Mar 15 2026*

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

---

# v9.9 / v6.6 / v4.6 Implementation — Batch 4 Scoring Fixes (Mar 16 2026)

Based on `/Users/zelman/Desktop/Quarantine/SCORING-ENHANCEMENTS-BATCH4-APPEND.md` spec targeting two specific failure patterns:

- **Browserbase** (False Negative): Scored 10, should be 78. Employee count read as 10 (stray integer) instead of ~50. Series B, $67.5M raised.
- **Fullview.io** (False Positive): Scored 82, should be Pass. CX vendor with 4-year-old stale funding, no CS hire signals.

## Fix 4.1: Employee Count Cross-Reference

**Problem:** Employee count used as standalone gate without funding cross-reference. Browserbase auto-DQ'd due to bad data.

**Solution:** Employee count corroboration using median of multiple mentions:

```javascript
// v9.9: Employee count corroboration (Batch 4 Fix 4.1)
const empMatches = [...allText.matchAll(/(\d[\d,]*)\s*(?:to\s*\d[\d,]*)?\s*employees?/gi)];
const empCounts = empMatches.map(m => parseInt(m[1].replace(/,/g, ''))).filter(n => n > 0 && n < 100000);

const median = (arr) => {
  if (arr.length === 0) return null;
  const sorted = [...arr].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 !== 0 ? sorted[mid] : Math.round((sorted[mid - 1] + sorted[mid]) / 2);
};

let employeeCount = empCounts.length > 0 ? (empCounts.length > 1 ? median(empCounts) : empCounts[0]) : null;

// Also extract ranges: "10-50 employees" → take upper bound
const rangeMatch = allText.match(/(\d+)\s*(?:to|-)\s*(\d+)\s*employees?/i);
if (rangeMatch) employeeCount = parseInt(rangeMatch[2]);

// Cross-reference against funding
let suspiciousEmployeeCount = false;
let employeeCountFlag = null;
const fundingStageRank = {
  'Pre-Seed': 1, 'Seed': 2, 'Series A': 3, 'Series B': 4,
  'Series C': 5, 'Series D': 6, 'Series E': 7, 'Series F+': 8
};
const isSeriesAPlus = fundingStage && fundingStageRank[fundingStage] >= 3;
const hasSignificantFunding = totalFunding && totalFunding >= 10000000;

if (employeeCount && employeeCount < 15) {
  if (isSeriesAPlus || hasSignificantFunding) {
    suspiciousEmployeeCount = true;
    employeeCountFlag = `Employee count ${employeeCount} seems low for ${fundingStage || 'this funding level'}`;
  }
}
```

**Output fields:**
- `suspiciousEmployeeCount` (boolean) - flag for manual review
- `employeeCountFlag` (string) - explanation

**Status:** ✅ Implemented in v9.9, v6.6, v4.6

---

## Fix 4.2: Funding Recency Signal

**Problem:** Fullview.io has $9.3M seed from May 2022 (4 years ago), no penalty for stale funding.

**Solution:** Graduated funding staleness penalties:

```javascript
// v9.9: Funding recency extraction (Batch 4 Fix 4.2)
let yearsSinceLastRound = null;
let fundingRecency = null;

// Extract funding date patterns
const datePatterns = [
  /(?:raised|funding|round|series [a-e])[^.]*?(?:in\s+)?(\d{4})/gi,
  /(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})/gi,
  /(\d{4})[^.]*?(?:raised|funding|round|series)/gi
];

const years = [];
for (const pattern of datePatterns) {
  const matches = [...allText.matchAll(pattern)];
  for (const m of matches) {
    const y = parseInt(m[1]);
    if (y >= 2010 && y <= currentYear) years.push(y);
  }
}

if (years.length > 0) {
  const lastFundingYear = Math.max(...years);
  yearsSinceLastRound = currentYear - lastFundingYear;

  if (yearsSinceLastRound < 1) fundingRecency = 'recent';
  else if (yearsSinceLastRound < 2) fundingRecency = 'moderate';
  else if (yearsSinceLastRound < 3) fundingRecency = 'aging';
  else fundingRecency = 'stale';
}

// Graduated staleness modifier (Opus review improvement)
let fundingStalenessModifier = 0;
const isEarlyStage = ['Seed', 'Series A', 'Pre-Seed'].includes(fundingStage);
if (yearsSinceLastRound && isEarlyStage && employeeCount < 100) {
  if (yearsSinceLastRound >= 4) fundingStalenessModifier = -15;
  else if (yearsSinceLastRound >= 3) fundingStalenessModifier = -10;
  else if (yearsSinceLastRound >= 2) fundingStalenessModifier = -5;
}
```

**Output fields:**
- `yearsSinceLastRound` (number) - decimal years
- `fundingRecency` (single select) - recent/moderate/aging/stale
- `fundingStalenessModifier` (number) - -5/-10/-15 penalty

**Status:** ✅ Implemented in v9.9, v6.6, v4.6

---

## Fix 4.3: CS Hire Readiness Score Capping

**Problem:** Fullview scored 82 despite zero CS hire signals. Sector/VC keywords inflated score without CS readiness providing counterweight.

**Original spec:** Cap at 50 if CS hire likelihood is "unlikely"

**Opus review improvement:** Graduated caps to allow "unlikely" companies to reach Monitor tier if other factors strong:

| CS Hire Likelihood | Score Cap |
|-------------------|-----------|
| `unlikely` | 65 (can reach Monitor, not Apply) |
| `low` | 75 |
| `medium`/`high` | No cap |

**Solution:**

```javascript
// v9.9: CS Hire Readiness score capping (Batch 4 Fix 4.3)
let finalScore = evaluation.score || 0;
let originalScore = finalScore;
let scoreCapped = false;
let scoreCapReason = null;

const csHireLikelihood = (evaluation.cs_hire_likelihood || '').toLowerCase();

// Graduated caps (Opus review improvement - less aggressive than original 50 cap)
if (csHireLikelihood === 'unlikely') {
  if (finalScore > 65) {
    scoreCapped = true;
    scoreCapReason = `Score capped from ${finalScore} to 65: CS hire likelihood is "unlikely"`;
    finalScore = 65;
  }
} else if (csHireLikelihood === 'low') {
  if (finalScore > 75) {
    scoreCapped = true;
    scoreCapReason = `Score capped from ${finalScore} to 75: CS hire likelihood is "low"`;
    finalScore = 75;
  }
}

// Additional cap for self-serve products without ops gap
if (evaluation.product_type === 'self-serve' && !evaluation.ops_gap) {
  if (finalScore > 60) {
    scoreCapped = true;
    scoreCapReason = `Score capped from ${finalScore} to 60: Self-serve product without ops gap`;
    finalScore = 60;
  }
}
```

**Output fields:**
- `originalScore` (number) - pre-cap score
- `scoreCapped` (boolean) - was score capped
- `scoreCapReason` (string) - explanation

**Status:** ✅ Implemented in v9.9, v6.6, v4.6

---

## Fix 4.4: CX Tooling Company Detection

**Problem:** Fullview.io sells customer support software (cobrowsing, session replays). Got full sector points for CX/support keywords. But they sell TO CS teams, they don't need to BUILD a CS team.

**Solution:** Detect CX tooling vendors and exclude from sector bonus:

```javascript
// v9.9: CX Tooling Keywords (Batch 4 Fix 4.4)
const CX_TOOLING_KEYWORDS = [
  'cobrowsing', 'session replay', 'helpdesk', 'ticketing',
  'chatbot', 'customer support software', 'live chat',
  'contact center', 'support automation', 'knowledge base software',
  'customer service platform', 'help desk software', 'support ticketing'
];

let isCXToolingCompany = false;
let cxToolingSignals = [];

for (const keyword of CX_TOOLING_KEYWORDS) {
  if (allText.toLowerCase().includes(keyword)) {
    cxToolingSignals.push(keyword);
  }
}

isCXToolingCompany = cxToolingSignals.length >= 2;

// Add context to LLM prompt
const cxToolingContext = isCXToolingCompany ?
  `\nCX TOOLING COMPANY: YES - This company SELLS customer support software (${cxToolingSignals.join(', ')}). ` +
  `They sell TO CS teams, they do NOT need CS leadership. Do NOT give sector bonus. ` +
  `CS Hire Likelihood should be "unlikely" unless explicit contrary evidence found.\n` : '';
```

**Output fields:**
- `isCXToolingCompany` (boolean) - is CX vendor
- `cxToolingSignals` (array) - which keywords matched

**LLM prompt guidance:**
```
CX TOOLING COMPANY DISTINCTION:
- Companies that SELL CX software should NOT receive sector match points
- These companies sell TO support teams, they don't BUILD large CS orgs
- If isCXToolingCompany = true: set domain_fit/sector bonus to 0
```

**Status:** ✅ Implemented in v9.9, v6.6, v4.6

---

## New Airtable Fields (Batch 4)

| Field | Type | Description |
|-------|------|-------------|
| `Funding Recency` | Single select | recent/moderate/aging/stale |
| `Years Since Last Round` | Number | Decimal years |
| `Suspicious Employee Count` | Checkbox | Flag for manual review |
| `Employee Count Flag` | Long text | Explanation of concern |
| `Is CX Tooling Company` | Checkbox | Sells to CS teams |
| `CX Tooling Signals` | Long text | Detection keywords |
| `Original Score` | Number | Pre-cap score |
| `Score Capped` | Checkbox | Was score capped |
| `Score Cap Reason` | Long text | Why capped |

---

## Verification Results

After implementation:

| Company | Before | After | Reason |
|---------|--------|-------|--------|
| **Browserbase** | Score 10 (auto-DQ) | Flagged for review | Suspicious employee count detected |
| **Fullview.io** | Score 82 (Apply) | Score ~50-65 (Monitor/Pass) | CX vendor + stale funding + CS cap |

---

## Files Updated

| Workflow | Old Version | New Version |
|----------|-------------|-------------|
| Enrich & Evaluate Pipeline | v9.8 | **v9.9** |
| Job Evaluation Pipeline | v6.5 | **v6.6** |
| Funding Alerts Rescore | v4.5 | **v4.6** |

*Implementation completed: Mar 16 2026*
