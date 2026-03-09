# Tide Pool Scoring Architecture

## Overview

The Tide Pool scoring system uses a **four-layer architecture** that splits responsibilities between a portable context document (the Agent Lens), deterministic code (n8n nodes), LLM-based classification (Customer Persona), and LLM-based evaluation (Claude API). This design optimizes for cost, speed, reliability, and maintainability.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SCORING ARCHITECTURE (v8.4)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ LAYER 1: TIDE POOL AGENT LENS (GitHub)                               │   │
│  │ tide-pool-agent-lens.md                                              │   │
│  │                                                                       │   │
│  │ • Source of truth for ALL scoring criteria                           │   │
│  │ • Human-readable YAML + prose documentation                          │   │
│  │ • Fetched at runtime by n8n workflows                                │   │
│  │ • Updated independently of workflow code                             │   │
│  │                                                                       │   │
│  │ Contains:                                                             │   │
│  │ - Disqualifier lists (PE firms, sectors, thresholds)                 │   │
│  │ - Penalty rules and point values                                     │   │
│  │ - Candidate profile and preferences                                  │   │
│  │ - Data validation flags                                              │   │
│  │ - Customer persona classification rules                              │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ LAYER 2: N8N PRE-FILTER (Parse Enrichment node)                      │   │
│  │ Enrich & Evaluate Pipeline v8.4                                      │   │
│  │                                                                       │   │
│  │ • Deterministic code-based gates                                     │   │
│  │ • Runs BEFORE any Claude API calls                                   │   │
│  │ • Binary pass/fail decisions                                         │   │
│  │ • No LLM cost for disqualified companies                             │   │
│  │                                                                       │   │
│  │ Implements:                                                           │   │
│  │ - Data extraction (employees, funding, stage, valuation)             │   │
│  │ - Pattern matching (PE firms, acquisition keywords)                  │   │
│  │ - Threshold checks (>200 emp, >$500M funding)                        │   │
│  │ - Sector detection (hardware, biotech, crypto, etc.)                 │   │
│  │ - Data validation flags                                              │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                    ┌───────────────┴───────────────┐                        │
│                    ▼                               ▼                        │
│           ┌──────────────┐                ┌──────────────┐                  │
│           │ DISQUALIFIED │                │  LAYER 2.5:  │                  │
│           │  Score = 0   │                │   PERSONA    │                  │
│           │  No API call │                │   GATE       │                  │
│           └──────────────┘                └──────┬───────┘                  │
│                                                  │                          │
│                                                  ▼                          │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ LAYER 3: CUSTOMER PERSONA CLASSIFICATION (Classify Persona node)    │   │
│  │                                                                       │   │
│  │ • Fast Claude call (Haiku) - single word classification              │   │
│  │ • Identifies developer-as-customer vs business-user-customer         │   │
│  │ • Developer companies auto-pass UNLESS enterprise exception          │   │
│  │                                                                       │   │
│  │ Classification:                                                       │   │
│  │ - business-user: Non-technical end users (sales, HR, finance, etc.) │   │
│  │ - developer: Technical practitioners (devs, SRE, data engineers)    │   │
│  │ - mixed: Both personas are primary users                             │   │
│  │                                                                       │   │
│  │ Enterprise Exception (proceed despite developer persona):            │   │
│  │ - 50+ employees AND 2+ signals: SOC 2, Fortune 500 customers,        │   │
│  │   enterprise sales, SSO/SAML, compliance, procurement                │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                    ┌───────────────┴───────────────┐                        │
│                    ▼                               ▼                        │
│           ┌──────────────┐                ┌──────────────┐                  │
│           │  DEVELOPER   │                │   EVALUATE   │                  │
│           │  AUTO-PASS   │                │  via Claude  │                  │
│           │  Score = 0   │                │              │                  │
│           └──────────────┘                └──────┬───────┘                  │
│                                                  │                          │
│                                                  ▼                          │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ LAYER 4: CLAUDE EVALUATION (Build Evaluation Prompt node)            │   │
│  │                                                                       │   │
│  │ • LLM-based nuanced scoring                                          │   │
│  │ • Judgment calls that require reasoning                              │   │
│  │ • 100-point weighted model across 5 categories                       │   │
│  │ • Receives lens context in system prompt                             │   │
│  │                                                                       │   │
│  │ Evaluates:                                                            │   │
│  │ - CS Hire Readiness (30 pts) - Does company need this hire NOW?      │   │
│  │ - Stage & Size Fit (25 pts) - Right inflection point?                │   │
│  │ - Role Mandate (20 pts) - Builder vs Maintainer?                     │   │
│  │ - Sector & Mission (15 pts) - Alignment with experience?             │   │
│  │ - Outreach Feasibility (10 pts) - Network access?                    │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Why Four Layers?

