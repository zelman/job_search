# VC Scraper - Sector Specific Workflows

Three n8n workflows that scrape portfolio companies from sector-focused venture capital firms. All use the same Tide Pool evaluation logic as the main VC Portfolio Scraper v20.

## Workflows

### VC Scraper - Healthcare
**Schedule:** Tuesday/Friday at 8am

| VC Firm | Method | Focus |
|---------|--------|-------|
| Flare Capital | Browserless | Healthcare IT |
| 7wireVentures | Browserless | Digital health |
| Oak HC/FT | Browserless | Healthcare & fintech |
| Digitalis Ventures | Browserless | Digital health |
| a16z Bio+Health | Browserless | Biotech, health tech |
| Healthworx | Browserless | Healthcare innovation |

### VC Scraper - Climate Tech
**Schedule:** Wednesday/Saturday at 8am

| VC Firm | Method | Focus |
|---------|--------|-------|
| Congruent Ventures | Browserless | Sustainability |
| Prelude Ventures | Browserless | Climate solutions |
| Clean Energy Ventures | Browserless | Clean energy |
| Lowercarbon Capital | Browserless | Climate tech |
| Energy Impact Partners | Browserless | Energy transition |
| DCVC | Browserless | Deep tech, climate |

### VC Scraper - Social Justice
**Schedule:** Tuesday/Friday at 9am

| VC Firm | Method | Focus |
|---------|--------|-------|
| Kapor Capital | Sitemap XML | Social impact, diversity |
| Backstage Capital | Browserless | Underrepresented founders |
| Harlem Capital | Browserless | Diverse founders |
| Impact America Fund | Browserless | Underserved communities |
| Collab Capital | Browserless | Black founders |

## Shared Features

All three workflows include:
- **Brave Search enrichment** (employee count, funding, PE detection, etc.)
- **Auto-disqualification** (PE-backed, 500+ employees, $200M+ funding, etc.)
- **Tide Pool evaluation** via Claude API (0-100 score)
- **Score-based status** (Apply/Monitor/Research/Skip)
- **Deduplication** against existing Airtable records

## Workflow Architecture

```
Schedule Trigger
    ↓
[VC Scrapers in parallel] → Merge → Dedup Against Existing
    ↓
Build Search Query → Brave Search Company → Parse Enrichment
    ↓
IF: Auto-Disqualify
    ↓ (true)                    ↓ (false)
Airtable: Auto-Disqualified    Fetch Tide Pool Profile
                                    ↓
                               Build Evaluation Prompt
                                    ↓
                               Evaluate via Anthropic API
                                    ↓
                               Parse Evaluation
                                    ↓
                               Airtable: Create Evaluated Record
```

## Setup

1. Import the desired workflow JSON into n8n
2. Configure credentials:
   - **Browserless API** (Header Auth)
   - **Brave Search API** (Header Auth - select for "Brave Search Company" node)
   - **Anthropic API Key** (Header Auth - select for "Evaluate via Anthropic API" node)
   - **Airtable API** token
3. Ensure Airtable has all required fields (see main VC Portfolio Scraper README)
4. Test run the workflow
5. Enable the schedule trigger

## Files

- `VC Scraper - Healthcare.json`
- `VC Scraper - Climate Tech.json`
- `VC Scraper - Social Justice.json`

## Notes

- All workflows write to the same "Funding Alerts" Airtable table
- Credentials must be manually configured after import (credential IDs are instance-specific)
- Rate limited to 30s between Anthropic API calls to avoid rate limits
- Brave Search limited to 1.5s between calls

## Version History

- **Feb 2026**: Updated to use Tide Pool evaluation framework (matching v20 of main scraper)
- **Feb 2026**: Added Brave Search enrichment and auto-disqualification
- **Jan 2026**: Initial versions with simple classification
