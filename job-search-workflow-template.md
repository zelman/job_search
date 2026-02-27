# Job Search Automation Workflow Template

> **Based on the Tide Pool System** - A production-tested job search automation platform using n8n, Claude AI, and Airtable.

---

## Quick Configuration

Fill in these values first:

```yaml
# Your Details
{{YOUR_NAME}}: "Your Name"
{{TARGET_ROLE}}: "VP/Head of Customer Success"
{{YEARS_EXPERIENCE}}: "10+"

# Infrastructure
{{N8N_INSTANCE}}: "n8n Cloud or self-hosted"
{{AIRTABLE_BASE_ID}}: "appXXXXXXXXXXXXXX"

# APIs
{{ANTHROPIC_API_KEY}}: "sk-ant-..."  # Claude API
{{BRAVE_API_KEY}}: "BSA..."          # Brave Search (free tier: 2000/month)
{{BROWSERLESS_TOKEN}}: "..."         # For JS-heavy sites

# Scoring Thresholds
{{STRONG_FIT_THRESHOLD}}: 80
{{GOOD_FIT_THRESHOLD}}: 60
{{MINIMUM_SCORE}}: 40
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           JOB SOURCE LAYER                                   │
├─────────────────┬─────────────────┬─────────────────┬───────────────────────┤
│  Email Alerts   │   VC Portfolio  │  Direct Scrape  │   Manual/Other        │
│  (Gmail API)    │   Scrapers      │  (YC, etc.)     │                       │
└────────┬────────┴────────┬────────┴────────┬────────┴───────────────────────┘
         │                 │                 │
         ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     CROSS-SOURCE DEDUPLICATION LAYER                         │
│  • Prevents duplicate evaluations across all sources                         │
│  • Key: job:{normalized_company}:{normalized_title}                          │
│  • Saves API costs by skipping already-seen opportunities                    │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ENRICHMENT & EVALUATION LAYER                         │
├─────────────────────────────────────────────────────────────────────────────┤
│  • Brave Search API (company data: funding, employees, investors)            │
│  • Job Description Fetching (HTTP + Browserless fallback)                    │
│  • Claude AI Scoring (using your personal "Agent Lens")                      │
│  • Builder vs. Maintainer classification                                     │
│  • Auto-disqualification rules                                               │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           STORAGE & WORKFLOW LAYER                           │
├─────────────────────────────────────────────────────────────────────────────┤
│  Airtable Base                                                               │
│  ├── Job Listings (scored opportunities)                                     │
│  ├── Funding Alerts (VC portfolio companies)                                │
│  ├── Seen Opportunities (deduplication tracking)                            │
│  └── Config (API keys, credentials)                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│  Review Status: New → Reviewing → Applied / Not a Fit → Archived             │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FEEDBACK LOOP LAYER                                │
│  • Weekly "Not a Fit" analysis → suggests new disqualifiers                  │
│  • Weekly "Applied" analysis → calibrates scoring                            │
│  • AI-generated reports with actionable recommendations                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Part 1: Your Agent Lens (Personal Profile)

> The most important piece. This document tells the AI who you are and what you want.

### Agent Lens Template

```markdown
# {{YOUR_NAME}} - Agent Lens

## Core Positioning
<!-- [CUSTOMIZE] Your career philosophy and what makes you unique -->
{{YOUR_POSITIONING_STATEMENT}}

## Target Profile

### Role
- **Primary**: {{TARGET_ROLE_1}}
- **Secondary**: {{TARGET_ROLE_2}}
- **Title Flexibility**: {{TITLE_NOTES}}

### Company Stage (Critical)
<!-- [CUSTOMIZE] This drives 50% of scoring -->
| Stage | Fit | Points |
|-------|-----|--------|
| Pre-Series A (0-50 people) | Ideal | 50 |
| Series A (50-150 people) | Strong | 40 |
| Series B (150-300 people) | Good | 25 |
| Series C+ | Weak | 10 |
| Public/PE-backed | No | 0 |

### Role Type: Builder vs. Maintainer
<!-- [CUSTOMIZE] This is a key differentiator -->

