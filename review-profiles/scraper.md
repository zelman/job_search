# Review Context: VC Scraper

## What This Code Does
VC portfolio scrapers that extract company lists from venture capital firm websites using Browserless.io, then send new companies to the Enrich & Evaluate Pipeline (rcMNDrfZR6csHRsYKFn0W) for scoring.

## VC Scraper Inventory

| Scraper | ID | VCs | Schedule | Dedup Status | Signal Rate |
|---------|-----|-----|----------|--------------|-------------|
| Growth Stage v2.7 | `u0rWl0T2SRZgfuJe` | 2 (Emergence, GC) | Wed/Sat 8am | Dual-source DONE | Emergence 24%, GC 11% |
| Healthcare v28 | `mwAsPafWzMtSqycYkEdjX` | 14 | Tue/Fri 8am | Dual-source DONE | a16z Bio 53%, 7wire 36%, Oak 29%, Flare 24% |
| Enterprise v28 | `QhG1YU8-b2pTgrvAx-yrd` | 15 | Mon/Thu 8am | Dual-source DONE | Varied |
| Bessemer/Battery v2.7 | `wF8Q5tgEJz1buzOI` | 2 | Weekly | Pipeline-only (paginated) | Bessemer 7% (32 Apply, highest absolute) |
| Micro-VC v15 | `UcK-xCze5eubBWnCHtyDT` | 5 | Tue/Fri 8am | **LIKELY NONE** | Needs verification |
| Social Justice v25 | `x0S2fhUfEKxG1Qj8NexDH` | 4 | Wed/Sat 8am | **LIKELY NONE** | Collab 0% |
| Climate Tech v23 | *(check n8n)* | 4 | Mon/Thu 8am | Unknown | Needs verification |
| Lightspeed v1 | `gHCiPqjUuOsMd0BF` | 1 | Tue/Fri 8am | Unknown | Needs verification |
| SEC Form D v2.4 | `rYnP4hC9QvP6LhPQ` | N/A | Daily 8am ET | Different architecture | Low |

## Dedup Register Bug (ACTIVE)
The Dedup Register subworkflow (MDzcHPZMySqn1DrGh8J0-) is NOT writing to Seen Opportunities. Scraper-level dedup MUST check Funding Alerts as a second source. Any code relying solely on Seen Opportunities for dedup will miss most existing companies.

## Dual-Source Dedup Pattern (Template)
Proven in Growth Stage v2.7, Healthcare v28, Enterprise v28:

```
Schedule Trigger
    |-> Fetch Seen Keys (Airtable: Seen Opportunities, filter: LEFT({Key}, 8) = "company:")
    |-> Fetch Funding Alerts (Airtable: Funding Alerts, Company Name field only)
           |
    Merge Seen Sources (Merge node)
           |
    Store Seen Keys (Code node: normalize both sources into Set, store in workflow staticData)
           |
    ... existing scraper branches (Browserless, parse, merge chain) ...
           |
    Filter New Only (Code node: check each company against stored keys, deduplicate)
           |
    Has New Companies? (IF node) -> Limit -> Execute Workflow (Pipeline)
```

Key normalization: `'company:' + name.toLowerCase().replace(/[^a-z0-9]/g, '')`

Full implementation code in BRAVE-COST-REDUCTION-PLAN.md under Tier 1.5.

## Pipeline Integration
Scrapers call E&E Pipeline via Execute Workflow node.
Pipeline ID: rcMNDrfZR6csHRsYKFn0W
Expected input fields: Company Name, Company URL, Source, and optionally stage, employee_count, total_funding, founded_year.

## Known Issues
- Healthcare v27 had hardcoded knownCompanies arrays (fixed in v28 with dual-source dedup)
- Enterprise v27 had no dedup (fixed in v28)
- Micro-VC, Social Justice, Climate Tech, Lightspeed still need dual-source dedup
- Browserless token in URL: find/replace `YOUR_BROWSERLESS_TOKEN` before importing Healthcare scraper
- First Round Jobs uses session cookie auth that expires: refresh from Chrome DevTools on 401
