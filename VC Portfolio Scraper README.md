# VC Portfolio Scraper v21

An n8n workflow that automatically scrapes portfolio companies from mission-aligned venture capital firms, enriches them with company data via Brave Search, evaluates fit using the Customer Journey Leader framework via a shared subworkflow, and adds them to Airtable for job search tracking.

## What's New in v21

- **Shared Evaluation Subworkflow**: All scrapers now call a single "Evaluate Company Subworkflow" instead of inline evaluation logic
- **evaluation-config.json**: Single source of truth for scoring rules, disqualifiers, and the Customer Journey Leader framework
- **Tide Pool Governance**: evaluation-config.json links to tide-pool-agent-lens.md as the "north star" for identity and values
- **Three Questions Framework**: APPLY decisions now include Tide Pool's three questions check (fills pool, sincere, flourishing)

## Features

- **Scrapes portfolio pages from 14 VC firms** using Browserless, HTTP, and API methods
- **Deduplicates** against existing Airtable records
- **Brave Search enrichment** for each company:
  - Employee count
  - Funding stage (Pre-Seed through Series F+, Public/IPO)
  - Total funding amount
  - PE/VC backer detection
  - Founded year
  - Acquisition status
- **Auto-disqualification** based on enrichment data:
  - PE-backed companies (checked FIRST - strongest signal)
  - 500+ employees
  - $200M+ funding
  - Public/IPO companies
  - Acquired companies
  - Founded before 2017
  - Series D/E/F+ (late stage)
- **Customer Journey Leader evaluation** via shared subworkflow:
  - Score (0-80) across 8 dimensions
  - Sector match classification (target/adjacent/unrelated)
  - CS hire likelihood (high/medium/low/unlikely)
  - Product type detection
  - Three Questions check for APPLY candidates
- **Status derived from score**: APPLY (50+), WATCH (35-49), PASS (<35)
- **Automated scheduling** (Mon/Thu at 8am)

## Supported VCs

| VC Firm | Method | Focus |
|---------|--------|-------|
| Unusual Ventures | Browserless | Enterprise, B2B |
| First Round Capital | Sanity CMS API | Seed stage |
| Essence VC | HTTP + HTML parsing | Early stage |
| Costanoa Ventures | Sitemap XML | Enterprise |
| Khosla Ventures | Browserless | Climate, cleantech, healthcare |
| Kapor Capital | Sitemap XML | Social impact, diversity |
| WhatIf Ventures | Browserless | Healthcare |
| WXR Fund | HTTP + HTML parsing | XR/spatial computing |
| Leadout Capital | Browserless | Healthcare, femtech |
| Golden Ventures | HTTP + URL parsing | Canadian early-stage |
| Notable Capital | Browserless | Global, early-growth |
| Headline | Browserless | Global fintech/enterprise |
| Pioneer Square Labs | HTTP + URL parsing | Seattle-based |
| Trilogy Equity Partners | HTTP + HTML parsing | Seattle enterprise/consumer |

## Customer Journey Leader Scoring Framework

**Scoring (80 points max, 8 dimensions x 10 pts each):**

| Dimension | 10 pts | 7 pts | 4 pts | 0 pts |
|-----------|--------|-------|-------|-------|
| Build Opportunity | 0-to-1 first hire | Small team (1-3) | Scaling existing | PE optimization |
| Company Stage | Seed/Series A | Series B | Series C | Series D+/PE |
| Company Size | 10-30 employees | 30-50 | 50-100 | 500+ |
| Title Level | SVP/VP/Head | Director | Sr Manager | Manager |
| Sector Fit | Healthcare/Life Sci | Dev Tools | Tech B2B SaaS | Mismatch |
| Compensation | $150K+ | $140-150K | $125-140K | <$110K |
| Technical Complexity | APIs/clinical/data | Enterprise SaaS | Mid-market | Non-technical |
| Customer Journey Scope | Full post-sale | 2-3 areas | Narrow support | Renewals-focused |

**Output Buckets:**
- **APPLY** (50+): Immediate action, apply within 48 hours
- **WATCH** (35-49): Add to watch list, review monthly
- **PASS** (<35 or disqualified): No action needed

## Requirements

- n8n (Cloud or self-hosted)
- Browserless.io account (for JS-rendered pages)
- Brave Search API key (for company enrichment)
- Anthropic API key (for Claude evaluation)
- Airtable base with "Funding Alerts" table

## Airtable Schema