**Builder Signals (Positive):**
- {{BUILDER_SIGNAL_1}}  # e.g., "build from scratch"
- {{BUILDER_SIGNAL_2}}  # e.g., "first hire"
- {{BUILDER_SIGNAL_3}}  # e.g., "define the playbook"

**Maintainer Signals (Negative):**
- {{MAINTAINER_SIGNAL_1}}  # e.g., "book of business"
- {{MAINTAINER_SIGNAL_2}}  # e.g., "existing team of 20"
- {{MAINTAINER_SIGNAL_3}}  # e.g., "proven playbook"

### Industries
- **Target**: {{TARGET_INDUSTRIES}}
- **Avoid**: {{AVOID_INDUSTRIES}}

### Compensation
- **Minimum Base**: {{MIN_SALARY}}
- **Equity**: {{EQUITY_PREFERENCE}}

### Location
- **Preferred**: {{LOCATION_PREFERENCE}}
- **Acceptable**: {{ACCEPTABLE_LOCATIONS}}

## Auto-Disqualifiers (Hard No)
<!-- [CUSTOMIZE] These result in immediate skip -->
- {{DISQUALIFIER_1}}  # e.g., "PE-backed company"
- {{DISQUALIFIER_2}}  # e.g., "1,000+ employees"
- {{DISQUALIFIER_3}}  # e.g., "$500M+ total funding"
- {{DISQUALIFIER_4}}  # e.g., "Fortune 500/Public company"
- {{DISQUALIFIER_5}}  # e.g., "Quota-carrying sales role"

## Scoring Framework (100 points)

| Category | Max Points | Criteria |
|----------|------------|----------|
| Company Stage & Fit | 50 | See stage table above |
| Role Type | 30 | Builder: 30, Hybrid: 15, Maintainer: 0 |
| Mission Alignment | 20 | Target sector: 20, Adjacent: 10, Neutral: 5 |

### Bonuses & Penalties
| Signal | Points |
|--------|--------|
| VC-backed | +10 |
| Recently founded (≤3 years) | +10 |
| PE-backed | -50 (auto-skip) |
| 200+ employees | -20 |

### Decision Thresholds
| Score | Action |
|-------|--------|
| 80-100 | STRONG FIT - Apply immediately |
| 60-79 | GOOD FIT - Research thoroughly |
| 40-59 | MARGINAL - Only if exceptional |
| <40 | SKIP |
```

---

## Part 2: n8n Workflow Structure

### Shared Subworkflows (DRY Principle)

Instead of duplicating evaluation logic, use shared subworkflows:

```
┌─────────────────────────────────────────────────────────────────┐
│  JOB EVALUATION PIPELINE (Subworkflow)                           │
├─────────────────────────────────────────────────────────────────┤
│  Trigger → Fetch Profile → Dedup Check →                         │
│    IF Duplicate? → Skip                                          │
│    IF New? → Brave Search → Fetch JD → Parse Enrichment →       │
│              Build Prompt → Claude API → Parse Response →        │
│              Airtable Upsert → Dedup Register                    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  COMPANY EVALUATION PIPELINE (Subworkflow)                       │
├─────────────────────────────────────────────────────────────────┤
│  Trigger → Dedup Check →                                         │
│    IF Duplicate? → Skip                                          │
│    IF New? → Brave Search → Parse Enrichment →                   │
│              Build Prompt → Claude API → Parse Response →        │
│              Airtable Upsert → Dedup Register                    │
└─────────────────────────────────────────────────────────────────┘
```

### Source Workflows Call Shared Pipelines

```
Email Parser ──────────┐
                       │
YC Scraper ────────────┼──→ Job Evaluation Pipeline
                       │
Other Job Sources ─────┘

Healthcare VC Scraper ─┐
                       │
Climate VC Scraper ────┼──→ Company Evaluation Pipeline
                       │
