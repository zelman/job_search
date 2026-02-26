# Tide Pool Job Search System Architecture

## Overview

This document details the technical architecture of the Tide Pool job search automation system, with emphasis on the modular evaluation sub-routine that enables consistent AI-powered job scoring across all workflows.

---

## System Components

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              DATA SOURCES                                        │
├─────────────────────┬─────────────────────┬─────────────────────────────────────┤
│   Email Parsers     │   Web Scrapers      │   VC Portfolio Miners               │
│   (10 job boards)   │   (YC, Costanoa)    │   (5 thematic scrapers)             │
└──────────┬──────────┴──────────┬──────────┴──────────────┬──────────────────────┘
           │                     │                         │
           ▼                     ▼                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     STANDARDIZED EVALUATION SUB-ROUTINE                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ Brave Search│→ │   Parse     │→ │   Build     │→ │   Wait      │              │
│  │   Company   │  │ Enrichment  │  │   Prompt    │  │ (Rate Limit)│              │
│  └─────────────┘  └─────────────┘  └─────────────┘  └──────┬──────┘              │
│                                                            │                     │
│                   ┌─────────────┐  ┌─────────────┐         │                     │
│                   │   Parse     │← │ Call Claude │←────────┘                     │
│                   │  Response   │  │     API     │                               │
│                   └──────┬──────┘  └─────────────┘                               │
└──────────────────────────┼──────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              AIRTABLE STORAGE                                    │
│  ├── Job Listings (scored opportunities)                                         │
│  ├── Funding Alerts (VC portfolio companies)                                     │
│  └── Config (API keys, credentials)                                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│  Review Status: New → Reviewing → Applied / Not a Fit → Archived                 │
└──────────────────────────┬──────────────────────────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────────────────────────┐
│                      CROSS-SOURCE DEDUPLICATION LAYER                            │
│  ┌─────────────────────────────┐    ┌─────────────────────────────┐             │
│  │  Dedup Check Subworkflow    │    │  Dedup Register Subworkflow │             │
│  │  (Before evaluation)        │    │  (After Airtable upsert)    │             │
│  │  → Generate normalized key  │    │  → Create Seen record       │             │
│  │  → Query Seen Opportunities │    │  → Link to job/company      │             │
│  │  → Skip if duplicate        │    │  → Track all sources        │             │
│  └──────────────┬──────────────┘    └──────────────┬──────────────┘             │
│                 │                                   │                            │
│                 └───────────────┬───────────────────┘                            │
│                                 ▼                                                │
│                     Seen Opportunities Table                                     │
│                     (Central dedup registry)                                     │
└──────────────────────────┬──────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           FEEDBACK LOOP LAYER                                    │
│  ┌─────────────────────────────┐    ┌─────────────────────────────┐             │
│  │  Not a Fit Analysis         │    │  Applied Analysis            │             │
│  │  (Weekly Mon 9am)           │    │  (Weekly Mon 9:30am)         │             │
│  │  → Pattern detection        │    │  → Calibration check         │             │
│  │  → New disqualifier ideas   │    │  → Score distribution        │             │
│  │  → Scoring adjustments      │    │  → Positive signal discovery │             │
│  └──────────────┬──────────────┘    └──────────────┬──────────────┘             │
│                 │                                   │                            │
│                 └───────────────┬───────────────────┘                            │
│                                 ▼                                                │
│                     Email Reports → Manual Lens Updates                          │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Modular Evaluation Sub-Routine

### Design Philosophy

The evaluation chain is designed for **modularity** and **maintainability**:

| Node | Responsibility | Swappable? | Swap Examples |
|------|----------------|------------|---------------|
| **Brave Search Company** | Fetch raw company intelligence | Yes | Clearbit, Apollo, Crunchbase API, Diffbot |
| **Parse Enrichment** | Normalize to standard schema | Adjust | Parse new API response format |
| **Fetch Profile** | Load evaluation criteria | Yes | Local file, Airtable, different URL |
| **Build Prompt** | Construct LLM prompt | Stable | Usually unchanged |
| **Wait (Rate Limit)** | API throttling | Adjust | Change delay per API limits |
| **Call Claude API** | LLM inference | Yes | OpenAI, Gemini, local LLM |
| **Parse Response** | Extract structured output | Adjust | Handle different response formats |

### Data Flow

