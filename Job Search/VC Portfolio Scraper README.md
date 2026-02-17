# VC Portfolio Scraper v20

An n8n workflow that automatically scrapes portfolio companies from mission-aligned venture capital firms, enriches them with company data via Brave Search, evaluates fit using the Tide Pool scoring framework via Claude AI, and adds them to Airtable for job search tracking.

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
  - PE-backed companies
  - 500+ employees
  - $200M+ funding
  - Public/IPO companies
  - Acquired companies
  - Founded before 2017
  - Series D/E/F+ (late stage)
- **Tide Pool evaluation** via Anthropic Claude API:
  - Score (0-100) based on company stage, sector match, and CS hire likelihood
  - Sector match classification (target/adjacent/unrelated)
  - CS hire likelihood (high/medium/low/unlikely)
  - Product type detection
  - Ops gap identification
- **Status derived from score**: Apply (70+), Monitor (50-69), Research (30-49), Skip (<30)
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

## Tide Pool Scoring Framework

**Scoring (100 points max):**
- Company Stage & Fit: up to 40 pts
  - Pre-Seed/Seed: 40 pts (ideal early builder)
  - Series A: 35 pts
  - Series B: 20 pts
  - Series C+: 5 pts
- Sector Match: up to 30 pts
  - Target sector (healthcare, climate, life sciences, education, audio/music, enterprise AI): 30 pts
  - Adjacent sector: 15 pts
  - Unrelated sector: 5 pts
- CS Hire Likelihood: up to 30 pts
  - B2B SaaS/Enterprise with high-touch product: 30 pts
  - Mid-market B2B: 20 pts
  - Consumer or self-serve: 10 pts

**Penalties:**
- PE-backed: -50 pts
- 200+ employees: -20 pts
- Founded before 2018: -15 pts
- Series C or later: -20 pts

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
| Tide-Pool Score | Number | 0-100 evaluation score |
| Sector Match | Single select | target, adjacent, unrelated, unknown |
| CS Hire Likelihood | Single line text | high, medium, low, unlikely |
| Product Type | Single line text | high-touch enterprise, mid-market, etc. |
| Ops Gap | Checkbox | Opportunity indicator |
| Summary | Long text | AI-generated evaluation summary |
| Stage | Single line text | Funding stage |
| Total Funding | Single line text | e.g., "$50M" |
| Employee Count | Number | From Brave Search |
| PE Backed | Checkbox | Private equity backed |
| Founded Year | Number | Year founded |
| Disqualify Reasons | Long text | Auto-disqualification reasons |
| First Seen Date | Date | When workflow first found company |
| Source | Single line text | VC Firm name |

## Workflow Architecture

```
Schedule Trigger (Mon/Thu 8am)
    ↓
[14 VC Scrapers in parallel] → Merge → Dedup Against Existing
    ↓
Build Search Query → Brave Search Company → Parse Enrichment
    ↓
IF: Auto-Disqualify
    ↓ (true)                    ↓ (false)
Airtable: Auto-Disqualified    IF: Needs Manual Research
                                    ↓ (false)
                               Fetch Tide Pool Profile
                                    ↓
                               Build Evaluation Prompt
                                    ↓
                               Evaluate via Anthropic API (30s rate limit)
                                    ↓
                               Parse Evaluation
                                    ↓
                               Airtable: Create Evaluated Record
```

## Setup

1. Import `vc-portfolio-scraper-v20-enriched.json` into n8n
2. Configure credentials:
   - Browserless API token (Header Auth)
   - Brave Search API key (Header Auth with `X-Subscription-Token`)
   - Anthropic API key (Header Auth with `x-api-key`)
   - Airtable API token
3. Create Airtable fields per schema above
4. Add single select options:
   - Status: Apply, Monitor, Research, Skip, Auto-Disqualified
   - Next Steps: Apply Now, Watch for Jobs, Research More, Skip
   - Sector Match: target, adjacent, unrelated, unknown
5. Test run the workflow
6. Enable the schedule trigger

## Files

- `vc-portfolio-scraper-v20-enriched.json` - Current version with Brave Search enrichment and Tide Pool evaluation
- `VC Scraper - Healthcare.json` - Healthcare-focused VCs (same evaluation logic)
- `VC Scraper - Climate Tech.json` - Climate/cleantech VCs (same evaluation logic)
- `VC Scraper - Social Justice.json` - Social impact VCs (same evaluation logic)

## Version History

- **v20**: Major upgrade - Added Brave Search enrichment, auto-disqualification logic, Tide Pool scoring framework (0-100), sector match detection, score-based status derivation. Replaced simple classification with comprehensive evaluation.
- **v19**: Added Brave Search enrichment (employee count, funding stage, PE detection)
- **v18**: Added 8 new VCs from career coach recommendations
- **v17**: Added Khosla Ventures and Kapor Capital
- **v16**: Initial version with 4 VCs

## Related Workflows

- **VC Scraper - Healthcare**: Flare Capital, 7wireVentures, Oak HC/FT, Digitalis, a16z Bio+Health, Healthworx
- **VC Scraper - Climate Tech**: Congruent Ventures, Prelude Ventures, Clean Energy Ventures, Lowercarbon Capital, Energy Impact Partners, DCVC
- **VC Scraper - Social Justice**: Kapor Capital, Backstage Capital, Harlem Capital, Impact America Fund, Collab Capital