### The Problem with "Just Use the MD File"

If we sent every company directly to Claude with the Agent Lens for evaluation:

| Metric | Claude-Only Approach | Four-Layer Approach |
|--------|---------------------|---------------------|
| **Cost** | ~$0.003/company × 500/week = **$78/month** | ~$0.003 × 100 evaluated = **$15/month** |
| **Speed** | 3-5 sec per company | <100ms for pre-filter, 0.5s persona, 3-5s only for candidates |
| **Reliability** | LLM may miss obvious disqualifiers | Code-based gates are deterministic |
| **Rate Limits** | Risk of API throttling at volume | 80% fewer full evaluation API calls |

### Why Add the Persona Gate?

The March 2026 audit revealed that ~60% of "Apply Now" companies were developer-as-customer tools that don't match Eric's background in enterprise B2B support for business users. Examples: Coiled, Inngest, Datafold, Orb, Gable, Secoda.

**Developer-as-customer support is fundamentally different:**
- Technical users who prefer docs/self-serve over human support
- Community/Slack-based support models
- Different success metrics (API uptime vs NPS/CSAT)
- Different skills required (can you read a stack trace?)

The persona gate uses a fast Claude Haiku call (~$0.00025/company) to classify customer type, then auto-passes developer tools unless they've reached enterprise scale (50+ employees + enterprise motion signals).

### Why Not Just Code Everything?

Pure code-based scoring fails at nuanced judgment:

- **"Does this company need a CS hire NOW?"** - Requires reading between the lines of company descriptions, inferring from funding timing, team size signals
- **"Is this a builder or maintainer role?"** - Requires understanding role mandates from limited context
- **"How strong is the sector alignment?"** - Healthcare B2B SaaS covers a spectrum from "perfect fit" to "adjacent"
- **"Is this a developer tool?"** - API, CLI, SDK keywords help but context matters (Salesforce has APIs but is business-user-customer)

Code can check `employee_count > 200`. Code cannot determine "this Series A company's description suggests they're still founder-led on customer relationships."

---

## Layer Details

### Layer 1: Tide Pool Agent Lens

**Location:** `https://raw.githubusercontent.com/zelman/tidepool/main/tide-pool-agent-lens.md`

**Purpose:** Single source of truth that can be updated without touching workflow code.

**What it contains:**

```yaml
# Hard disqualifiers (implemented in n8n as code)
disqualify:
  investor_type: [PE, Growth Equity]
  employee_count_max: 200
  employee_count_min: 15
  total_funding_max: 500000000
  company_status: [Acquired, Shut Down, Merged, Defunct]
  company_type: [Fortune 500, Fortune 500 Subsidiary, Public]
  business_model: [B2C, Consumer, Hardware, ...]
  domain_expertise_required: [Web3, Crypto, Biotech, ...]

# Penalties (passed to Claude for weighted scoring)
penalties:
  - rule: "150-200 employees"
    points: -20
  - rule: "Series C"
    points: -10

# Candidate context (passed to Claude)
target_roles: [Director of Customer Support, VP of Customer Support, ...]
compensation_target: 125000
```

**Why it's separate:**
1. **Portability** - Same lens works across Claude Code, Claude.ai, n8n, other tools
2. **Versioning** - Git history tracks all criteria changes
3. **Transparency** - Human-readable explanation of every rule
4. **Independence** - Update thresholds without re-deploying workflows

---

### Layer 2: n8n Pre-Filter (Parse Enrichment)

**Location:** `Enrich & Evaluate Pipeline v8.4.json` → "Parse Enrichment" node

**Purpose:** Fast, cheap, deterministic filtering before expensive LLM calls.

**What it implements:**

| Check | Implementation | Why Code, Not LLM |
|-------|---------------|-------------------|
| Employee count | Regex: `/(\d+)\s*employees/i` | Binary threshold check |
| Funding amount | Contextual regex + parsing | Numeric comparison |
| PE backing | String match against 29-firm list | Exact match lookup |
| Acquisition | Multiple regex patterns | Pattern matching |
| Public company | NYSE/NASDAQ/IPO keywords | Keyword detection |
| Sector exclusion | Hardware/biotech/crypto keywords | Presence check |
| Fortune 500 | Match against 45-company list | Exact match lookup |
| Data validation | Stage vs funding/employee combos | Logic rules |

**What it does NOT implement:**
- "Is this company at the right inflection point?" (requires judgment)
- "Does the description suggest CS hire readiness?" (requires inference)
- "How strong is the sector alignment?" (requires spectrum assessment)

