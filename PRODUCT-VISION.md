# Tide Pool: Product Vision & Architecture

> A personalized company discovery system for job seekers, with user-adjustable scoring lenses.

## Executive Summary

Tide Pool helps job seekers find companies that match their career goals by aggregating funding alerts, job postings, and VC portfolio data, then scoring each opportunity through a personalized lens. The core innovation is a **user-adjustable scoring system** that combines LLM intelligence with configurable guardrails.

---

## Current State (v1 - Personal Tool)

### What Exists Today

1. **Data Ingestion Pipelines** (n8n workflows)
   - VC Portfolio Scrapers (Bessemer, a]16z, sector-specific funds)
   - Job Board Scrapers (Work at a Startup, Indeed, First Round Jobs)
   - Email Parsers (LinkedIn alerts, job alert emails)
   - Enrichment via Apollo, Brave Search, company websites

2. **Scoring System**
   - LLM-based evaluation (Claude/GPT-4o)
   - JavaScript guardrails for known failure modes
   - Post-score caps and adjustments
   - Output to Airtable for review

3. **Pain Points**
   - Scoring logic scattered across 7+ workflow nodes
   - Duplicate logic in two separate workflows
   - Hard to tune without editing code
   - No regression testing for scoring changes

### Lessons Learned

| Problem | Root Cause | Fix Applied |
|---------|------------|-------------|
| Fullview.io scored 82, should be ~50 | CX tooling companies get false sector match | Added CX vendor detection |
| Browserbase scored 10, should be ~78 | Bad employee count data (10 vs actual ~50) | Cross-reference with funding stage |
| Stale funding not penalized | No funding recency signal | Added years-since-funding calculation |
| LLM scores inconsistently | No guardrails on known failure modes | Post-score caps for edge cases |

These fixes are **empirically derived** from months of iteration. They represent domain knowledge that must be preserved.

---

## Target State (v2 - Productizable)

### Core Concept: The Adjustable Lens

Instead of one-size-fits-all scoring, each user configures their own "lens" - a set of preferences that shape how companies are evaluated.

```
┌─────────────────────────────────────────────────────────────┐
│  MY SCORING LENS                                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  I'm looking for:  ○ IC Role  ● Leadership Role  ○ Either  │
│                                                             │
│  Preferred Sectors                                          │
│  ☑ Healthcare   ☑ Fintech   ☐ E-commerce   ☐ DevTools      │
│                                                             │
│  Company Stage                                              │
│  Seed ────●━━━━━━━━━━━━●──── Series D                       │
│           Series A    Series C                              │
│                                                             │
│  Company Size (employees)                                   │
│  10 ──────●━━━━━━━━━━━━●────── 500                          │
│           20          300                                   │
│                                                             │
│  Funding Recency                                            │
│  Don't care ──────────●━━━━━━ Must be recent (<2 yrs)      │
│                                                             │
│  Deal Breakers                                              │
│  ☑ PE-backed companies                                      │
│  ☑ Consulting/services businesses                           │
│  ☐ Remote-only companies                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

User adjusts sliders/checkboxes → Config updates → Prompt assembles → Scores change

### Architecture: Config-Driven Scoring

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   User UI    │────▶│ Scoring      │────▶│   Prompt     │
│  (sliders)   │     │ Config       │     │  Assembly    │
└──────────────┘     └──────────────┘     └──────────────┘
                            │                    │
                            ▼                    ▼
                     ┌──────────────┐     ┌──────────────┐
                     │  Guardrails  │     │     LLM      │
                     │  (filters,   │────▶│  Evaluation  │
                     │   caps)      │     │              │
                     └──────────────┘     └──────────────┘
                                                │
                                                ▼
                                         ┌──────────────┐
                                         │ Final Score  │
                                         │ + Explanation│
                                         └──────────────┘
```

---

## Scoring Config Structure

### Overview

