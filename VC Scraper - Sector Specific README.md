# VC Scraper - Sector Specific Workflows

Four n8n workflows that scrape portfolio companies from sector-focused venture capital firms.

**Current Versions:**
- Healthcare: v24 (added Cade Ventures, Hustle Fund)
- Enterprise/Generalist: v22 (added K9, Precursor, M25, GoAhead)
- Climate Tech: v22
- Social Justice: v22

**All workflows now use the shared `Enrich & Evaluate Pipeline.json` subworkflow** via Execute Workflow node for:
- Airtable deduplication
- Brave Search company enrichment
- Claude AI evaluation (Haiku 4.5)
- Airtable record creation

## Workflows

### VC Scraper - Healthcare v24
**Schedule:** Tuesday/Friday at 8am

| VC Firm | Method | Focus |
|---------|--------|-------|
| WhatIf Ventures | Browserless | Healthcare innovation |
| Leadout Capital | Browserless | Healthcare/femtech |
| Flare Capital | Static list | Healthcare IT |
| 7wireVentures | Static list | Digital health |
| Oak HC/FT | Static list | Healthcare & fintech |
| **Cade Ventures** | Browserless | Health tech (Ro, Function Health) |
| **Hustle Fund** | Static list | Health/wellness filter (Rupa Health) |

### VC Scraper - Climate Tech v22
**Schedule:** Monday/Thursday at 8am

| VC Firm | Method | Focus |
|---------|--------|-------|
| Khosla Ventures | Browserless | Climate/energy |
| Congruent Ventures | Static list | Sustainability |
| Prelude Ventures | Static list | Climate solutions |
| Lowercarbon Capital | Static list | Climate tech |

### VC Scraper - Social Justice v22
**Schedule:** Wednesday/Saturday at 8am

| VC Firm | Method | Focus |
|---------|--------|-------|
| Kapor Capital | HTTP (Sitemap) | Social impact |
| Backstage Capital | Static list | Underrepresented founders |
| Harlem Capital | Static list | Diverse founders |
| Collab Capital | Static list | Black founders |

### VC Scraper - Enterprise & Generalist v22
**Schedule:** Monday/Thursday at 8am

| VC Firm | Method | Focus |
|---------|--------|-------|
| Unusual Ventures | Browserless | Enterprise software |
| First Round Capital | HTTP (Sanity API) | Seed-stage generalist |
| Essence VC | HTTP | Early-stage generalist |
| Costanoa Ventures | HTTP (Sitemap) | Enterprise/B2B |
| WXR Fund | HTTP | XR/spatial computing |
| Golden Ventures | HTTP | Canadian early-stage |
| Notable Capital | Browserless | Enterprise/consumer |
| Headline | Browserless | Global generalist |
| Pioneer Square Labs | HTTP | Seattle-based |
| Trilogy Equity Partners | Browserless | Seattle enterprise |
| **K9 Ventures** | Static HTML | Enterprise SaaS (Twilio, Carta, Auth0) |
| **Precursor Ventures** | Sitemap (343 co.) | B2B software (Carrot Fertility, Modern Health) |
| **M25** | Sitemap (200+ co.) | Midwest HealthTech/FinTech/Vertical SaaS |
| **GoAhead Ventures** | Browserless | Generalist (Paratus Health, HackerRank) |

## Shared Features

All v22 workflows include:
- **Real scraping** using Browserless and HTTP where available
- **Static lists** for VCs without scrapable portfolios
- **Shared Pipeline**: Calls "Enrich & Evaluate Pipeline" for:
  - Airtable deduplication
  - Brave Search enrichment (employee count, funding, PE detection)
  - Auto-disqualification (PE-backed, 500+ employees, $200M+ funding)
  - Claude API evaluation (Customer Journey Leader score 0-80)
  - Three Questions check for APPLY candidates
  - Score-based buckets (APPLY/WATCH/PASS)
  - Airtable record creation

## Workflow Architecture

### Current Architecture (All scrapers use shared pipeline)

```
Schedule Trigger
    |
[Scraping Nodes] --> [Parse Nodes] --> Merge --> Combine All VCs --> Filter Valid
    |                                                                     |
[Static Data Node] ----------------------------------------->     Execute Enrich &
                                                                  Evaluate Pipeline
                                                                         |
                                                                         v
                                                          ┌─────────────────────────────┐
                                                          │ SHARED SUBWORKFLOW          │
                                                          │ - Airtable dedup            │
                                                          │ - Brave Search enrichment   │
                                                          │ - Auto-disqualify check     │
                                                          │ - Claude AI evaluation      │
                                                          │ - Airtable record creation  │
                                                          └─────────────────────────────┘
```