**Output:**
```javascript
{
  isAutoDisqualified: true/false,
  autoDisqualifiers: ["PE-backed (Vista Equity)", ">200 employees (350)"],
  warnings: ["Employee count 175 in penalty zone"],
  data_flags: ["Data inconsistency: Seed stage with $25M funding"],
  // ... extracted fields for Claude
}
```

---

### Layer 3: Customer Persona Classification (v8.4)

**Location:** `Enrich & Evaluate Pipeline v8.4.json` → "Classify Persona via Claude" node

**Purpose:** Fast LLM classification to identify developer-as-customer companies that don't match Eric's background.

**Why this layer exists:**
The March 2026 audit found that ~60% of "Apply Now" companies were developer tools. These companies have fundamentally different support models:
- Developers prefer self-serve docs over human support
- Community/Slack-based support is common
- Technical skills required (debugging API issues, reading stack traces)
- Lower headcount in support orgs (often just 1-2 people even at scale)

**Classification prompt:**
```
Classify as ONE of:
- "business-user": End users are non-technical business professionals
- "developer": End users are developers, engineers, DevOps, SRE, data engineers
- "mixed": Both personas are equally important primary users
```

**Enterprise exception logic:**
Developer-as-customer companies still proceed to scoring if they meet the enterprise exception:
- 50+ employees, AND
- 2+ enterprise signals from: SOC 2, HIPAA, compliance, Fortune 500/1000 customers, enterprise sales team, account executives, SSO, SAML, multi-tenant, self-hosted, on-premise, contract value, ACV, ARR, procurement, vendor management

**Output:**
```javascript
{
  customer_persona: "business-user" | "developer" | "mixed",
  enterprise_signal_count: 2,
  has_enterprise_exception: true,  // 50+ emp + 2+ signals
  developer_auto_pass: false,      // if true, skip scoring
  developer_auto_pass_reason: null // or "Developer-as-customer (35 employees)"
}
```

**Cost:** ~$0.00025/company (Claude Haiku, 50 token response)

---

### Layer 4: Claude Evaluation (Build Evaluation Prompt)

**Location:** `Enrich & Evaluate Pipeline v8.4.json` → "Build Evaluation Prompt" node

**Purpose:** Nuanced scoring that requires LLM reasoning.

**What it evaluates:**

```
100-POINT SCORING MODEL

1. CS HIRE READINESS (30 points max)
   Does the company need a CS hire NOW?
   - 30 = First CX hire needed (no existing team, product launched)
   - 25 = Very small team (<5), needs senior leadership
   - 20 = Small team (<10), building out org
   ...
   Requires: Inferring from company description, funding timing, team signals

2. STAGE & SIZE FIT (25 points max)
   Is this the right stage/size for a builder?
   - 25 = Seed/Series A, 10-50 employees (sweet spot)
   - 20 = Series B, 30-80 employees
   ...
   Requires: Understanding growth trajectory, not just current numbers

3. ROLE MANDATE (20 points max)
   Builder (0-to-1) or Maintainer (scale existing)?
   - 20 = Clear builder opportunity (first hire, greenfield)
   - 5 = Mostly maintaining/optimizing existing org
   ...
   Requires: Reading between lines of company positioning

4. SECTOR & MISSION (15 points max)
   Does the sector/mission align?
   - 15 = Healthcare B2B SaaS (providers, clinical)
   - 12 = Developer tools, infrastructure
   - 10 = Enterprise B2B SaaS
   ...
   Requires: Spectrum assessment, not binary match

5. OUTREACH FEASIBILITY (10 points max)
   How accessible is this opportunity?
   - 10 = YC company (network advantage) + founder accessible
   - 8 = Known VC portfolio + clear contact
   ...
   Requires: Knowledge of VC relationships, network effects
```

**Why this needs an LLM:**
- "Company X raised Series A 6 months ago and has 25 employees" → Code sees numbers
- Claude infers: "This is likely pre-CS function, founder still handling relationships, prime window for first hire" → Judgment

---