```javascript
const scoringConfig = {
  version: "2024-11-15",
  changelog: "Added CX tooling detection, raised Series B employee floor",

  filters: { /* Pre-scoring pass/fail gates */ },
  caps: { /* Post-scoring ceilings */ },
  adjustments: { /* Score modifiers */ },
  dataQuality: { /* Handle known data issues */ },
  promptConfig: { /* LLM instruction assembly */ }
};
```

### Filters (Pre-Scoring Gates)

Binary pass/fail applied BEFORE LLM scoring. Saves API costs by rejecting obvious mismatches early.

```javascript
filters: {
  // Company characteristics
  min_employees: 5,
  max_employees: null,  // null = no limit
  reject_pe_backed: true,
  max_years_since_funding: null,  // null = don't filter

  // Industry exclusions
  exclude_industries: ["consulting", "staffing", "recruiting"],

  // Stage requirements
  min_stage: "seed",
  max_stage: "series_d",

  // User-specific (future)
  exclude_companies: ["CompanyA", "CompanyB"],  // Previously rejected
  exclude_investors: ["InvestorX"]  // User preference
}
```

**UI Mapping:**
- `min/max_employees` → Range slider
- `reject_pe_backed` → Checkbox
- `exclude_industries` → Multi-select
- `min/max_stage` → Range slider

### Caps (Post-Scoring Ceilings)

Applied AFTER LLM scoring to enforce known constraints. Each cap includes evidence for why it exists.

```javascript
caps: {
  cs_hire_unlikely: {
    max: 65,
    condition: "cs_hire_likelihood === 'unlikely'",
    reason: "No CS leadership hire signal",
    added: "2024-08",
    evidence: "Fullview.io false positive - scored 82 with no CS signals"
  },

  self_serve_no_ops_gap: {
    max: 60,
    condition: "product_type === 'self_serve' && !ops_gap",
    reason: "Self-serve product without operational complexity",
    added: "2024-09",
    evidence: "Multiple PLG companies scoring high despite no CS need"
  },

  cx_tooling_vendor: {
    max: 55,
    condition: "is_cx_tooling_company === true",
    reason: "Company sells CX software, doesn't need CS leadership",
    added: "2024-11",
    evidence: "Fullview.io - cobrowsing vendor scored as sector match"
  },

  stale_early_stage: {
    max: 70,
    condition: "funding_age_years > 3 && stage in ['seed', 'series_a'] && employees < 100",
    reason: "Stale funding at early stage suggests zombie company",
    added: "2024-11",
    evidence: "Multiple 4+ year old seed companies with no growth"
  }
}
```

**UI Mapping:** Caps are generally NOT user-adjustable. They encode domain knowledge about scoring failure modes. Power users might enable/disable specific caps.

### Adjustments (Score Modifiers)

Additive bonuses/penalties based on signals. These stack.

```javascript
adjustments: {
  // Positive adjustments
  sector_match: {
    value: 15,
    trigger: "industry in user.preferred_sectors",
    description: "Company in preferred sector"
  },

  recent_funding: {
    value: 10,
    trigger: "funding_age_years < 1",
    description: "Raised funding within last year"
  },

  active_cs_hiring: {
    value: 10,
    trigger: "has_cx_job_posting === true",
    description: "Actively hiring for CS/CX roles"
  },

  network_connection: {
    value: 5,
    trigger: "has_network_connection === true",
    description: "User has LinkedIn connection at company"
  },

  // Negative adjustments
  stale_funding_penalty: {
    value: -10,
    trigger: "funding_age_years >= 3 && stage in ['seed', 'series_a']",
    description: "Early stage with stale funding"
  },

  employee_funding_mismatch: {
    value: -15,
    trigger: "employee_count_suspicious === true",
    description: "Employee count inconsistent with funding stage"
  }
}
```

**UI Mapping:**
- `sector_match` → Controlled by sector preference checkboxes
- `recent_funding` → Controlled by funding recency slider
- User could potentially adjust `value` weights with advanced sliders