```
Job Data (from source)
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│ BRAVE SEARCH COMPANY                                          │
│ ─────────────────────                                         │
│ Input:  { Company: "Acme Corp", ... }                        │
│ Action: GET https://api.search.brave.com/res/v1/web/search   │
│         Query: "Acme Corp" funding series employees          │
│                site:crunchbase.com OR site:pitchbook.com     │
│ Output: { web: { results: [...] } }                          │
└──────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│ PARSE ENRICHMENT                                              │
│ ────────────────                                              │
│ Input:  Brave Search results                                  │
│ Action: Extract via regex patterns:                           │
│         - Employee count (multiple patterns)                  │
│         - Funding stage (Series A/B/C, Seed, etc.)           │
│         - Total funding raised                                │
│         - PE vs VC backing (35+ PE firm names)               │
│         - Founded year                                        │
│ Output: {                                                     │
│   _enrichment: {                                              │
│     employeeCount: 150,                                       │
│     fundingStage: "Series B",                                │
│     totalFunding: 45,  // millions                           │
│     isPEBacked: false,                                        │
│     isVCBacked: true,                                         │
│     foundedYear: 2019,                                        │
│     companyAge: 7,                                            │
│     autoDisqualifiers: []                                     │
│   }                                                           │
│ }                                                             │
└──────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│ FETCH PROFILE (runs at workflow start)                        │
│ ─────────────                                                 │
│ Input:  None (triggered by schedule)                          │
│ Action: GET https://raw.githubusercontent.com/zelman/         │
│             tidepool/refs/heads/main/tide-pool-agent-lens.md │
│ Output: Full Tide Pool Agent Lens markdown document           │
└──────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│ BUILD PROMPT                                                  │
│ ────────────                                                  │
│ Input:  Job data + Enrichment + Profile                       │
│ Action: Construct system prompt with:                         │
│         - Full Tide Pool Agent Lens                           │
│         - Scoring framework (100 points)                      │
│         - Builder vs Maintainer criteria                      │
│         - Auto-disqualifier rules                             │
│         Construct user prompt with:                           │
│         - Job title, company, location, salary                │
│         - Enrichment data block                               │
│         - Prefilter analysis                                  │
│ Output: { _systemPrompt, _userPrompt, _apiKey }              │
└──────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│ WAIT (RATE LIMIT)                                             │
│ ─────────────────                                             │
│ Input:  Prompt data                                           │
│ Action: Wait 30 seconds                                       │
│ Output: Passthrough                                           │
│                                                               │
│ Note: Prevents Anthropic API rate limiting when processing    │
│       multiple jobs in sequence                               │
└──────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│ CALL CLAUDE API                                               │
│ ───────────────                                               │
│ Input:  System prompt + User prompt                           │
│ Action: POST https://api.anthropic.com/v1/messages            │
│         Model: claude-haiku-4-5-20250314                      │
│         Max tokens: 2000                                      │
│ Output: {                                                     │
│   content: [{                                                 │
│     text: "{ \"score\": 75, \"role_type\": \"builder\", ...}"|
│   }]                                                          │
│ }                                                             │
└──────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│ PARSE RESPONSE                                                │
│ ──────────────                                                │
│ Input:  Claude API response                                   │
│ Action: Extract JSON from response text                       │
│         - Robust parsing with regex fallback                  │
│         - Handle malformed JSON                               │
│         - Append enrichment summary to rationale              │
│ Output: {                                                     │
│   "Job Title": "...",                                        │
│   "Company": "...",                                          │
│   "Tide-Pool Score": 75,                                     │
│   "Tide-Pool Rationale": "Strong builder signals...",        │
│   "Role Type": "builder",                                     │
│   "Builder Evidence": "first hire; build from scratch",      │
│   "Maintainer Evidence": "",                                  │
│   "Recommendation": "apply",                                  │
│   "Industry": "Enterprise SaaS",                             │
│   "Company Stage": "series_b"                                │
│ }                                                             │
└──────────────────────────────────────────────────────────────┘
       │
       ▼
    Airtable
```

---

## Enrichment Schema

The `_enrichment` object provides a **standardized interface** between data fetching and prompt building:

```javascript
{
  // Company size
  employeeCount: number | null,      // Extracted from search results

  // Funding information
  fundingStage: string | null,       // Pre-Seed, Seed, Series A/B/C/D+, Public
  totalFunding: number | null,       // In millions (e.g., 45 = $45M)

  // Investor type (critical signal)
  isPEBacked: boolean,               // Private equity - auto-disqualifier
  isVCBacked: boolean,               // Venture capital - positive signal

  // Company age
  foundedYear: number | null,        // e.g., 2019
  companyAge: number | null,         // Years since founding

  // Source tracking
  enrichmentSource: string | null,   // URL of primary data source
  rawSnippets: string[],             // First 3 search result snippets

  // Auto-disqualification
  autoDisqualifiers: string[],       // Reasons for automatic rejection
  isKnownLarge: boolean,             // Known large company flag
  hasSkillsMismatch: boolean         // Required skills mismatch
}
```

