# Tide Pool Scoring Architecture

## Overview

The Tide Pool scoring system uses a **six-phase architecture** that splits responsibilities between entity validation, deterministic code gates, LLM-based classification, CS hire readiness threshold, and LLM-based evaluation with domain distance modifiers. This design optimizes for cost, speed, reliability, and maintainability.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SCORING ARCHITECTURE (v9)                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ PHASE 0: ENTITY VALIDATION (Code node)                               │   │
│  │                                                                       │   │
│  │ • Catches non-companies before enrichment                            │   │
│  │ • Detects: podcasts, media, nonprofits, university labs             │   │
│  │ • Invalid entities exit immediately (no API calls)                   │   │
│  │                                                                       │   │
│  │ Implements:                                                           │   │
│  │ - Invalid entity patterns (.org, .edu, podcast, blog, newsletter)   │   │
│  │ - Valid company signals (inc., llc, raised, series, employees)      │   │
│  │ - Fail → Exit: "Invalid Entity"                                      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ PHASE 1: ENRICHMENT (Brave Search)                                   │   │
│  │                                                                       │   │
│  │ • Fetch company data via Brave Search API                            │   │
│  │ • Enhanced acquisition detection (PE portfolio patterns)            │   │
│  │ • GTM motion extraction (PLG vs enterprise signals)                 │   │
│  │ • Software-first check (not services/hardware)                       │   │
│  │ • Stale company detection (shrinking headcount)                      │   │
│  │ • Geography detection (US vs non-US)                                 │   │
│  │                                                                       │   │
│  │ Outputs:                                                              │   │
│  │ - Employee count, funding, stage, valuation                          │   │
│  │ - Acquisition status, current ownership                              │   │
│  │ - GTM motion (PLG-dominant, enterprise, hybrid)                      │   │
│  │ - Software-first flag, pre-sales function flag                       │   │
│  │ - Stale company signals, geography flags                             │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ PHASE 2: PRE-EVALUATION GATES (Parse Enrichment - 5 Tiers)          │   │
│  │                                                                       │   │
│  │ TIER 1 - HARD GATES (binary, immediate exit):                        │   │
│  │   • PE-backed, >200 emp, >$500M funding, public, Series D+          │   │
│  │   • Acquired/merged, Fortune 500, invalid entity, non-US market     │   │
│  │                                                                       │   │
│  │ TIER 2 - SECTOR GATES (also hard DQ):                                │   │
│  │   • Biotech, hardware, crypto, consumer, HR Tech                     │   │
│  │   • Not software-first (services business, hardware+software)       │   │
│  │                                                                       │   │
│  │ TIER 3 - GTM MOTION GATES:                                           │   │
│  │   • PLG-dominant (no enterprise CS need)                             │   │
│  │   • Pre-sales function company                                       │   │
│  │                                                                       │   │
│  │ TIER 4 - STALE COMPANY GATES:                                        │   │
│  │   • 3+ years since funding (no recent growth)                        │   │
│  │   • Shrinking headcount signals                                      │   │
│  │                                                                       │   │
│  │ TIER 5 - SOFT FLAGS (proceed but flag):                              │   │
│  │   • <15 employees (too early)                                        │   │
│  │   • 150-200 employees (penalty zone)                                 │   │
│  │   • $75M-$500M funding (soft cap)                                    │   │
│  │   • Founded pre-2016 (age warning)                                   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                    ┌───────────────┴───────────────┐                        │
│                    ▼                               ▼                        │
│           ┌──────────────┐                ┌──────────────┐                  │
│           │ DISQUALIFIED │                │   PHASE 3:   │                  │
│           │  Score = 0   │                │   PERSONA    │                  │
│           │  No API call │                │ CLASSIFICATION│                  │
│           └──────────────┘                └──────┬───────┘                  │
│                                                  │                          │
│                                                  ▼                          │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ PHASE 3: CUSTOMER PERSONA CLASSIFICATION (Claude Haiku)             │   │
│  │                                                                       │   │
│  │ • Identifies customer type for CS motion fit                         │   │
│  │ • Four personas: business-user, employee-user, developer, mixed     │   │
│  │                                                                       │   │
│  │ Classification:                                                       │   │
│  │ - business-user: Non-technical (sales, HR, finance, healthcare)     │   │
│  │ - employee-user: B2B2C patterns (Oshi Health, Koa Health)           │   │
│  │ - developer: Technical practitioners (devs, SRE, data engineers)    │   │
│  │ - mixed: Both personas are primary users                             │   │
│  │                                                                       │   │
│  │ Auto-pass logic:                                                      │   │
│  │ - Developer + <50 emp → Auto-pass                                    │   │
│  │ - Developer + 50+ emp + <3 enterprise signals → Auto-pass           │   │
│  │ - Developer + 50+ emp + 3+ enterprise signals → Proceed             │   │
│  │ - Employee-user + <50 emp → Auto-pass                                │   │
│  │ - Business-user or mixed → Proceed to CS Readiness                  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                    ┌───────────────┴───────────────┐                        │
│                    ▼                               ▼                        │
│           ┌──────────────┐                ┌──────────────┐                  │
│           │  AUTO-PASS   │                │   PHASE 4:   │                  │
│           │  (dev/emp)   │                │ CS READINESS │                  │
│           │  Score = 0   │                │  THRESHOLD   │                  │
│           └──────────────┘                └──────┬───────┘                  │
│                                                  │                          │
│                                                  ▼                          │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ PHASE 4: CS HIRE READINESS THRESHOLD (Claude Haiku)                 │   │
│  │                                                                       │   │
│  │ • Quick Claude call: "Is this company actively building CS?"         │   │
│  │ • Scores 0-30 on CS hire readiness                                   │   │
│  │ • Must score >= 10 to proceed to full evaluation                     │   │
│  │                                                                       │   │
│  │ Evaluation criteria:                                                  │   │
│  │ - Does company have paying customers?                                │   │
│  │ - Is there a post-sales CS motion?                                   │   │
│  │ - Are they likely hiring for CS leadership?                          │   │
│  │                                                                       │   │
│  │ Scoring bands:                                                        │   │
│  │ - 25-30: Clear CS leadership hiring need                             │   │
│  │ - 15-24: Probable CS need, timing may vary                           │   │
│  │ - 10-14: Possible but uncertain                                      │   │
│  │ - 0-9: No clear CS need → Exit: "CS Hire Readiness Below Threshold" │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                    ┌───────────────┴───────────────┐                        │
│                    ▼                               ▼                        │
│           ┌──────────────┐                ┌──────────────┐                  │
│           │  BELOW       │                │   PHASE 5:   │                  │
│           │  THRESHOLD   │                │    FULL      │                  │
│           │  Score = 0   │                │  EVALUATION  │                  │
│           └──────────────┘                └──────┬───────┘                  │
│                                                  │                          │
│                                                  ▼                          │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ PHASE 5: FULL EVALUATION (Claude Haiku)                              │   │
│  │                                                                       │   │
│  │ • 100-point weighted model across 5 categories                       │   │
│  │ • Domain distance modifier applied after base scoring                │   │
│  │ • APPLY/WATCH/PASS bucketing                                         │   │
│  │                                                                       │   │
│  │ Base Scoring Categories:                                              │   │
│  │ - CS Hire Readiness (25 pts) - Does company need this hire NOW?     │   │
│  │ - Stage & Size Fit (25 pts) - Right inflection point?               │   │
│  │ - Role Mandate (20 pts) - Builder vs Maintainer?                    │   │
│  │ - Sector & Mission (15 pts) - Alignment with experience?            │   │
│  │ - Outreach Feasibility (15 pts) - Network access?                   │   │
│  │                                                                       │   │
│  │ Domain Distance Modifier (-10 to +5):                                │   │
│  │ - Target domains: Healthcare B2B (+5), Clinical Ops (+5)            │   │
│  │ - High-distance: Physical Security (-10), ITSM (-8), Retail POS (-8)│   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Why Six Phases?

