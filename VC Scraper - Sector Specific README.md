# VC Scraper - Sector Specific Workflows

Five n8n workflows that scrape portfolio companies from sector-focused venture capital firms.

**Current Versions:**
- Healthcare: v27 (14 VCs including Tier 2 healthcare and vertical SaaS)
- Enterprise/Generalist: v26 (14 VCs)
- Climate Tech: v23
- Social Justice: v25
- Micro-VC: v14 (includes Y Combinator)

**All workflows use the shared `Enrich & Evaluate Pipeline v9.json` subworkflow** for:
- 6-phase evaluation architecture
- 100-point scoring with domain distance modifiers
- 5-tier gate system (hard gates, sector gates, GTM motion, stale company, soft flags)
- CS Hire Readiness threshold (>=10 required)
- Airtable record creation

## Workflows

### VC Scraper - Healthcare v27
**Schedule:** Tuesday/Friday at 8am

| VC Firm | Method | Focus |
|---------|--------|-------|
| WhatIf Ventures | Browserless | Healthcare innovation |
| Leadout Capital | Browserless | Healthcare/femtech |
| Flare Capital | Static list | Healthcare IT |
| 7wireVentures | Static list | Digital health |
| Oak HC/FT | Static list | Healthcare & fintech |
| Digitalis | Static list | Digital health |
| a16z Bio+Health | Static list | Healthcare |
| Healthworx | Static list | Healthcare innovation |
| Cade Ventures | Browserless | Health tech (Ro, Function Health) |
| Hustle Fund | Static list | Health/wellness filter |
| Martin Ventures | Static list | Healthcare |
| Town Hall Ventures | Static list | Healthcare |
| **Transformation Capital** | Static list | Healthcare PE/Growth |
| **Brewer Lane** | Static list | Healthcare |
| **Mainsail Partners** | Static list | Vertical SaaS |
| **Five Elms** | Static list | Vertical SaaS |

### VC Scraper - Climate Tech v23
**Schedule:** Monday/Thursday at 8am

| VC Firm | Method | Focus |
|---------|--------|-------|
| Khosla Ventures | Browserless | Climate/energy |
| Congruent Ventures | Static list | Sustainability |
| Prelude Ventures | Static list | Climate solutions |
| Lowercarbon Capital | Static list | Climate tech |

### VC Scraper - Social Justice v25
**Schedule:** Wednesday/Saturday at 8am

| VC Firm | Method | Focus |
|---------|--------|-------|
| Kapor Capital | HTTP (Sitemap) | Social impact |
| Backstage Capital | Static list | Underrepresented founders |
| Harlem Capital | Static list | Diverse founders |
| Collab Capital | Static list | Black founders |

### VC Scraper - Enterprise & Generalist v26
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
| K9 Ventures | Static HTML | Enterprise SaaS (Twilio, Carta) |
| Precursor Ventures | Sitemap | B2B software (Carrot Fertility) |
| M25 | Sitemap | Midwest HealthTech/FinTech |
| GoAhead Ventures | Browserless | Generalist |

### VC Scraper - Micro-VC v14
**Schedule:** Tuesday/Friday at 8am

| Source | Method | Focus |
|--------|--------|-------|
| Pear VC | Browserless | Early-stage |
| Floodgate | Browserless | Early-stage |
| Afore | Browserless | Pre-seed |
| Unshackled | Browserless | Immigrant founders |
| 2048 | Browserless | Deep tech |
| **Y Combinator** | Browserless | Sorted by launch date, extracts batch codes |

## Enrich & Evaluate Pipeline v9 Features

### 6-Phase Architecture

```
Phase 0: Entity Validation → Phase 1: Enrichment → Phase 2: Gates (5 tiers) →
Phase 3: Persona Classification → Phase 4: CS Readiness Threshold → Phase 5: Full Evaluation
```

### Gate Tiers