### Auto-Disqualifier Rules

| Rule | Threshold | Rationale |
|------|-----------|-----------|
| PE-backed | Any PE investor | PE firms optimize for cost-cutting, not building |
| Employee count | ≥ 1,000 | Too large for builder role |
| Total funding | ≥ $500M | Late-stage, likely has mature operations |
| Public company | IPO/NASDAQ/NYSE | Established, not startup |
| Known large | Anthropic, Google, Meta, etc. | Pre-flagged companies |
| Zombie company | 7+ years old + still Seed + <100 employees | Stalled growth |
| Skills mismatch | HIPAA/PHI required | Healthcare compliance expertise needed |

---

## Workflow Implementations

### Job Alert Email Parser v3-32

```
Schedule (hourly)
       │
       ├──→ Fetch Profile (GitHub)
       │
       ├──→ Get Config (Airtable: ANTHROPIC_API_KEY)
       │
       ├──→ Search records (Airtable: existing jobs)
       │
       └──→ Get many messages (Gmail)
                   │
                   ▼
              Mark as Read
                   │
                   ▼
             Identify Source (10 parsers)
                   │
                   ▼
               Parse Jobs
                   │
                   ▼
               Has Jobs? ──No──→ No Jobs Found
                   │
                  Yes
                   │
                   ▼
            Merge + Dedup
                   │
                   ▼
        Map Fields for Airtable
                   │
                   ▼
    Prefilter: Builder vs Maintainer
                   │
                   ▼
         IF: Should Process ──No──→ Skip Filtered Jobs
                   │
                  Yes
                   │
                   ▼
    ┌─────────────────────────────────┐
    │  EVALUATION SUB-ROUTINE         │
    │  (7-node chain - see above)     │
    └─────────────────────────────────┘
                   │
                   ▼
            Filter Empty
                   │
                   ▼
          Add to Airtable
                   │
                   ▼
        Add label to message (Gmail)
```

### Work at a Startup Scraper v6

```
Schedule (every 6 hours)
       │
       ├──→ Get Config (Airtable)
       │
       ├──→ Search Existing Jobs (Airtable)
       │
       └──→ Fetch Profile (GitHub)  ← NEW in v6
                   │
              Parse Config
                   │
       ┌───────────┴───────────┐
       ▼                       ▼
Scrape via Browserless    Scrape Costanoa
(YC Work at a Startup)    (Costanoa VC jobs)
       │                       │
       ▼                       ▼
 Parse & Filter YC       Parse Costanoa Jobs
       │                       │
       └───────────┬───────────┘
                   ▼
           Merge Job Sources
                   │
                   ▼
           Merge for Dedup
                   │
                   ▼
        Dedup Against Airtable
                   │
                   ▼
              Has Jobs? ──No──→ No Jobs/Error
                   │
                  Yes
                   │
                   ▼
    Prefilter: Builder vs Maintainer
                   │
                   ▼
         IF: Should Process ──No──→ Skip Filtered Jobs
                   │
                  Yes
                   │
                   ▼
    ┌─────────────────────────────────┐
    │  EVALUATION SUB-ROUTINE         │  ← NEW in v6
    │  (7-node chain - same as above) │
    └─────────────────────────────────┘
                   │
                   ▼
          Add to Airtable
```

---

## Feedback Loop Architecture

### Purpose

The feedback loops create a **closed-loop learning system** that continuously refines the Tide Pool Agent Lens based on actual user decisions. Instead of static scoring rules, the system learns from patterns in accepted and rejected opportunities.

### Feedback Loop - Not a Fit

**Goal**: Identify patterns in rejected jobs to suggest new auto-disqualifiers and scoring penalties.

