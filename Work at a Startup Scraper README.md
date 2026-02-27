# Work at a Startup Scraper v6

An n8n workflow that scrapes job listings from Y Combinator's Work at a Startup and Costanoa Ventures portfolio, using the standardized Tide Pool evaluation sub-routine for AI-powered job scoring.

## Overview

This workflow runs every 6 hours to:
1. Scrape YC Work at a Startup (authenticated via Browserless)
2. Scrape Costanoa Ventures job board
3. Filter for customer support/success leadership roles
4. Deduplicate against existing Airtable records
5. Prefilter using builder vs. maintainer signals
6. **Enrich company data via Brave Search** (employee count, funding, PE/VC backing)
7. **Score using Claude AI** with dynamic Tide Pool Agent Lens
8. Add scored jobs to Airtable

## v6 Changes

**Major refactor**: Replaced single "Rate Job Fit" node with the standardized 7-node evaluation sub-routine used by the Job Alert Email Parser.

| v5 | v6 |
|----|----|
| Hard-coded evaluation criteria | Dynamic profile from GitHub |
| Single monolithic node | 7 modular nodes |
| No company enrichment | Brave Search enrichment |
| Tied to "Eric's" criteria | Uses shared Tide Pool Agent Lens |

### Benefits
- **Modular**: Can swap Brave Search for another enrichment provider
- **Consistent**: Same evaluation logic as email parser
- **Maintainable**: Update criteria in one place (GitHub)
- **Enriched**: Company funding/size data improves scoring accuracy

## Data Sources

### Work at a Startup (YC)
- **URL**: workatastartup.com
- **Method**: Browserless headless browser with YC account login
- **Filter**: Support/success + leadership keywords

### Costanoa Ventures
- **URL**: jobs.costanoa.vc
- **Method**: Browserless extraction of `serverInitialData`
- **Filter**: 1-100 employee companies, support/success + leadership

## Pipeline

```
Schedule Trigger (6 hours)
       │
       ├──→ Get Config (Airtable)
       │
       ├──→ Search Existing Jobs (dedup)
       │
       └──→ Fetch Profile (GitHub)
                   │
              Parse Config
                   │
       ┌───────────┴───────────┐
       ▼                       ▼
  Scrape YC              Scrape Costanoa
(Browserless)            (Browserless)
       │                       │
       ▼                       ▼
Parse & Filter           Parse Costanoa
       │                       │
       └───────────┬───────────┘
                   ▼
           Merge Job Sources
                   │
                   ▼
        Dedup Against Airtable
                   │
                   ▼
              Has Jobs?
                   │
                   ▼
    Prefilter: Builder vs Maintainer
                   │
                   ▼
         IF: Should Process
                   │
    ┌──────────────┴──────────────┐
    ▼                             ▼
Skip Filtered              EVALUATION CHAIN
                                  │
                    ┌─────────────┴─────────────┐
                    │  Brave Search Company     │
                    │  Parse Enrichment         │
                    │  Build Prompt             │
                    │  Wait (Rate Limit)        │
                    │  Call Claude API          │
                    │  Parse Response           │
                    └─────────────┬─────────────┘
                                  │
                                  ▼
                          Add to Airtable
```

## Configuration

### Airtable Config Table

| Key | Description |
|-----|-------------|
| `ANTHROPIC_API_KEY` | Claude API key for scoring |
| `BROWSERLESS_TOKEN` | Browserless.io API token |
| `YC_USER` | Work at a Startup email |
| `YC_PASSWORD` | Work at a Startup password |

### n8n Credentials

| Credential | Type | Used By |
|------------|------|---------|
| Airtable | Token | All Airtable nodes |
| Brave Search | Header Auth | Brave Search Company |

### External Dependencies

| Service | Purpose |
|---------|---------|
| Browserless.io | Headless browser scraping |
| Brave Search API | Company enrichment |
| Anthropic Claude API | AI scoring |
| GitHub Raw | Tide Pool profile hosting |

## Role Filtering

Jobs must contain:

**At least one support/success keyword:**
- support, success, customer, client, cx, experience

**AND at least one leadership keyword:**
- manager, director, vp, vice president, head, lead, chief, supervisor, team lead

## Evaluation Sub-Routine

The 7-node evaluation chain provides:

### Enrichment (Brave Search)
- Employee count
- Funding stage (Seed → Series D+)
- Total funding raised
- PE vs VC backing
- Founded year / company age

### AI Scoring (Claude)
- Tide-Pool Score (0-100)
- Role type (builder/maintainer/hybrid)
- Builder evidence
- Maintainer evidence
- Recommendation (apply/research/skip)
- Industry classification
- Company stage detection

### Auto-Disqualifiers
- PE-backed company
- 1,000+ employees
- $500M+ total funding
- Public company
- Zombie companies (7+ years, still Seed, <100 employees)

## Output Fields

| Field | Description |
|-------|-------------|
| Job Title | Role title |
| Company | Company name |
| Location | Work location |
| Source | "Work at a Startup" or "Costanoa VC" |
| Job URL | Link to posting |
| Job ID | Dedup key |
| Salary Info | If available |
| Date Found | Scrape date |
| Review Status | "New" |
| Tide-Pool Score | 0-100 fit score |
| Tide-Pool Rationale | AI explanation + enrichment data |
| Industry | AI-detected industry |
| Company Stage | Funding stage |
| Role Type | builder/maintainer/hybrid |
| Builder Evidence | Positive signals |
| Maintainer Evidence | Negative signals |
| Recommendation | apply/research/skip |

## Troubleshooting

### No jobs scraped
- Check Browserless token is valid
- Verify YC credentials work (try manual login)
- Check if site structure changed

### Brave Search errors
- Verify Brave API key in Header Auth credential
- Check monthly quota (2,000 free requests)

### Claude API errors
- Verify ANTHROPIC_API_KEY in Airtable Config
- Check for rate limiting (30s delay should prevent)

### Profile not loading
- Verify GitHub URL is accessible
- Check `https://raw.githubusercontent.com/zelman/tidepool/refs/heads/main/tide-pool-agent-lens.md`

## Version History

- **v6**: Refactored to use standardized evaluation sub-routine (Brave Search enrichment + dynamic Tide Pool profile)
- **v5**: Added Costanoa Ventures scraping, prefilter for builder/maintainer
- **v4**: Initial YC Work at a Startup scraper with built-in Claude rating

---

*See also: `ARCHITECTURE.md` for detailed evaluation sub-routine documentation*