### The Problem with "Just Use the MD File"

If we sent every company directly to Claude with the Agent Lens for evaluation:

| Metric | Claude-Only Approach | Six-Phase Approach |
|--------|---------------------|---------------------|
| **Cost** | ~$0.003/company × 500/week = **$78/month** | ~$0.003 × 50 fully evaluated = **$8/month** |
| **Speed** | 3-5 sec per company | <100ms for code gates, 0.5s persona, 0.5s CS check, 3-5s only for qualified |
| **Reliability** | LLM may miss obvious disqualifiers | Code-based gates are deterministic |
| **Rate Limits** | Risk of API throttling at volume | 90% fewer full evaluation API calls |

### Why Add Entity Validation (Phase 0)?

The v9 redesign revealed that non-companies (podcasts, university labs, nonprofits) were slipping through enrichment and wasting API calls. Phase 0 catches these immediately with simple pattern matching.

### Why Add CS Hire Readiness Threshold (Phase 4)?

The 4% signal rate in v8.5 was largely due to timing mismatches - companies that might need CS eventually but aren't actively building that function now. Phase 4 uses a quick Claude call to confirm active CS hiring need before the expensive full evaluation.

### Why Not Just Code Everything?

Pure code-based scoring fails at nuanced judgment:

- **"Does this company need a CS hire NOW?"** - Requires reading between the lines of company descriptions, inferring from funding timing, team size signals
- **"Is this a builder or maintainer role?"** - Requires understanding role mandates from limited context
- **"How strong is the sector alignment?"** - Healthcare B2B SaaS covers a spectrum from "perfect fit" to "adjacent"
- **"What's the domain distance penalty?"** - Requires understanding what the company actually does

