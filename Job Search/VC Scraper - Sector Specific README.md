# VC Scraper - Sector Specific Workflows

Four n8n workflows that scrape portfolio companies from sector-focused venture capital firms.

**v22 workflows** use the shared "Enrich & Evaluate Pipeline" with actual scraping logic from v20.

**v21 workflows** (legacy) use the shared "Evaluate Company Subworkflow" for evaluation only.

## Workflows

### VC Scraper - Healthcare v22
**Schedule:** Tuesday/Friday at 8am

| VC Firm | Method | Focus |
|---------|--------|-------|
| WhatIf Ventures | Browserless | Healthcare innovation |
| Leadout Capital | Browserless | Healthcare/femtech |
| Flare Capital | Static list | Healthcare IT |
| 7wireVentures | Static list | Digital health |
| Oak HC/FT | Static list | Healthcare & fintech |

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

### VC Scraper - Enterprise & Generalist v22 (NEW)
**Schedule:** Sunday at 8am

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

### v22 Architecture (Scraping + Pipeline)

```
Schedule Trigger
    |
[Scraping Nodes] --> [Parse Nodes] --> Merge --> Combine & Dedupe --> Filter Valid
    |                                                                     |
[Static Data Node] ----------------------------------------->        Execute Pipeline
```

Each workflow:
1. Triggers on schedule
2. Runs scrapers in parallel (Browserless/HTTP)
3. Parses responses to extract company data
4. Merges with static company lists
5. Deduplicates within workflow
6. Calls shared pipeline for enrichment + evaluation

### v21 Architecture (Legacy - Evaluate subworkflow only)

```
Schedule Trigger
    |
[VC Scrapers] --> Merge --> Dedup --> Brave Search --> Parse Enrichment
    |
IF: Auto-Disqualify
    | (true)                         | (false)
Airtable: Auto-Disqualified     Execute Evaluate Subworkflow
                                     |
                                Airtable: Create Evaluated Record
```

## Setup

### v22 Setup

1. **Import the pipeline subworkflow:**
   - Import `Enrich & Evaluate Pipeline.json` into n8n
   - **Configure credentials ONCE in the pipeline:**
     - Airtable API token (3 nodes use this)
     - Brave Search API (Header Auth with `X-Subscription-Token`)
     - Anthropic API Key (Header Auth with `x-api-key`)
   - Note the workflow ID

2. **Import v22 sector workflows:**
   - `VC Scraper - Healthcare v22.json`
   - `VC Scraper - Climate Tech v22.json`
   - `VC Scraper - Social Justice v22.json`
   - `VC Scraper - Enterprise & Generalist v22.json`

3. **Configure each v22 workflow:**
   - Set the "Execute Enrich & Evaluate Pipeline" node's workflow ID
   - Configure **Browserless credentials** for workflows that use them:
     - Healthcare v22: Browserless (for WhatIf, Leadout)
     - Climate Tech v22: Browserless (for Khosla)
     - Enterprise & Generalist v22: Browserless (for Unusual, Notable, Headline, Trilogy)
   - Social Justice v22 uses HTTP only (no Browserless needed)

4. **Test and enable the schedule triggers**

### v21 Setup (Legacy)

1. Import `Evaluate Company Subworkflow.json`, note its workflow ID
2. Import v21 sector workflows
3. Configure subworkflow connection in each
4. Configure credentials in EACH workflow (Browserless, Brave, Anthropic, Airtable)

## Files

### v22 (Recommended - full pipeline + real scraping)
- `Enrich & Evaluate Pipeline.json` - Complete pipeline: dedup, Brave, Claude, Airtable
- `VC Scraper - Healthcare v22.json` - WhatIf + Leadout scraping + static lists
- `VC Scraper - Climate Tech v22.json` - Khosla scraping + static lists
- `VC Scraper - Social Justice v22.json` - Kapor scraping + static lists
- `VC Scraper - Enterprise & Generalist v22.json` - 10 VC scrapers (NEW)

### v21 (Evaluate subworkflow only)
- `Evaluate Company Subworkflow.json` - Evaluation logic only
- `VC Scraper - Healthcare v21.json`
- `VC Scraper - Climate Tech v21.json`
- `VC Scraper - Social Justice v21.json`

### v20 (Legacy - inline everything)
- `VC Scraper - Healthcare.json`
- `VC Scraper - Climate Tech.json`
- `VC Scraper - Social Justice.json`
- `vc-portfolio-scraper-v20-enriched.json` - Original 14 VC scraper

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
- Pipeline credentials (Airtable, Brave, Anthropic) configured once in the pipeline
- Browserless credentials must be configured in each workflow that uses them
- Rate limited to 30s between Anthropic API calls to avoid rate limits
- Brave Search limited to 1.5s between calls

## Architecture Comparison

| Aspect | v20 (Inline) | v21 (Eval Subworkflow) | v22 (Full Pipeline) |
|--------|--------------|------------------------|---------------------|
| Nodes per scraper | ~40 | ~25 | 8-30 (depends on VCs) |
| Pipeline credentials | 4 per workflow | 3 per workflow | **1 (pipeline only)** |
| Browserless creds | Per workflow | Per workflow | Per workflow |
| Dedup logic | Per workflow | Per workflow | **Pipeline** |
| Brave Search | Per workflow | Per workflow | **Pipeline** |
| Claude eval | Per workflow | Subworkflow | **Pipeline** |
| Airtable writes | Per workflow | Per workflow | **Pipeline** |
| Real scraping | Yes | Yes | **Yes** |
| To add new VC | Copy ~40 nodes | Copy ~25 nodes | **Add scraper nodes** |

## Version History

- **Feb 2026 (v22 update)**: Added real scraping logic from v20 to all sector workflows. Created Enterprise & Generalist workflow for 10 VCs. Redistributed all 14 original VCs across 4 sector workflows.
- **Feb 2026 (v22)**: Full pipeline subworkflow. Scrapers initially used static lists. Credentials configured once in pipeline.
- **Feb 2026 (v21)**: Evaluate-only subworkflow. Still had dedup/Brave/Airtable in each scraper.
- **Feb 2026 (v20)**: Tide Pool evaluation framework with inline logic.
- **Jan 2026**: Initial versions with simple classification