Required fields:
| Field | Type | Description |
|-------|------|-------------|
| Company Name | Single line text | Primary field |
| Company URL | URL | Company website |
| Company Description | Long text | From VC portfolio |
| VC Firm | Single line text | Source VC |
| Status | Single select | Apply, Monitor, Research, Skip, Auto-Disqualified |
| Next Steps | Single select | Apply Now, Watch for Jobs, Research More, Skip |
| Tide-Pool Score | Number | 0-80 evaluation score |
| Sector Match | Single select | target, adjacent, unrelated, unknown |
| CS Hire Likelihood | Single line text | high, medium, low, unlikely |
| Product Type | Single line text | high-touch enterprise, mid-market, etc. |
| Summary | Long text | AI-generated evaluation summary |
| Stage | Single line text | Funding stage |
| Total Funding | Single line text | e.g., "$50M" |
| Employee Count | Number | From Brave Search |
| PE Backed | Checkbox | Private equity backed |
| Founded Year | Number | Year founded |
| Disqualify Reasons | Long text | Auto-disqualification reasons |
| Source | Single line text | VC Firm name |

## Workflow Architecture (v21)

```
Schedule Trigger (Mon/Thu 8am)
    |
[14 VC Scrapers in parallel] --> Merge --> Dedup Against Existing
    |
Build Search Query --> Brave Search Company --> Parse Enrichment
    |
IF: Auto-Disqualify
    | (true)                         | (false)
Airtable: Auto-Disqualified     Execute Evaluate Subworkflow
                                     |
                                Airtable: Create Evaluated Record
```

**Evaluate Company Subworkflow (called by all scrapers):**
```
Execute Workflow Trigger (receives company data)
    |
Parse Input --> Check Disqualifiers
    |
IF: Disqualified
    | (yes)              | (no)
Format PASS         Fetch Tide Pool Profile
                         |
                    Build Evaluation Prompt
                         |
                    Evaluate via Anthropic API
                         |
                    Parse Evaluation (scores, three questions, summary)
                         |
                    Return to parent workflow
```

## Setup

### Option 1: v21 Workflows (Recommended)

1. Import `Evaluate Company Subworkflow.json` into n8n first
2. Note the workflow ID of the imported subworkflow
3. Import the v21 scraper workflows:
   - `VC Scraper - Healthcare v21.json`
   - `VC Scraper - Climate Tech v21.json`
   - `VC Scraper - Social Justice v21.json`
4. In each v21 workflow, configure the "Execute Evaluate Subworkflow" node:
   - Set the workflow ID to match your imported subworkflow
5. Configure credentials:
   - Browserless API token (Header Auth)
   - Brave Search API key (Header Auth with `X-Subscription-Token`)
   - Anthropic API key (Header Auth with `x-api-key`)
   - Airtable API token
6. Test run the workflow
7. Enable the schedule trigger

### Option 2: v20 Workflows (Legacy)

1. Import `vc-portfolio-scraper-v20-enriched.json` into n8n
2. Configure credentials (same as above)
3. Note: v20 has inline evaluation logic, not using shared subworkflow

## Files

### Configuration
- `evaluation-config.json` - Single source of truth for evaluation logic (Customer Journey Leader framework)

### Subworkflow
- `Evaluate Company Subworkflow.json` - Shared evaluation logic called by all v21 scrapers

### v21 Workflows (Current - use shared subworkflow)
- `VC Scraper - Healthcare v21.json`
- `VC Scraper - Climate Tech v21.json`
- `VC Scraper - Social Justice v21.json`

### v20 Workflows (Legacy - inline evaluation)
- `vc-portfolio-scraper-v20-enriched.json`
- `VC Scraper - Healthcare.json`
- `VC Scraper - Climate Tech.json`
- `VC Scraper - Social Justice.json`

## Version History

- **v21**: Refactored to use shared "Evaluate Company Subworkflow". Added evaluation-config.json as single source of truth. Added Three Questions framework from Tide Pool. Updated scoring to Customer Journey Leader framework (80 pts max).
- **v20**: Major upgrade - Added Brave Search enrichment, auto-disqualification logic, Tide Pool scoring framework (0-100), sector match detection, score-based status derivation.
- **v19**: Added Brave Search enrichment (employee count, funding stage, PE detection)
- **v18**: Added 8 new VCs from career coach recommendations
- **v17**: Added Khosla Ventures and Kapor Capital
- **v16**: Initial version with 4 VCs

## Related Workflows

- **VC Scraper - Healthcare v21**: Flare Capital, 7wireVentures, Oak HC/FT
- **VC Scraper - Climate Tech v21**: Congruent Ventures, Prelude Ventures, Lowercarbon Capital
- **VC Scraper - Social Justice v21**: Backstage Capital, Harlem Capital, Collab Capital

## Governance

The evaluation logic follows a governance hierarchy:

1. **tide-pool-agent-lens.md** (North Star) - Identity, values, essence, "why"
2. **evaluation-config.json** (Derived) - Tactical evaluation logic, "how"
3. **n8n workflows** (Execution) - Implementation

When in conflict, the north star governs. See `evaluation-config.json` for the full `_governance` section.