Code can check `employee_count > 200`. Code cannot determine "this Series A company's description suggests they're still founder-led on customer relationships."

---

## Phase Details

### Phase 0: Entity Validation

**Location:** `Enrich & Evaluate Pipeline v9.json` → "Validate Entity" node

**Purpose:** Catch non-companies before enrichment wastes API calls.

**Patterns detected:**

```javascript
// Invalid entity signals
INVALID_ENTITY_SIGNALS = [
  /podcast/i, /blog/i, /newsletter/i, /media/i,
  /student.*team/i, /university.*lab/i, /research.*group/i,
  /nonprofit/i, /foundation/i, /\.org$/i,
  /association/i, /coalition/i, /consortium/i,
  /\.edu$/i, /\.gov$/i
]

// Valid company signals (override invalid if present)
VALID_COMPANY_SIGNALS = [
  /inc\./i, /llc/i, /corp/i, /ltd/i,
  /founded/i, /raised/i, /series [a-d]/i,
  /employees/i, /hiring/i, /careers/i,
  /product/i, /platform/i, /saas/i
]
```

**Output:** `isValidEntity` boolean, `entityValidationReason` string

---

### Phase 1: Enhanced Enrichment

**Location:** `Enrich & Evaluate Pipeline v9.json` → "Brave Search" + "Parse Enrichment" nodes

**Purpose:** Comprehensive data extraction with new v9 detection patterns.

**New in v9:**

| Detection | Implementation | Why Added |
|-----------|----------------|-----------|
| PE Portfolio Patterns | Match against Jonas Software, Constellation, Volaris, etc. | PE-owned companies slip through |
| Current Ownership | "currently owned by", "majority stake" patterns | Distinguish from investor history |
| GTM Motion | PLG signals (free tier, self-serve, freemium) vs enterprise signals | PLG companies don't need enterprise CS |
| Software-First | Detect services businesses, hardware-with-software | "SaaS" in name doesn't mean software-first |
| Pre-Sales Function | presales platform, demo automation, CPQ signals | Pre-sales tools don't need post-sales CS |
| Stale Company | Layoff keywords, restructuring, contraction signals | 3+ years since funding with no growth |
| Geography | US vs non-US HQ detection | Non-US primary market filter |

---

### Phase 2: Pre-Evaluation Gates (5 Tiers)

**Location:** `Enrich & Evaluate Pipeline v9.json` → "IF: Auto-Disqualify" node

**Tier Structure:**

```javascript
// TIER 1: HARD GATES (Exit immediately)
const tier1Disqualify =
  is_acquired ||
  pe_backed ||
  is_public ||
  is_fortune500 ||
  employee_count > 200 ||
  total_funding_numeric > 500000000 ||
  /series d|series e|growth/i.test(funding_stage) ||
  !isValidEntity ||
  geography.isNonUSBased;

// TIER 2: SECTOR GATES
const tier2Disqualify =
  is_biotech ||
  is_hardware ||
  is_crypto ||
  is_consumer ||
  is_hrtech ||
  is_marketplace ||
  !isSoftwareFirst;

// TIER 3: GTM MOTION GATES
const tier3Disqualify =
  gtmMotion.isPLGDominant ||
  isPresalesCompany;

// TIER 4: STALE COMPANY GATE
const tier4Disqualify =
  (fundingAgeYears >= 3 && !hasRecentGrowthSignals) ||
  hasShrinkingSignals;

// TIER 5: SOFT FLAGS (proceed but flag)
// <15 employees, 150-200 employees, $75M+ funding, pre-2016
```