### Data Quality Rules

Handle known data source conflicts and bad data patterns.

```javascript
dataQuality: {
  // Minimum employee counts by stage (catches bad data)
  employee_count_floor_by_stage: {
    pre_seed: 1,
    seed: 3,
    series_a: 15,
    series_b: 40,
    series_c: 100,
    series_d: 200
  },

  // Source priority for conflicting data
  employee_count_source_priority: ["linkedin", "apollo", "pitchbook", "website"],

  // Flag suspicious data for review
  flag_employee_funding_mismatch: true,

  // Trust signals
  linkedin_data_weight: 1.0,
  self_reported_data_weight: 0.7
}
```

**UI Mapping:** Data quality rules are NOT user-adjustable. They're system-level corrections for known data issues.

---

## Prompt Config: Three-Tier System

### Tier 1: System Persona (Locked)

The core instruction that defines the evaluation task. Users cannot modify this.

```javascript
promptConfig: {
  tier1_system: `You are evaluating companies for job seekers.
Your task is to assess how well each company matches the user's career preferences.
Be objective and evidence-based. Return structured JSON.`
}
```

**Why locked:** Changing this could break output format, change evaluation purpose, or introduce conflicting instructions.

### Tier 2: Evaluation Criteria (User-Tunable)

The signals and red flags the LLM should consider. Users can enable/disable and add custom criteria.

```javascript
promptConfig: {
  tier2_criteria: {
    // Positive signals - boost score when present
    positive_signals: [
      { id: "enterprise_customers", text: "B2B SaaS with enterprise customers", enabled: true },
      { id: "complex_onboarding", text: "Complex onboarding or implementation required", enabled: true },
      { id: "high_acv", text: "High ACV ($50K+) suggesting white-glove service", enabled: true },
      { id: "cs_hiring", text: "Active job posts for customer success roles", enabled: true },
      { id: "series_a_plus", text: "Series A or later with product-market fit", enabled: true },
      { id: "recent_funding", text: "Raised funding within last 18 months", enabled: false }
    ],

    // Red flags - lower score when present
    red_flags: [
      { id: "pure_plg", text: "Product-led growth with no enterprise motion", enabled: true },
      { id: "cx_vendor", text: "Company sells CX/support software to other companies", enabled: true },
      { id: "consulting", text: "Consulting or professional services business", enabled: true },
      { id: "pre_revenue", text: "Pre-seed with no revenue or customers", enabled: true },
      { id: "remote_only", text: "Fully remote with no office presence", enabled: false }
    ],

    // User's preferred sectors
    preferred_sectors: ["healthcare", "fintech", "infrastructure"],

    // User's target company profile
    target_profile: {
      stage: { min: "seed", max: "series_c" },
      size: { min: 20, max: 300 },
      funding_recency: "moderate"  // recent, moderate, any
    }
  }
}
```

**UI Mapping:**
- `positive_signals` → Checklist with toggles
- `red_flags` → Checklist with toggles
- `preferred_sectors` → Multi-select dropdown
- `target_profile.*` → Sliders and dropdowns

### Tier 3: Output Schema (Locked)

The structure the LLM must return. Users cannot modify this.

```javascript
promptConfig: {
  tier3_output: {
    schema: {
      score: "number (0-100)",
      cs_hire_likelihood: "enum: unlikely, low, medium, high",
      sector_match: "boolean",
      stage_fit: "boolean",
      size_fit: "boolean",
      red_flags_triggered: "array of strings",
      positive_signals_found: "array of strings",
      reasoning: "string (2-3 sentences)"
    }
  }
}
```

**Why locked:** Downstream processing (Airtable writes, caps, adjustments) depends on this exact structure.

### Prompt Assembly