Other VC Scrapers ─────┘
```

---

## Part 3: Company Enrichment

### Brave Search Integration

```javascript
// Brave Search Company node
// GET https://api.search.brave.com/res/v1/web/search
// Query: "{Company}" funding series employees site:crunchbase.com OR site:pitchbook.com
```

### Enrichment Schema

```javascript
{
  employeeCount: number | null,      // Extracted from search results
  fundingStage: string | null,       // Pre-Seed, Seed, Series A/B/C/D+, Public
  totalFunding: number | null,       // In millions (e.g., 45 = $45M)
  isPEBacked: boolean,               // Private equity - auto-disqualifier
  isVCBacked: boolean,               // Venture capital - positive signal
  foundedYear: number | null,
  companyAge: number | null,
  autoDisqualifiers: string[],       // Reasons for automatic rejection
}
```

### PE Firm Detection

```javascript
// Include a list of PE firms to detect
const PE_FIRMS = [
  'vista equity', 'thoma bravo', 'kkr', 'blackstone', 'carlyle',
  'bain capital', 'tpg', 'apollo', 'warburg pincus', 'silver lake',
  'francisco partners', 'ares management', 'golden gate capital',
  // ... add more
];
```

### Auto-Disqualifier Rules

| Rule | Threshold | Rationale |
|------|-----------|-----------|
| PE-backed | Any PE investor | PE optimizes for cost-cutting |
| Employee count | ≥ 1,000 | Too large for builder role |
| Total funding | ≥ $500M | Late-stage, mature operations |
| Public company | IPO/NASDAQ/NYSE | Established, not startup |
| Zombie company | 7+ years + still Seed + <100 emp | Stalled growth |

---

## Part 4: Cross-Source Deduplication

### Why Dedup?

The same job can appear from multiple sources:
- LinkedIn email alert
- Work at a Startup scraper
- VC portfolio scraper

Without dedup, you pay for Claude API evaluation multiple times.

### Dedup Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  DEDUP CHECK SUBWORKFLOW                                         │
├─────────────────────────────────────────────────────────────────┤
│  Input: { company, title, source, recordType }                   │
│                                                                  │
│  1. Generate Key: job:{normalize(company)}:{normalize(title)}   │
│  2. Query Seen Opportunities table                               │
│  3. Return: { isDuplicate, existingRecordId, _originalJobData } │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  DEDUP REGISTER SUBWORKFLOW                                      │
├─────────────────────────────────────────────────────────────────┤
│  Input: { key, company, title, source, airtableRecordId }       │
│                                                                  │
│  1. Create record in Seen Opportunities table                    │
│  2. Return: { registered: true, seenRecordId }                  │
└─────────────────────────────────────────────────────────────────┘
```

### Seen Opportunities Table Schema

| Field | Type | Description |
|-------|------|-------------|
| Key | Text | Normalized dedup key |
| Company | Text | Company name |
| Title | Text | Job title (empty for companies) |
| Record Type | Select | job / company |
| First Source | Text | First source to discover |
| All Sources | Text | All sources (comma-separated) |
| First Seen | DateTime | First discovery timestamp |
| Job Record ID | Text | Link to Job Listings |
| Company Record ID | Text | Link to Funding Alerts |

---

## Part 5: Feedback Loops

### Weekly "Not a Fit" Analysis

```
Schedule (Weekly Monday 9am)
       │
       ▼
Query jobs marked "Not a Fit" in past 7 days
       │
       ▼
Send to Claude Sonnet for pattern analysis
       │
       ▼
Output:
{
  "patterns_identified": [...],
  "suggested_disqualifiers": [
    { "rule": "Requires agency experience", "jobs_affected": 7 }
  ],
  "scoring_adjustments": [...],
  "working_well": [...]
}
       │
       ▼
Email HTML report with recommendations
```

### Weekly "Applied" Calibration

```
Schedule (Weekly Monday 9:30am)
       │
       ▼
Query jobs marked "Applied" in past 7 days
       │
       ▼
Calculate score distribution (min, max, avg, median)
       │
       ▼
Send to Claude Sonnet for calibration analysis
       │
       ▼
Output:
{
  "calibration_issues": [
    { "issue": "Builder roles at Series B scoring too low" }
  ],
  "new_positive_signals": [
    { "signal": "AI-native company", "suggested_points": 5 }
  ]
}
       │
       ▼
Email HTML report with recommendations
```

### Why Claude Sonnet for Feedback?

| Use Case | Model | Rationale |
|----------|-------|-----------|
| Individual job scoring | Haiku | High volume, cost-effective |
| Weekly pattern analysis | Sonnet | Complex reasoning, strategic insights |