---

### Phase 3: Customer Persona Classification

**Location:** `Enrich & Evaluate Pipeline v9.json` → "Classify Persona via Claude" node

**Purpose:** Identify customer type for CS motion fit.

**Four personas (v9):**

| Persona | Description | CS Motion Fit |
|---------|-------------|---------------|
| business-user | Non-technical end users (sales, HR, finance, healthcare providers) | Primary target |
| employee-user | B2B2C patterns (Oshi Health, Koa Health) | Secondary target |
| developer | Technical practitioners (devs, SRE, data engineers) | Auto-pass unless enterprise |
| mixed | Both personas equally important | Evaluate case-by-case |

**Enterprise exception (stricter in v9):**
- 50+ employees, AND
- 3+ enterprise signals (was 2+ in v8.4)

---

### Phase 4: CS Hire Readiness Threshold

**Location:** `Enrich & Evaluate Pipeline v9.json` → "Check CS Readiness" node

**Purpose:** Confirm company is actively building post-sales CS function before expensive full evaluation.

**Threshold:** Score >= 10 to proceed (was 15, lowered after testing)

**Scoring bands:**
- 25-30: Clear CS leadership hiring need (recent funding, no CS team, product launched)
- 15-24: Probable CS need, timing may vary
- 10-14: Possible but uncertain (proceed to full evaluation)
- 0-9: No clear CS need → Exit pipeline

---

### Phase 5: Full Evaluation with Domain Distance

**Location:** `Enrich & Evaluate Pipeline v9.json` → "Build Evaluation Prompt" + "Claude Evaluate" nodes

**100-Point Base Scoring:**

| Category | Points | What It Measures |
|----------|--------|------------------|
| CS Hire Readiness | 0-25 | Does company need this hire NOW? |
| Stage & Size Fit | 0-25 | Right inflection point for builder role? |
| Role Mandate | 0-20 | Builder (0-to-1) vs Maintainer (scale existing)? |
| Sector & Mission | 0-15 | Alignment with healthcare/B2B SaaS experience? |
| Outreach Feasibility | 0-15 | Network access, warm intro potential? |

**Domain Distance Modifier (New in v9):**

| Domain | Modifier | Rationale |
|--------|----------|-----------|
| Healthcare B2B SaaS | +5 | Target domain, direct experience |
| Clinical Operations | +5 | Target domain |
| Care Coordination | +4 | Adjacent target |
| Patient Engagement | +3 | B2B2C, adjacent |
| Developer Tools | +2 | Experience with technical users |
| General Enterprise SaaS | 0 | Neutral |
| Financial Compliance/RegTech | -6 | High distance |
| Legal Tech | -6 | High distance |
| Real Estate Tech | -7 | High distance |
| Construction Tech | -7 | High distance |
| Vertical Retail POS | -8 | High distance |
| IT Operations/ITSM | -8 | High distance |
| Physical Security | -10 | Highest distance |

**Bucketing:**
- 60+: **APPLY** - Worth pursuing
- 40-59: **WATCH** - Monitor for changes
- <40: **PASS** - Not a fit

---