## Data Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ VC Scraper  │────▶│ Brave Search│────▶│   Parse     │────▶│  Hard Gate  │
│ (source)    │     │ (enrich)    │     │ Enrichment  │     │  Check?     │
└─────────────┘     └─────────────┘     └─────────────┘     └──────┬──────┘
                                                                    │
                                         ┌──────────────────────────┴──────┐
                                         │                                 │
                                         ▼                                 ▼
                                  ┌─────────────┐                   ┌─────────────┐
                                  │ Disqualified│                   │  Classify   │
                                  │ Score = 0   │                   │  Persona    │
                                  │ → Airtable  │                   │ (Haiku)     │
                                  └─────────────┘                   └──────┬──────┘
                                                                           │
                                         ┌─────────────────────────────────┴──────┐
                                         │                                        │
                                         ▼                                        ▼
                                  ┌─────────────┐                          ┌─────────────┐
                                  │  Developer  │                          │  Evaluate   │
                                  │  Auto-Pass  │                          │  via Claude │
                                  │  Score = 0  │                          │  (Haiku)    │
                                  │ → Airtable  │                          └──────┬──────┘
                                  └─────────────┘                                 │
                                                                                  ▼
                                                                           ┌─────────────┐
                                                                           │ Score 0-100 │
                                                                           │ → Airtable  │
                                                                           └─────────────┘
```

---

## Maintenance Model

| Change Type | Where to Update | Deployment |
|-------------|-----------------|------------|
| Add new PE firm | Agent Lens (YAML) + Parse Enrichment (peFirms array) | Commit + re-import workflow |
| Change employee threshold | Agent Lens (YAML) + Parse Enrichment (constants) | Commit + re-import workflow |
| Add sector exclusion | Agent Lens (YAML) + Parse Enrichment (regex) | Commit + re-import workflow |
| Adjust scoring weights | Build Evaluation Prompt (systemPrompt) | Re-import workflow |
| Update candidate profile | Agent Lens only | Commit to GitHub |
| Add penalty rule | Agent Lens (YAML) + Build Evaluation Prompt | Commit + re-import workflow |
| Change persona classification | Build Persona Prompt (systemPrompt) | Re-import workflow |
| Add enterprise exception signal | Parse Persona & Check Enterprise (enterpriseSignals) | Re-import workflow |
| Change enterprise exception threshold | Parse Persona & Check Enterprise (50 emp, 2 signals) | Re-import workflow |

**Note:** Some changes require updates in two places (lens + workflow) because:
1. The lens is documentation/source of truth
2. The workflow implements the actual logic
3. They must stay in sync

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v8.4 | 2026-03-06 | Customer Persona Gate - classifies business-user vs developer-as-customer, auto-passes developer tools unless 50+ emp + 2+ enterprise signals |
| v8.3 | 2026-03-06 | March 2026 Audit fixes - two-tier architecture, Fortune 500 detection, employee 200 cap |
| v8.2 | 2026-03-06 | Employee min/max gates, valuation extraction, HR Tech/DEI detection |
| v8.1 | 2026-03 | Funding extraction improvements, $5B sanity cap |
| v8 | 2026-02 | 100-point model, 5-category scoring, public company gates |

---

## Rescore Mode

The pipeline supports a **rescore mode** for re-evaluating existing Airtable records that have score = 0 or were evaluated with outdated logic.

**How it works:**

1. `Funding Alerts Rescore v3` fetches records with score = 0 from Airtable
2. It formats them with `_isRescore: true` and `_updateRecordId: {record.id}`
3. The pipeline detects `_isRescore` and **bypasses all dedup logic**
4. Records go straight to Brave Search enrichment → Parse Enrichment → Claude evaluation
5. Pipeline updates the existing record instead of creating new

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Rescore v3  │────▶│ IF: Rescore │────▶│ Build Query │──▶ (normal flow)
│ (_isRescore)│     │   Mode?     │     │ (skip dedup)│
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │ false
                           ▼
                    ┌─────────────┐
                    │ Dedup Check │──▶ (normal new company flow)
                    └─────────────┘
```

**Why rescore needs its own mode:**
- Existing records are already in the Seen Opportunities table
- Without bypass, they'd be skipped as duplicates
- We want to re-evaluate with updated gates/prompts, not skip

---

## FAQ

**Q: Why not embed the lens directly in the workflow?**
A: Portability. The same lens is used by Claude Code for resume tailoring, Claude.ai for research, and n8n for automated scoring. One source of truth.

**Q: Why duplicate logic between lens and workflow?**
A: The lens is documentation; the workflow is implementation. The lens says "disqualify >200 employees" in human-readable YAML. The workflow implements `if (employeeCount > 200) autoDisqualifiers.push(...)`. Both are needed.

**Q: Why not have Claude read the lens and do all filtering?**
A: Cost and reliability. Claude costs ~$0.003 per evaluation. Pre-filtering 70% of companies in code saves ~$55/month. Also, code doesn't hallucinate threshold checks.

**Q: When should I update the lens vs the workflow?**
A: Update both when changing disqualification logic. Update only the lens when changing documentation/context. Update only the workflow when fixing bugs in extraction logic.