| Tier | Gate Type | Examples |
|------|-----------|----------|
| **Tier 1** | Hard Gates | PE-backed, >200 emp, >$500M, acquired, non-US |
| **Tier 2** | Sector Gates | Biotech, hardware, crypto, not software-first |
| **Tier 3** | GTM Motion | PLG-dominant, pre-sales function company |
| **Tier 4** | Stale Company | 3+ years since funding, shrinking signals |
| **Tier 5** | Soft Flags | <15 employees, 150-200 employees, pre-2016 |

### Scoring (100 Points + Domain Distance)

| Category | Points |
|----------|--------|
| CS Hire Readiness | 0-25 |
| Stage & Size Fit | 0-25 |
| Role Mandate | 0-20 |
| Sector & Mission | 0-15 |
| Outreach Feasibility | 0-15 |
| Domain Distance Modifier | -10 to +5 |

**Buckets:** APPLY (60+) / WATCH (40-59) / PASS (<40)

## Workflow Architecture

```
Schedule Trigger
    |
[Scraping Nodes] --> [Parse Nodes] --> Merge --> Combine All VCs --> Filter Valid
    |                                                                     |
[Static Data Node] ----------------------------------------->     Execute Enrich &
                                                                  Evaluate Pipeline v9
                                                                         |
                                                                         v
                                                          ┌─────────────────────────────┐
                                                          │ 6-PHASE PIPELINE            │
                                                          │ - Entity validation         │
                                                          │ - Brave Search enrichment   │
                                                          │ - 5-tier gate system        │
                                                          │ - Persona classification    │
                                                          │ - CS readiness threshold    │
                                                          │ - Full evaluation + domain  │
                                                          │ - Airtable record creation  │
                                                          └─────────────────────────────┘
```

## Setup

1. **Import the pipeline subworkflow first:**
   - Import `Enrich & Evaluate Pipeline v9.json` into n8n
   - Configure credentials ONCE in the pipeline:
     - Airtable API token
     - Brave Search API (Header Auth with `X-Subscription-Token`)
     - Anthropic API Key (Header Auth with `x-api-key`)
   - Note the workflow ID

2. **Import the sector workflows:**
   - `VC Scraper - Healthcare.json` (v27)
   - `VC Scraper - Climate Tech.json` (v23)
   - `VC Scraper - Social Justice.json` (v25)
   - `vc-portfolio-scraper-v26-enriched.json` (Enterprise v26)
   - `VC Scraper - Micro-VC v14.json`

3. **Configure each workflow:**
   - Open the "Execute Enrich & Evaluate Pipeline" node
   - Select the imported pipeline workflow
   - Configure Browserless credentials for workflows that use them

4. **Test and enable the schedule triggers**

## Files

### Pipeline (v9)
- `Enrich & Evaluate Pipeline v9.json` - Shared 6-phase evaluation pipeline

### Scrapers
- `VC Scraper - Healthcare.json` (v27) - 14 VCs
- `VC Scraper - Climate Tech.json` (v23) - 4 VCs
- `VC Scraper - Social Justice.json` (v25) - 4 VCs
- `vc-portfolio-scraper-v26-enriched.json` (v26) - 14 VCs
- `VC Scraper - Micro-VC v14.json` - 6 sources including YC

## Notes

- All workflows write to the same "Funding Alerts" Airtable table
- Pipeline credentials (Airtable, Brave, Anthropic) configured once in the pipeline
- Browserless credentials must be configured in each workflow that uses headless scraping
- Rate limited to 30s between Anthropic API calls
- Claude model: `claude-haiku-4-5`

## Related Documentation

- `CLAUDE.md` - Workflow IDs and credentials
- `ARCHITECTURE.md` - Technical architecture
- `SCORING-ARCHITECTURE.md` - 6-phase scoring details

## Version History

- **Mar 2026 (v9 pipeline)**: Full redesign - 6-phase architecture, domain distance scoring
- **Mar 2026 (Healthcare v27)**: Added Tier 2 healthcare VCs, vertical SaaS VCs
- **Feb 2026 (Micro-VC v14)**: Added Y Combinator
- **Feb 2026 (Enterprise v26)**: Added K9, Precursor, M25, GoAhead

---

*Last updated: March 2026*