```javascript
function assemblePrompt(config, companyData) {
  let prompt = config.promptConfig.tier1_system + "\n\n";

  // Tier 2: User preferences
  prompt += "USER PREFERENCES:\n";
  prompt += `Preferred sectors: ${config.promptConfig.tier2_criteria.preferred_sectors.join(', ')}\n`;
  prompt += `Target stage: ${config.promptConfig.tier2_criteria.target_profile.stage.min} to ${config.promptConfig.tier2_criteria.target_profile.stage.max}\n`;
  prompt += `Target size: ${config.promptConfig.tier2_criteria.target_profile.size.min}-${config.promptConfig.tier2_criteria.target_profile.size.max} employees\n\n`;

  // Tier 2: Enabled positive signals
  prompt += "POSITIVE SIGNALS (boost score when present):\n";
  for (const signal of config.promptConfig.tier2_criteria.positive_signals.filter(s => s.enabled)) {
    prompt += `- ${signal.text}\n`;
  }

  // Tier 2: Enabled red flags
  prompt += "\nRED FLAGS (lower score when present):\n";
  for (const flag of config.promptConfig.tier2_criteria.red_flags.filter(f => f.enabled)) {
    prompt += `- ${flag.text}\n`;
  }

  // Company data
  prompt += "\n\nCOMPANY DATA:\n" + JSON.stringify(companyData, null, 2);

  // Tier 3: Output format
  prompt += "\n\nReturn your evaluation as JSON matching this schema:\n";
  prompt += JSON.stringify(config.promptConfig.tier3_output.schema, null, 2);

  return prompt;
}
```

---

## Scoring Pipeline Flow

```
1. INGEST
   └── Company data from scrapers/parsers

2. ENRICH
   └── Apollo, Brave Search, LinkedIn data

3. PRE-FILTER (filters)
   ├── Apply binary gates
   ├── Reject: PE-backed, wrong stage, excluded industries
   └── Pass: Proceed to scoring

4. DATA QUALITY (dataQuality)
   ├── Cross-reference employee counts
   ├── Flag suspicious data
   └── Apply source priority for conflicts

5. LLM SCORING (promptConfig)
   ├── Assemble prompt from tiers 1-3
   ├── Send to Claude/GPT-4o
   └── Parse structured response

6. POST-PROCESS (caps, adjustments)
   ├── Apply caps based on conditions
   ├── Apply adjustment bonuses/penalties
   └── Calculate final score

7. OUTPUT
   ├── Final score (0-100)
   ├── Explanation breakdown
   ├── Flags for review
   └── Write to Airtable
```

---

## Explanation Output

Every scored company includes a breakdown for debugging and transparency.

```javascript
{
  company: "Acme Corp",
  final_score: 72,

  explanation: {
    llm_base_score: 78,

    caps_applied: [],

    adjustments_applied: [
      { rule: "sector_match", effect: +15, reason: "Healthcare sector" },
      { rule: "stale_funding_penalty", effect: -10, reason: "Series A, 3.5 years since funding" },
      { rule: "employee_funding_mismatch", effect: -15, reason: "Employee count 12 seems low for Series A" }
    ],

    data_quality_notes: [
      "Employee count from Apollo (12) below Series A floor (15), flagged for review"
    ],

    llm_reasoning: "B2B healthcare SaaS with enterprise focus. Complex implementation suggests CS need. However, small team size and aging funding raise concerns about growth trajectory."
  },

  config_version: "2024-11-15",
  scored_at: "2024-11-15T14:30:00Z"
}
```

---

## Regression Testing

Every false positive/negative fix becomes a regression test case.