## Data Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ VC Scraper  │────▶│  Validate   │────▶│ Brave Search│────▶│   Parse     │
│ (source)    │     │  Entity     │     │ (enrich)    │     │ Enrichment  │
└─────────────┘     └──────┬──────┘     └─────────────┘     └──────┬──────┘
                           │                                        │
                           │ Invalid                    ┌───────────┴───────────┐
                           ▼                            │                       │
                    ┌─────────────┐                     ▼                       ▼
                    │ Exit:       │              ┌─────────────┐         ┌─────────────┐
                    │ Invalid     │              │ Disqualified│         │  Classify   │
                    │ Entity      │              │ (Tier 1-4)  │         │  Persona    │
                    └─────────────┘              └─────────────┘         └──────┬──────┘
                                                                                │
                                                   ┌────────────────────────────┴──────┐
                                                   │                                   │
                                                   ▼                                   ▼
                                            ┌─────────────┐                     ┌─────────────┐
                                            │ Auto-Pass   │                     │ Check CS    │
                                            │ (dev/emp)   │                     │ Readiness   │
                                            └─────────────┘                     └──────┬──────┘
                                                                                       │
                                                          ┌────────────────────────────┴──────┐
                                                          │                                   │
                                                          ▼                                   ▼
                                                   ┌─────────────┐                     ┌─────────────┐
                                                   │ Exit:       │                     │ Full        │
                                                   │ Below       │                     │ Evaluation  │
                                                   │ Threshold   │                     │ + Domain    │
                                                   └─────────────┘                     │ Distance    │
                                                                                       └──────┬──────┘
                                                                                              │
                                                                                              ▼
                                                                                       ┌─────────────┐
                                                                                       │ APPLY/WATCH │
                                                                                       │ /PASS       │
                                                                                       │ → Airtable  │
                                                                                       └─────────────┘
```

---

## Disqualification Reasons (v9)

### Tier 1-4 Auto-DQ Reasons

```javascript
const V9_DQ_REASONS = [
  // Tier 1 - Hard Gates
  'Acquired/merged company',
  'PE-backed (firm name)',
  'Public company',
  'Fortune 500 subsidiary',
  '>200 employees',
  '>$500M funding',
  'Series D+ stage',
  'Invalid entity (media/podcast/nonprofit)',
  'Non-US primary market',

  // Tier 2 - Sector Gates
  'Biotech/pharma',
  'Hardware/physical product',
  'Crypto/Web3',
  'Consumer/B2C',
  'HR Tech/DEI',
  'Marketplace',
  'Not software-first (services business)',
  'Not software-first (hardware with software)',

  // Tier 3 - GTM Motion Gates
  'PLG-dominant (no enterprise CS need)',
  'Pre-sales function company',

  // Tier 4 - Stale Company Gates
  'Stale company (3+ years since funding)',
  'Shrinking headcount signals',

  // Phase 4 - CS Readiness
  'CS Hire Readiness below threshold'
];
```

---

## Maintenance Model

| Change Type | Where to Update | Deployment |
|-------------|-----------------|------------|
| Add new PE firm | Parse Enrichment (peFirms array) | Re-import workflow |
| Change employee threshold | Parse Enrichment (constants) | Re-import workflow |
| Add sector exclusion | Parse Enrichment (regex patterns) | Re-import workflow |
| Adjust scoring weights | Build Evaluation Prompt (systemPrompt) | Re-import workflow |
| Change CS readiness threshold | Parse CS Readiness (CS_READINESS_THRESHOLD) | Re-import workflow |
| Add domain distance modifier | Build Evaluation Prompt (systemPrompt) | Re-import workflow |
| Add GTM motion pattern | Parse Enrichment (PLG_SIGNALS, ENTERPRISE_SIGNALS) | Re-import workflow |
| Change enterprise exception threshold | Parse Persona (signal count) | Re-import workflow |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v9 | 2026-03-11 | **FULL REDESIGN**: Phase 0 Entity Validation, enhanced acquisition detection, GTM motion gates (PLG/pre-sales), stale company gates, CS Hire Readiness threshold (>=10), domain distance scoring, employee-user persona, stricter enterprise exception (3+ signals) |
| v8.5 | 2026-03-09 | 8 scoring fixes: employee-user persona, stricter SaaS gate, geography gate, stricter developer persona, age gate, stale funding penalty |
| v8.4 | 2026-03-06 | Customer Persona Gate - classifies business-user vs developer-as-customer |
| v8.3 | 2026-03-06 | Two-tier architecture, Fortune 500 detection, employee 200 cap |
| v8 | 2026-02 | 100-point model, 5-category scoring, public company gates |

---

## FigJam Diagrams

Interactive diagrams for visual reference:

- **[v9 Pipeline Gate Flow](https://www.figma.com/online-whiteboard/create-diagram/6d2f6511-9e89-4635-8585-238feae95221)** - 5-phase architecture with decision points
- **[v9 Scoring Architecture](https://www.figma.com/online-whiteboard/create-diagram/d16d9d48-12af-4d27-9fa1-99566ea42a1d)** - 100-point scoring breakdown with domain distance modifiers

---

*Last updated: March 2026*
