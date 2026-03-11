# VC Portfolio Scraper

An n8n workflow system that automatically scrapes portfolio companies from mission-aligned venture capital firms, enriches them with company data via Brave Search, evaluates fit using the Enrich & Evaluate Pipeline v9, and adds them to Airtable for job search tracking.

## Current Architecture

**All VC scrapers now use the shared `Enrich & Evaluate Pipeline v9.json` subworkflow** which provides:

- **6-phase evaluation architecture** (entity validation → enrichment → gates → persona → CS readiness → full evaluation)
- **100-point scoring** with domain distance modifiers (+5 healthcare to -10 physical security)
- **5-tier gate system** (hard gates, sector gates, GTM motion gates, stale company gates, soft flags)
- **CS Hire Readiness threshold** (must score >=10 to proceed to full evaluation)
- **Enhanced detection** (PE portfolio patterns, PLG-dominant, services businesses, stale companies)

## Scraper Inventory

| Scraper | Version | VCs Covered | Schedule |
|---------|---------|-------------|----------|
| **Healthcare** | v27 | 14 VCs: Flare Capital, 7wireVentures, Oak HC/FT, Digitalis, a16z Bio+Health, Healthworx, Cade, Hustle Fund, Martin Ventures, Town Hall Ventures, Transformation Capital, Brewer Lane, Mainsail Partners, Five Elms | Tue/Fri 8am |
| **Climate Tech** | v23 | 4 VCs: Khosla, Congruent, Prelude, Lowercarbon | Mon/Thu 8am |
| **Social Justice** | v25 | 4 VCs: Kapor, Backstage, Harlem, Collab | Wed/Sat 8am |
| **Enterprise/Generalist** | v26 | 14 VCs: Unusual, First Round, Essence, Costanoa, WXR, Golden, Notable, Headline, PSL, Trilogy, K9, Precursor, M25, GoAhead | Mon/Thu 8am |
| **Micro-VC** | v14 | 6 sources: Pear VC, Floodgate, Afore, Unshackled, 2048, **Y Combinator** | Tue/Fri 8am |

## Enrich & Evaluate Pipeline v9 Features

### 6-Phase Architecture

```
INPUT (company from scraper)
    │
    ▼
Phase 0: ENTITY VALIDATION
    • Catches non-companies (podcasts, media, nonprofits)
    │
    ▼
Phase 1: ENRICHMENT (Brave Search)
    • Employee count, funding, stage, geography
    • Enhanced acquisition detection (PE portfolio patterns)
    • GTM motion signals (PLG vs enterprise)
    • Software-first check
    │
    ▼
Phase 2: PRE-EVALUATION GATES (5 Tiers)
    • Tier 1: Hard gates (PE, >200 emp, >$500M, public, acquired, non-US)
    • Tier 2: Sector gates (biotech, hardware, crypto, not software-first)
    • Tier 3: GTM motion gates (PLG-dominant, pre-sales function)
    • Tier 4: Stale company gates (3+ years since funding, shrinking)
    • Tier 5: Soft flags (<15 emp, 150-200 emp, pre-2016)
    │
    ▼
Phase 3: PERSONA CLASSIFICATION
    • business-user, employee-user, developer, mixed
    • Developer auto-pass unless 50+ emp + 3+ enterprise signals
    │
    ▼
Phase 4: CS HIRE READINESS THRESHOLD
    • Quick Claude call to confirm CS need
    • Must score >= 10 to proceed
    │
    ▼
Phase 5: FULL EVALUATION
    • 100-point scoring with domain distance modifier
    • APPLY (60+) / WATCH (40-59) / PASS (<40)
```

### Scoring Categories (100 Points + Domain Distance)

| Category | Points | What It Measures |
|----------|--------|------------------|
| CS Hire Readiness | 0-25 | Does company need CS hire NOW? |
| Stage & Size Fit | 0-25 | Right inflection point? |
| Role Mandate | 0-20 | Builder vs Maintainer? |
| Sector & Mission | 0-15 | Alignment with experience? |
| Outreach Feasibility | 0-15 | Network access? |
| **Domain Distance** | -10 to +5 | Healthcare +5, Physical Security -10 |