```javascript
const regressionSuite = [
  {
    company: "Fullview.io",
    expectedRange: [45, 55],
    mustTrigger: ["cx_tooling_vendor cap"],
    reason: "CX tooling company - sells cobrowsing software"
  },
  {
    company: "Browserbase",
    expectedRange: [70, 85],
    mustTrigger: ["employee_funding_mismatch flag"],
    mustNotTrigger: ["auto-reject"],
    reason: "Series B infrastructure - bad employee data should flag, not reject"
  },
  {
    company: "Stripe",
    expectedRange: [30, 50],
    mustTrigger: ["pure_plg red flag", "size exceeds max"],
    reason: "Too large, PLG-focused, not hiring CS leadership"
  }
];

function runRegressionTests(config) {
  for (const testCase of regressionSuite) {
    const result = scoreCompany(testCase.company, config);

    assert(result.score >= testCase.expectedRange[0],
      `${testCase.company} scored ${result.score}, expected >= ${testCase.expectedRange[0]}`);
    assert(result.score <= testCase.expectedRange[1],
      `${testCase.company} scored ${result.score}, expected <= ${testCase.expectedRange[1]}`);

    // Verify expected triggers
    for (const trigger of testCase.mustTrigger || []) {
      assert(result.explanation.includes(trigger),
        `${testCase.company} should trigger: ${trigger}`);
    }
  }
}
```

---

## Implementation Phases

### Phase 1: Config Extraction (Current Work)

- [ ] Extract all hardcoded thresholds into `scoringConfig` object
- [ ] Store config as JSON file in repo (version controlled)
- [ ] Load config at workflow start
- [ ] Add explanation output to all scored companies
- [ ] Build initial regression test suite (Fullview, Browserbase, etc.)

### Phase 2: Config Consolidation

- [ ] Merge VC workflow and Job Search workflow scoring logic
- [ ] Single "Scoring Service" sub-workflow both pipelines call
- [ ] Move config to Airtable Config table (queryable, editable)
- [ ] Add config versioning and changelog

### Phase 3: User Adjustability (MVP)

- [ ] Simple web UI for editing Tier 2 criteria
- [ ] Sliders for stage, size, funding recency
- [ ] Checkboxes for sectors, signals, red flags
- [ ] Preview mode: "Re-score last 10 companies with new settings"

### Phase 4: Multi-User (Product)

- [ ] User accounts with individual configs
- [ ] Default config as starting point
- [ ] Config templates ("CS Leader", "Sales Leader", "Engineering Manager")
- [ ] A/B testing infrastructure for config changes

---

## Open Questions for Review

1. **Config Storage:** JSON file vs Airtable Config table vs dedicated database?
   - JSON: Easy to version control, harder to edit without deploy
   - Airtable: Already in stack, queryable, but schema constraints
   - Database: Most flexible, but adds infrastructure

2. **Prompt Assembly Complexity:** How much should users be able to customize?
   - Conservative: Just sliders and checkboxes (current plan)
   - Moderate: Add custom positive signals / red flags
   - Aggressive: Edit prompt fragments directly (risky)

3. **Regression Test Execution:** When and how to run?
   - On every config change? (thorough but slow)
   - Nightly batch? (catches drift)
   - Manual trigger? (developer responsibility)

4. **Explanation Verbosity:** How much detail to store?
   - Minimal: Just final score + top 3 factors
   - Moderate: Full breakdown (current plan)
   - Verbose: Include raw LLM response, all intermediate values

5. **Multi-Persona Support:** Should one user have multiple lenses?
   - Example: "CS Leadership" lens vs "Product Manager" lens
   - Would require config-per-lens, selector in UI

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| False positive rate | ~15% | <5% |
| False negative rate | ~10% | <3% |
| Time to tune scoring | Hours (code change) | Minutes (UI) |
| Regression test coverage | 0 cases | 20+ cases |
| Config change audit trail | None | Full history |

---

## Appendix: Current False Positive/Negative Log

| Company | Actual Score | Expected | Issue | Fix |
|---------|--------------|----------|-------|-----|
| Fullview.io | 82 | 50-55 | CX tooling vendor got sector match | Add CX vendor cap |
| Browserbase | 10 (rejected) | 75-85 | Bad employee data | Add employee/funding cross-ref |
| [Add more as discovered] | | | | |

---

*Document Version: 1.0*
*Last Updated: 2024-11-15*
*Author: Tide Pool Development*