---

## Part 6: Airtable Schema

### Job Listings Table

| Field | Type | Description |
|-------|------|-------------|
| Job Title | Text | Role title |
| Company | Text | Company name |
| Location | Text | Work location |
| Source | Select | LinkedIn, Built In, YC, etc. |
| Job URL | URL | Link to posting (merge key) |
| Salary Info | Text | Compensation if available |
| Date Found | Date | Discovery date |
| Review Status | Select | New, Reviewing, Applied, Not a Fit, Archived |
| Tide-Pool Score | Number | 0-100 fit score |
| Tide-Pool Rationale | Long Text | AI explanation |
| Industry | Text | Company sector |
| Company Stage | Text | Funding stage |
| Role Type | Select | builder / maintainer / hybrid |
| Builder Evidence | Text | Positive signals found |
| Maintainer Evidence | Text | Negative signals found |
| Recommendation | Select | apply / research / skip |

### Funding Alerts Table (VC Companies)

Similar structure for company-level tracking from VC portfolio scrapers.

### Config Table

| Key | Purpose |
|-----|---------|
| ANTHROPIC_API_KEY | Claude AI scoring |
| BROWSERLESS_TOKEN | Headless browser scraping |
| BRAVE_API_KEY | Company enrichment |

---

## Part 7: Job Sources

### Email Alert Parsing

Parse job alert emails from multiple sources:

| Source | Parse Method |
|--------|--------------|
| LinkedIn | URL + text extraction |
| Indeed | URL + "at" pattern |
| Built In | HTML card structure |
| Wellfound | Job pattern + employee count |
| Himalayas | URL slug parsing |
| Google Careers | Careers URL parsing |

### VC Portfolio Scraping

Proactively mine investor portfolios:

| Category | Example VCs |
|----------|-------------|
| Healthcare | 7wireVentures, Oak HC/FT, Flare Capital |
| Climate Tech | Congruent, Prelude, Lowercarbon |
| Enterprise | First Round, Unusual Ventures, Costanoa |
| Social Justice | Kapor Capital, Backstage, Harlem |

### Direct Job Board Scraping

- Y Combinator Work at a Startup
- Costanoa Jobs
- Individual company career pages

---

## Part 8: API Costs

| Service | Purpose | Cost |
|---------|---------|------|
| Claude Haiku | Job scoring | ~$0.001/job |
| Claude Sonnet | Weekly analysis | ~$0.01/report |
| Brave Search | Company enrichment | Free (2000/month) |
| Browserless | JS-heavy scraping | ~$0.01/session |

**Monthly estimate for ~500 jobs/month**: ~$5-10

---

## Part 9: Quick Start Checklist

### Setup

- [ ] Create n8n instance (cloud or self-hosted)
- [ ] Create Airtable base with tables above
- [ ] Get Anthropic API key
- [ ] Get Brave Search API key (free tier)
- [ ] Get Browserless token (optional, for JS sites)

### Configuration

- [ ] Write your Agent Lens (personal profile)
- [ ] Host Agent Lens on GitHub (raw URL for fetching)
- [ ] Set up Gmail API connection for email parsing
- [ ] Configure Airtable credentials in n8n

### Workflows

- [ ] Create Job Evaluation Pipeline subworkflow
- [ ] Create Company Evaluation Pipeline subworkflow
- [ ] Create Dedup Check/Register subworkflows
- [ ] Create email parser workflow
- [ ] Create VC scraper workflows
- [ ] Create feedback loop workflows

### Testing

- [ ] Run email parser manually
- [ ] Verify jobs appear in Airtable with scores
- [ ] Check dedup prevents duplicates
- [ ] Review feedback loop reports

---

## Resources

- [n8n Documentation](https://docs.n8n.io/)
- [Airtable API](https://airtable.com/developers/web/api/introduction)
- [Anthropic Claude API](https://docs.anthropic.com/)
- [Brave Search API](https://brave.com/search/api/)
- [Browserless](https://browserless.io/)

---

## Template Version

- Version: 2.0
- Last Updated: February 2026
- Based on: Tide Pool Job Search Automation System

---

*This template is based on a production system processing 500+ jobs/month with 95%+ accuracy on fit scoring.*