Each workflow:
1. Triggers on schedule
2. Runs scrapers in parallel (Browserless/HTTP/Sitemap)
3. Parses responses to extract company data
4. Merges with static company lists
5. Combines all companies from all VC sources
6. **Calls shared `Enrich & Evaluate Pipeline.json` subworkflow** for:
   - Deduplication against Airtable
   - Brave Search company enrichment
   - Auto-disqualification (PE-backed, 500+ employees, $200M+ funding)
   - Claude AI scoring (Haiku 4.5)
   - Airtable record creation

## Setup

### Setup Steps

1. **Import the pipeline subworkflow first:**
   - Import `Enrich & Evaluate Pipeline.json` into n8n
   - **Configure credentials ONCE in the pipeline:**
     - Airtable API token (3 nodes use this)
     - Brave Search API (Header Auth with `X-Subscription-Token`)
     - Anthropic API Key (Header Auth with `x-api-key`)
   - **Note the workflow ID** (you'll need this for each scraper)

2. **Import the sector workflows:**
   - `VC Scraper - Healthcare.json` (v24)
   - `VC Scraper - Climate Tech.json` (v22)
   - `VC Scraper - Social Justice.json` (v22)
   - `vc-portfolio-scraper-v20-enriched.json` (Enterprise v22)

3. **Configure each workflow:**
   - Open the "Execute Enrich & Evaluate Pipeline" node
   - Select the imported pipeline workflow (or set workflow ID)
   - Configure **Browserless credentials** for workflows that use them:
     - Healthcare v24: Browserless (for WhatIf, Leadout, Cade)
     - Climate Tech v22: Browserless (for Khosla)
     - Enterprise v22: Browserless (for Unusual, Notable, Headline, Trilogy, GoAhead)
   - Social Justice v22 uses HTTP/Sitemap only (no Browserless needed)

4. **Test and enable the schedule triggers**

## Files

### Current (All use shared pipeline subworkflow)
- `Enrich & Evaluate Pipeline.json` - Shared subworkflow: dedup, Brave enrichment, Claude AI (Haiku 4.5), Airtable
- `VC Scraper - Healthcare.json` (v24) - 7 VCs: WhatIf, Leadout, Cade + static lists
- `VC Scraper - Climate Tech.json` (v22) - 4 VCs: Khosla scraping + static lists
- `VC Scraper - Social Justice.json` (v22) - 4 VCs: Kapor sitemap + static lists
- `vc-portfolio-scraper-v20-enriched.json` (v22) - 14 VCs: Enterprise/generalist scrapers

### Configuration
- `evaluation-config.json` - Single source of truth for evaluation rules

## VC Distribution (v22)

The 14 VCs from the original v20 scraper have been redistributed:

| Sector | Scraped VCs | Static VCs |
|--------|-------------|------------|
| Healthcare | WhatIf, Leadout | Flare, 7wire, Oak |
| Climate Tech | Khosla | Congruent, Prelude, Lowercarbon |
| Social Justice | Kapor | Backstage, Harlem, Collab |
| Enterprise & Generalist | Unusual, First Round, Essence, Costanoa, WXR, Golden, Notable, Headline, PSL, Trilogy | - |

## Notes

- All workflows write to the same "Funding Alerts" Airtable table
- **Pipeline credentials** (Airtable, Brave, Anthropic) configured **once** in the `Enrich & Evaluate Pipeline.json` subworkflow
- **Browserless credentials** must be configured in each workflow that uses headless scraping
- Rate limited to 30s between Anthropic API calls to avoid rate limits
- Brave Search limited to 1.5s between calls
- Claude model: `claude-haiku-4-5-20250314`

## Architecture Benefits

The current architecture using the shared `Enrich & Evaluate Pipeline.json` subworkflow provides:

| Benefit | Description |
|---------|-------------|
| **Single credential config** | Airtable, Brave, Anthropic credentials configured once in pipeline |
| **Consistent evaluation** | All scrapers use identical Claude AI scoring logic |
| **Easy updates** | Update pipeline once, all scrapers benefit |
| **Reduced node count** | Each scraper has ~28-60 nodes instead of ~40-74 |
| **Simple VC additions** | Just add scraper/parse nodes, pipeline handles the rest |

## Version History

- **Feb 2026 (v24/v22)**: Refactored all 4 VC scrapers to use shared Enrich & Evaluate Pipeline subworkflow. Healthcare v24, Enterprise v22.
- **Feb 2026**: Added K9 Ventures, Precursor, M25, GoAhead (Enterprise). Added Cade Ventures, Hustle Fund (Healthcare).
- **Feb 2026 (v22)**: Full pipeline subworkflow with Brave enrichment and Claude AI evaluation.
- **Feb 2026**: Updated all workflows to Claude Haiku 4.5.
- **Jan 2026**: Initial versions with simple classification