```
Schedule (Weekly Mon 9am)
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│ QUERY NOT A FIT JOBS                                          │
│ ─────────────────────                                         │
│ Filter: Review Status = 'Not a Fit'                          │
│         Date Found >= 7 days ago                              │
│ Fields: Title, Company, Score, Rationale, Industry,          │
│         Stage, Role Type, Builder/Maintainer Evidence        │
└──────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│ AGGREGATE JOBS                                                │
│ ──────────────                                                │
│ Combine all job records into single payload for analysis     │
└──────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│ CLAUDE SONNET ANALYSIS                                        │
│ ──────────────────────                                        │
│ Model: claude-sonnet-4-20250514 (higher capability for        │
│        strategic analysis vs haiku for individual scoring)    │
│                                                               │
│ Output JSON:                                                  │
│ {                                                             │
│   "patterns_identified": [...],                               │
│   "suggested_disqualifiers": [                                │
│     { "rule": "Requires agency experience",                   │
│       "rationale": "7 of 12 rejections had this",            │
│       "jobs_affected": 7 }                                    │
│   ],                                                          │
│   "scoring_adjustments": [...],                               │
│   "working_well": [...]                                       │
│ }                                                             │
└──────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│ EMAIL HTML REPORT                                             │
│ ─────────────────                                             │
│ Styled report with:                                           │
│ - Summary                                                     │
│ - Suggested new disqualifiers (highlighted)                   │
│ - Scoring adjustments                                         │
│ - Pattern breakdown                                           │
│ - What's working well                                         │
└──────────────────────────────────────────────────────────────┘
```

### Feedback Loop - Applied

**Goal**: Calibrate scoring by analyzing what made jobs worth applying to, ensuring good opportunities aren't scored too low.

```
Schedule (Weekly Mon 9:30am)
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│ QUERY APPLIED JOBS                                            │
│ ──────────────────                                            │
│ Filter: Review Status = 'Applied'                             │
│         Date Found >= 7 days ago                              │
│ + Calculate score statistics: min, max, avg, median          │
└──────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│ CLAUDE SONNET CALIBRATION ANALYSIS                            │
│ ──────────────────────────────────                            │
│ Output JSON:                                                  │
│ {                                                             │
│   "score_distribution": { min, max, average, median },        │
│   "calibration_issues": [                                     │
│     { "issue": "Builder roles at Series B scoring low",       │
│       "example_jobs": ["Head of CX at Acme"],                │
│       "suggested_fix": "Increase Series B builder bonus" }   │
│   ],                                                          │
│   "new_positive_signals": [                                   │
│     { "signal": "AI-native company",                          │
│       "suggested_points": 5 }                                 │
│   ],                                                          │
│   "working_well": [...]                                       │
│ }                                                             │
└──────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│ EMAIL HTML REPORT                                             │
│ ─────────────────                                             │
│ - Score distribution stats                                    │
│ - Calibration issues (PRIORITY - highlighted red)            │
│ - New positive signals to add (highlighted green)             │
│ - Positive signals found                                      │
│ - What's working well                                         │
└──────────────────────────────────────────────────────────────┘
```

### Why Claude Sonnet vs Haiku?

| Use Case | Model | Rationale |
|----------|-------|-----------|
| Individual job scoring | Haiku | High volume, simple eval, cost-effective |
| Weekly pattern analysis | Sonnet | Complex reasoning across multiple jobs, strategic recommendations |

---

## Cross-Source Deduplication

### Purpose

Prevent duplicate evaluations when the same job/company appears from multiple sources (e.g., LinkedIn email alert + Work at a Startup scraper + VC portfolio). This saves Claude API costs and keeps records clean.

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           DEDUP CHECK SUBWORKFLOW                                │
│                                                                                  │
│  Input: { company, title, source, recordType, _originalJobData }                │
│         │                                                                        │
│         ▼                                                                        │
│  ┌──────────────────┐                                                           │
│  │ Generate Key     │  job:acme:headofcx  or  company:acme                      │
│  │ (normalize)      │  Lowercase, remove non-alphanumeric, trim                 │
│  └────────┬─────────┘                                                           │
│           │                                                                      │
│           ├──────────────────────┐                                               │
│           ▼                      ▼                                               │
│  ┌──────────────────┐   ┌──────────────────┐                                    │
│  │ Query Airtable   │   │ Pass Through     │  (ensures data flows even if       │
│  │ Seen Opps        │   │ (NoOp)           │   Airtable returns no results)     │
│  └────────┬─────────┘   └────────┬─────────┘                                    │
│           │                      │                                               │
│           └──────────┬───────────┘                                               │
│                      ▼                                                           │
│           ┌──────────────────┐                                                  │
│           │ Merge Results    │                                                  │
│           └────────┬─────────┘                                                  │
│                    ▼                                                            │
│           ┌──────────────────┐                                                  │
│           │ Check Result     │  Compare keys, determine isDuplicate             │
│           │ (Code node)      │  Preserve _originalJobData in output             │
│           └────────┬─────────┘                                                  │
│                    │                                                            │
│  Output: { isDuplicate, key, existingRecordId, _originalJobData }              │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                          DEDUP REGISTER SUBWORKFLOW                              │
│                                                                                  │
│  Input: { key, company, title, source, recordType, airtableRecordId }           │
│         │                                                                        │
│         ▼                                                                        │
│  ┌──────────────────┐                                                           │
│  │ Create Seen      │  Airtable create in Seen Opportunities table              │
│  │ Record           │  Fields: Key, Company, Title, Record Type,                │
│  └────────┬─────────┘          First Source, All Sources, First Seen,           │
│           │                    Job Record ID, Company Record ID                  │
│           ▼                                                                      │
│  ┌──────────────────┐                                                           │
│  │ Confirm          │  Return { registered: true, seenRecordId }                │
│  │ Registration     │                                                           │
│  └──────────────────┘                                                           │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Integration in Pipelines