### Auto-Disqualification Reasons (v9)

- Acquired/merged company
- PE-backed (with firm name detection)
- Public company, Fortune 500 subsidiary
- >200 employees, >$500M funding, Series D+
- Invalid entity (media/podcast/nonprofit)
- Non-US primary market
- Not software-first (services, hardware+software)
- PLG-dominant (no enterprise CS need)
- Pre-sales function company
- Stale company (3+ years since funding)
- CS Hire Readiness below threshold

## Requirements

- n8n (Cloud or self-hosted)
- Browserless.io account (for JS-rendered pages)
- Brave Search API key (for company enrichment)
- Anthropic API key (for Claude Haiku 4.5 evaluation)
- Airtable base with "Funding Alerts" table

## Setup

1. **Import the pipeline subworkflow first:**
   - Import `Enrich & Evaluate Pipeline v9.json` into n8n
   - Configure credentials in the pipeline:
     - Airtable API token
     - Brave Search API (Header Auth with `X-Subscription-Token`)
     - Anthropic API Key (Header Auth with `x-api-key`)
   - Note the workflow ID (you'll need this for each scraper)

2. **Import the sector workflows:**
   - `VC Scraper - Healthcare.json` (v27)
   - `VC Scraper - Climate Tech.json` (v23)
   - `VC Scraper - Social Justice.json` (v25)
   - `vc-portfolio-scraper-v26-enriched.json` (Enterprise/Generalist)
   - `VC Scraper - Micro-VC v14.json`

3. **Configure each workflow:**
   - Open the "Execute Enrich & Evaluate Pipeline" node
   - Select the imported pipeline workflow (or set workflow ID)
   - Configure Browserless credentials for workflows that use them

4. **Test and enable the schedule triggers**

## Airtable Schema

Required fields in Funding Alerts table:

| Field | Type | Description |
|-------|------|-------------|
| Company Name | Text | Primary field |
| Company URL | URL | Company website |
| Company Description | Long text | From VC portfolio |
| VC Firm | Single line text | Source VC |
| Status | Single select | Apply, Watch, Pass, Auto-Disqualified |
| Tide-Pool Score | Number | 0-100 evaluation score |
| Customer Persona | Single select | business-user, employee-user, developer, mixed |
| CS Hire Readiness | Number | 0-30 (threshold: 10) |
| Domain Distance | Text | target, adjacent, high-distance |
| Summary | Long text | AI-generated evaluation |
| Stage | Single line text | Funding stage |
| Total Funding | Single line text | e.g., "$50M" |
| Employee Count | Number | From Brave Search |
| PE Backed | Checkbox | Private equity backed |
| Disqualify Reasons | Long text | Auto-disqualification reasons |

## Related Documentation

- `CLAUDE.md` - Project instructions and workflow IDs
- `ARCHITECTURE.md` - Detailed technical architecture
- `SCORING-ARCHITECTURE.md` - 6-phase scoring system
- `SYSTEM-OVERVIEW.md` - Executive summary

## FigJam Diagrams

- [System Architecture v9](https://www.figma.com/online-whiteboard/create-diagram/f1065a98-f078-44b9-9ba6-b088601f526b)
- [v9 Pipeline Gate Flow](https://www.figma.com/online-whiteboard/create-diagram/6d2f6511-9e89-4635-8585-238feae95221)
- [v9 Scoring Architecture](https://www.figma.com/online-whiteboard/create-diagram/d16d9d48-12af-4d27-9fa1-99566ea42a1d)

## Version History

- **Mar 2026 (v9)**: Full pipeline redesign - 6-phase architecture, entity validation, GTM motion gates, CS readiness threshold, domain distance scoring
- **Mar 2026 (v27)**: Healthcare scraper - Added Tier 2 VCs (Transformation Capital, Brewer Lane) and vertical SaaS VCs (Mainsail, Five Elms)
- **Feb 2026 (v14)**: Micro-VC - Added Y Combinator (sorted by launch date, extracts batch codes)
- **Feb 2026 (v26)**: Enterprise - Added K9, Precursor, M25, GoAhead

---

*Last updated: March 2026*
