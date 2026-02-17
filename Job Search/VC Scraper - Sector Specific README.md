# VC Scraper - Sector Specific Workflows

Three n8n workflows that scrape portfolio companies from sector-focused venture capital firms.

**v21 workflows** use the shared "Evaluate Company Subworkflow" for consistent evaluation logic across all scrapers.

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

## Workflow Architecture (v21)

```
Schedule Trigger
    |
[VC Scrapers in parallel] --> Merge --> Dedup Against Existing
    |
Build Search Query --> Brave Search Company --> Parse Enrichment
    |
IF: Auto-Disqualify
    | (true)                         | (false)
Airtable: Auto-Disqualified     Execute Evaluate Subworkflow
                                     |
                                Airtable: Create Evaluated Record
```

The key difference from v20: Instead of inline evaluation logic (Fetch Tide Pool, Build Prompt, Claude API, Parse), v21 workflows call the shared subworkflow with a single "Execute Workflow" node.

## Setup

1. **Import the subworkflow first:**
   - Import `Evaluate Company Subworkflow.json` into n8n
   - Note its workflow ID

2. **Import the v21 sector workflows:**
   - `VC Scraper - Healthcare v21.json`
   - `VC Scraper - Climate Tech v21.json`
   - `VC Scraper - Social Justice v21.json`

3. **Configure the subworkflow connection:**
   - In each v21 workflow, find the "Execute Evaluate Subworkflow" node
   - Set the workflow ID to match your imported subworkflow

4. **Configure credentials:**
   - **Browserless API** (Header Auth) - if using Browserless scrapers
   - **Brave Search API** (Header Auth with `X-Subscription-Token`)
   - **Anthropic API Key** (Header Auth with `x-api-key`) - configured in subworkflow
   - **Airtable API** token

5. **Test and enable:**
   - Test run the workflow
   - Enable the schedule trigger

## Files

### v21 (Current - shared subworkflow)
- `Evaluate Company Subworkflow.json` - Shared evaluation logic
- `VC Scraper - Healthcare v21.json`
- `VC Scraper - Climate Tech v21.json`
- `VC Scraper - Social Justice v21.json`

### v20 (Legacy - inline evaluation)
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

## Benefits of v21 Architecture

| Aspect | v20 (Inline) | v21 (Subworkflow) |
|--------|--------------|-------------------|
| Evaluation logic | Duplicated in each workflow | Single subworkflow |
| Updates | Edit every workflow | Edit subworkflow once |
| Consistency | Manual sync required | Automatic |
| Config source | Hardcoded in prompts | evaluation-config.json |
| Complexity | ~40 nodes per workflow | ~25 nodes + subworkflow |

## Version History

- **Feb 2026 (v21)**: Refactored to use shared "Evaluate Company Subworkflow". Added evaluation-config.json governance. Simplified sector workflows.
- **Feb 2026 (v20)**: Updated to use Tide Pool evaluation framework
- **Feb 2026**: Added Brave Search enrichment and auto-disqualification
- **Jan 2026**: Initial versions with simple classification