**Job Evaluation Pipeline v2**:
```
Trigger → Fetch Profile → Prepare Dedup Check → Dedup Check →
    IF: Is Duplicate?
        ├─ Yes → Skip Duplicate (return early)
        └─ No → Restore Job Data → [evaluation chain] → Airtable Upsert →
                Prepare Dedup Register → Dedup Register → Done
```

**Enrich & Evaluate Pipeline v2**:
```
Trigger → Prepare Dedup Check → Dedup Check (Cross-Source) →
    IF: Is Duplicate?
        ├─ Yes → Skip Duplicate
        └─ No → [enrichment & evaluation chain] → Airtable Upsert →
                IF: Disqualified?
                    ├─ Yes → Dedup Register (Disqualified)
                    └─ No → Dedup Register (Evaluated)
```

### Key Generation

| Record Type | Key Format | Example |
|-------------|------------|---------|
| Job | `job:{normalized_company}:{normalized_title}` | `job:acme:headofcx` |
| Company | `company:{normalized_company}` | `company:acme` |

**Normalization**: `str.toLowerCase().replace(/[^a-z0-9]/g, '').trim()`

### Seen Opportunities Table Schema

| Field | Type | Description |
|-------|------|-------------|
| Key | Text (Primary) | Normalized dedup key |
| Company | Text | Original company name |
| Title | Text | Original job title (empty for companies) |
| Record Type | Select | `job` or `company` |
| First Source | Text | First source to discover this |
| All Sources | Text | Comma-separated list of all sources |
| First Seen | DateTime | Timestamp of first discovery |
| Job Record ID | Text | Airtable record ID in Job Listings |
| Company Record ID | Text | Airtable record ID in Funding Alerts |

### Feedback Loop Output → Lens Updates

The email reports provide **suggestions only**. Human review decides which recommendations to implement:

1. **Read weekly reports** (Monday morning)
2. **Evaluate suggestions** against real-world context
3. **Update Tide Pool Agent Lens** on GitHub if approved
4. **Changes propagate** to all workflows (lens fetched at runtime)

```
Feedback Report                    Tide Pool Agent Lens (GitHub)
      │                                      │
      │  "Add 'agency experience'            │
      │   as auto-disqualifier"              │
      │                                      │
      └────── Human Review ──────────────────┤
                                             │
                                   ┌─────────▼─────────┐
                                   │ ## Auto-Disqualifiers
                                   │ - PE-backed        │
                                   │ - 1000+ employees  │
                                   │ + Agency experience│ ← Added
                                   └───────────────────┘
```

---

## Scoring Framework

### 100-Point System

| Category | Points | Criteria |
|----------|--------|----------|
| **Company Stage & Fit** | 0-50 | Pre-A: 50, Series A: 40, Series B: 25, Series C: 10, Later: 0 |
| **Role Type** | 0-30 | Builder: 30, Hybrid: 15, Maintainer: 0 |
| **Mission Alignment** | 0-20 | Target sector: 20, Adjacent: 10, Neutral: 5, Misaligned: 0 |

### Bonuses & Penalties

| Signal | Points |
|--------|--------|
| VC-backed | +10 |
| Recently founded (≤3 years) | +10 |
| PE-backed | -50 (auto-skip) |
| 200+ employees | -20 |
| Founded before 2018 | -15 |
| Series C or later | -20 |

### Decision Thresholds

