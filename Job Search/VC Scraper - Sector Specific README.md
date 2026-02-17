# VC Scraper - Sector Specific Workflows

Three n8n workflows that scrape portfolio companies from sector-focused venture capital firms.

**v22 workflows** (recommended) use the shared "Enrich & Evaluate Pipeline" - just 3 nodes each!

**v21 workflows** use the shared "Evaluate Company Subworkflow" for evaluation only.

## Workflows

### VC Scraper - Healthcare v21
**Schedule:** Tuesday/Friday at 8am

| VC Firm | Method | Focus |
|---------|--------|-------|
| Flare Capital | Browserless | Healthcare IT |
| 7wireVentures | Browserless | Digital health |
| Oak HC/FT | Browserless | Healthcare & fintech |

### VC Scraper - Climate Tech v21
**Schedule:** Monday/Thursday at 8am

| VC Firm | Method | Focus |
|---------|--------|-------|
| Congruent Ventures | HTTP | Sustainability |
| Prelude Ventures | HTTP | Climate solutions |
| Lowercarbon Capital | HTTP | Climate tech |

### VC Scraper - Social Justice v21
**Schedule:** Wednesday/Saturday at 8am

| VC Firm | Method | Focus |
|---------|--------|-------|
| Backstage Capital | HTTP | Underrepresented founders |
| Harlem Capital | HTTP | Diverse founders |
| Collab Capital | HTTP | Black founders |

## Shared Features

All v21 workflows include:
- **Shared Subworkflow**: Calls "Evaluate Company Subworkflow" for consistent evaluation
- **Brave Search enrichment** (employee count, funding, PE detection, etc.)
- **Auto-disqualification** (PE-backed, 500+ employees, $200M+ funding, etc.)
- **Customer Journey Leader evaluation** via Claude API (0-80 score)
- **Three Questions check** for APPLY candidates (from Tide Pool framework)
- **Score-based buckets** (APPLY/WATCH/PASS)
- **Deduplication** against existing Airtable records

## Workflow Architecture

### v22 Architecture (Recommended - 3 nodes!)

```
Schedule Trigger --> VC Portfolio Data --> Execute "Enrich & Evaluate Pipeline"
```

That's it! The pipeline handles everything: dedup, Brave Search, disqualification, Claude evaluation, Airtable writes.

### v21 Architecture (Evaluate subworkflow only)

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

### v22 Setup (Recommended - credentials in ONE place)

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

3. **Configure each v22 workflow:**
   - Set the "Execute Enrich & Evaluate Pipeline" node's workflow ID
   - **No other credentials needed!**

4. **Test and enable the schedule triggers**

### v21 Setup (Legacy)

1. Import `Evaluate Company Subworkflow.json`, note its workflow ID
2. Import v21 sector workflows
3. Configure subworkflow connection in each
4. Configure credentials in EACH workflow (Browserless, Brave, Anthropic, Airtable)

## Files

### v22 (Recommended - full pipeline subworkflow)
- `Enrich & Evaluate Pipeline.json` - Complete pipeline: dedup, Brave, Claude, Airtable
- `VC Scraper - Healthcare v22.json` (3 nodes)
- `VC Scraper - Climate Tech v22.json` (3 nodes)
- `VC Scraper - Social Justice v22.json` (3 nodes)

### v21 (Evaluate subworkflow only)
- `Evaluate Company Subworkflow.json` - Evaluation logic only
- `VC Scraper - Healthcare v21.json`
- `VC Scraper - Climate Tech v21.json`
- `VC Scraper - Social Justice v21.json`

### v20 (Legacy - inline everything)
- `VC Scraper - Healthcare.json`
- `VC Scraper - Climate Tech.json`
- `VC Scraper - Social Justice.json`

### Configuration
- `evaluation-config.json` - Single source of truth for evaluation rules

## Notes

- All workflows write to the same "Funding Alerts" Airtable table
- Credentials must be manually configured after import (credential IDs are instance-specific)
- Rate limited to 30s between Anthropic API calls to avoid rate limits
- Brave Search limited to 1.5s between calls
- v21 workflows are simpler to maintain - update the subworkflow and all scrapers benefit

## Architecture Comparison

| Aspect | v20 (Inline) | v21 (Eval Subworkflow) | v22 (Full Pipeline) |
|--------|--------------|------------------------|---------------------|
| Nodes per scraper | ~40 | ~25 | **3** |
| Credential configs | 4 per workflow | 3 per workflow | **1 (pipeline only)** |
| Dedup logic | Per workflow | Per workflow | **Pipeline** |
| Brave Search | Per workflow | Per workflow | **Pipeline** |
| Claude eval | Per workflow | Subworkflow | **Pipeline** |
| Airtable writes | Per workflow | Per workflow | **Pipeline** |
| To add new VC | Copy 40 nodes | Copy 25 nodes | **Add to data array** |

## Version History

- **Feb 2026 (v22)**: Full pipeline subworkflow. Scrapers reduced to 3 nodes. Credentials configured once in pipeline. Added "Enrich & Evaluate Pipeline.json".
- **Feb 2026 (v21)**: Evaluate-only subworkflow. Still had dedup/Brave/Airtable in each scraper.
- **Feb 2026 (v20)**: Tide Pool evaluation framework with inline logic.
- **Jan 2026**: Initial versions with simple classification