| Score | Classification | Action |
|-------|----------------|--------|
| 80-100 | STRONG FIT | Apply immediately |
| 60-79 | GOOD FIT | Research thoroughly |
| 40-59 | MARGINAL | Only if exceptional |
| <40 | SKIP | Do not pursue |

---

## API Dependencies

| Service | Purpose | Rate Limit | Cost |
|---------|---------|------------|------|
| **Anthropic Claude API** | Job fit scoring | ~1 req/30s | ~$0.001/job |
| **Brave Search API** | Company enrichment | 2,000/month free | Free tier |
| **Gmail API** | Email fetching/labeling | Generous | Free |
| **Airtable API** | Data storage | 5 req/sec | Free tier |
| **Browserless.io** | Headless scraping | Usage-based | ~$0.01/session |
| **GitHub Raw** | Profile hosting | Generous | Free |

---

## Configuration

### Required Credentials (Airtable Config table)

| Key | Description |
|-----|-------------|
| `ANTHROPIC_API_KEY` | Claude API authentication |
| `BROWSERLESS_TOKEN` | Headless browser service |
| `YC_USER` | Work at a Startup login |
| `YC_PASSWORD` | Work at a Startup login |

### n8n Credentials

| Credential Type | Used By |
|-----------------|---------|
| Gmail OAuth2 | Email Parser |
| Airtable Token | All workflows |
| HTTP Header Auth (Brave) | Enrichment nodes |

---

## File Inventory

| File | Version | Description |
|------|---------|-------------|
| `Job Alert Email Parser v3-35.json` | v3-35 | Email-based job aggregation (10 sources) |
| `Work at a Startup Scraper v12.json` | v12 | YC/Costanoa web scraping |
| `Indeed Job Scraper v4.json` | v4 | Indeed direct scraping |
| `Job Evaluation Pipeline v2.json` | v2 | Shared subworkflow for job evaluation (with JD fetching + dedup) |
| `Enrich & Evaluate Pipeline v2.json` | v2 | Shared subworkflow for company enrichment + evaluation (with dedup) |
| `Dedup Check Subworkflow.json` | v1 | Cross-source deduplication lookup |
| `Dedup Register Subworkflow.json` | v1 | Cross-source deduplication registration |
| `vc-portfolio-scraper-v26-enriched.json` | v26 | Enterprise/generalist VC mining |
| `VC Scraper - Healthcare.json` | v25 | Healthcare-focused VC mining |
| `VC Scraper - Climate Tech.json` | v23 | Climate-focused VC mining |
| `VC Scraper - Social Justice.json` | v24 | Social justice-focused VC mining |
| `VC Scraper - Micro-VC v6.json` | v6 | Micro-VC mining (Pear, Floodgate, Afore, Unshackled, 2048) |
| `Feedback Loop - Not a Fit.json` | v1 | Weekly pattern analysis for rejected jobs |
| `Feedback Loop - Applied.json` | v1 | Weekly calibration analysis for applied jobs |

**Note:** All VC scrapers use the shared `Enrich & Evaluate Pipeline.json` subworkflow. Job workflows use `Job Evaluation Pipeline.json`.

---

## Version History

| Date | Change |
|------|--------|
| 2026-02-26 | Added cross-source deduplication (Dedup Check + Dedup Register subworkflows) |
| 2026-02-26 | Updated Job Evaluation Pipeline to v2 with dedup integration |
| 2026-02-26 | Updated Enrich & Evaluate Pipeline to v2 with dedup integration |
| 2026-02-26 | Added Seen Opportunities table for dedup tracking |
| 2026-02-24 | Added Feedback Loop - Not a Fit (weekly pattern analysis) |
| 2026-02-24 | Added Feedback Loop - Applied (weekly calibration analysis) |
| 2026-02-24 | Added Job Evaluation Pipeline with JD fetching |
| 2026-02-24 | Added VC Scraper - Micro-VC v6 (Pear, Floodgate, Afore, Unshackled, 2048) |
| 2026-02-23 | Refactored all VC scrapers to use shared Enrich & Evaluate Pipeline subworkflow |
| 2026-02-23 | Healthcare v24: Added Cade Ventures, Hustle Fund (health filter) |
| 2026-02-23 | Enterprise v22: Added K9 Ventures, Precursor, M25, GoAhead Ventures |
| 2026-02-23 | v6: Standardized evaluation sub-routine across all workflows |
| 2026-02-23 | v3-32: Removed Underdog.io source |
| 2026-02-22 | Updated all workflows to Claude Haiku 4.5 |
| 2026-02 | v3-31: Added zombie company detection |

---

*Last updated: February 2026*
