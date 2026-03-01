# Migration Plan: n8n → Python + GitHub Actions

*Created: March 1, 2026*
*Status: DRAFT — Not yet approved for implementation*

---

## Motivation

The current system runs on n8n, a visual workflow tool. While powerful, it creates a bottleneck: every change to credentials, workflow logic, or scheduling requires manual interaction in the n8n UI. Moving to Python + GitHub Actions enables:

1. **Full code ownership** — Claude can write, modify, and push all automation code via git
2. **No GUI dependency** — credentials in GitHub Secrets (one-time setup), everything else is code
3. **Version control by default** — real diffs, PRs, blame, rollback via git (vs opaque JSON blobs)
4. **Free compute** — GitHub Actions free tier provides 2,000 minutes/month (more than enough for cron jobs)
5. **Simpler debugging** — Python stack traces vs n8n node error modals

---

## Current System Inventory

### Data Sources (15+)

| Source | Current Method | Frequency |
|--------|---------------|-----------|
| Gmail (10 job boards) | n8n Gmail node + HTML parsing | Hourly |
| YC Work at a Startup | Browserless headless login | Every 6 hours |
| Costanoa Ventures | HTTP + serverInitialData parse | Every 6 hours |
| VC Healthcare (7 VCs) | Browserless + HTTP + sitemaps | Tue/Fri 8am |
| VC Climate Tech (4 VCs) | Browserless + HTTP | Mon/Thu 8am |
| VC Social Justice (4 VCs) | Browserless + HTTP | Wed/Sat 8am |
| VC Enterprise/Generalist | Browserless + HTTP + sitemaps | Mon/Thu 8am |
| VC Micro-VC + YC (6 VCs) | Browserless + HTTP | Tue/Fri |
| Indeed | Direct scrape | TBD |

### External APIs

| API | Purpose | Auth Method | Python Library |
|-----|---------|-------------|----------------|
| Anthropic Claude | AI scoring (Haiku 4.5 + Sonnet 4) | API key | `anthropic` |
| Airtable | Data storage | Bearer token | `pyairtable` |
| Gmail | Email fetch + labeling | OAuth2 | `google-api-python-client` |
| Brave Search | Company enrichment | API key header | `requests` |
| Browserless.io | Headless scraping | Token param | `requests` (REST API) |

### Shared Subworkflows → Python Modules

| n8n Subworkflow | Python Module |
|-----------------|---------------|
| Job Evaluation Pipeline v4 | `pipelines/evaluate_job.py` |
| Enrich & Evaluate Pipeline v4 | `pipelines/evaluate_company.py` |
| Dedup Check Subworkflow | `pipelines/dedup.py` |
| Dedup Register Subworkflow | `pipelines/dedup.py` |
| Feedback Loop - Not a Fit | `feedback/not_a_fit.py` |
| Feedback Loop - Applied | `feedback/applied.py` |

---

## Target Architecture

```
job_search/
├── .github/
│   └── workflows/
│       ├── email-parser.yml          # Hourly cron
│       ├── startup-scraper.yml       # Every 6 hours
│       ├── vc-healthcare.yml         # Tue/Fri 8am ET
│       ├── vc-climate.yml            # Mon/Thu 8am ET
│       ├── vc-social-justice.yml     # Wed/Sat 8am ET
│       ├── vc-enterprise.yml         # Mon/Thu 8am ET
│       ├── vc-micro.yml              # Tue/Fri 8am ET
│       ├── indeed-scraper.yml        # TBD
│       ├── feedback-not-a-fit.yml    # Mon 9am ET
│       └── feedback-applied.yml      # Mon 9:30am ET
│
├── src/
│   ├── __init__.py
│   │
│   ├── scrapers/                     # Data source modules
│   │   ├── __init__.py
│   │   ├── email_parser.py           # Gmail fetch + 10 board parsers
│   │   ├── startup_scraper.py        # YC Work at a Startup + Costanoa
│   │   ├── indeed_scraper.py         # Indeed direct scrape
│   │   └── vc_scraper.py             # All VC portfolio scrapers
│   │
│   ├── parsers/                      # Email HTML parsers (per board)
│   │   ├── __init__.py
│   │   ├── linkedin.py
│   │   ├── indeed.py
│   │   ├── builtin.py
│   │   ├── wellfound.py
│   │   ├── himalayas.py
│   │   ├── remotive.py
│   │   ├── welcome_jungle.py
│   │   ├── jobright.py
│   │   ├── google_careers.py
│   │   └── bloomberry.py
│   │
│   ├── pipelines/                    # Shared evaluation logic
│   │   ├── __init__.py
│   │   ├── evaluate_job.py           # Job Evaluation Pipeline
│   │   ├── evaluate_company.py       # Enrich & Evaluate Pipeline
│   │   └── dedup.py                  # Cross-source dedup (check + register)
│   │
│   ├── enrichment/                   # Company/job enrichment
│   │   ├── __init__.py
│   │   ├── brave_search.py           # Brave API for company data
│   │   ├── jd_fetcher.py             # Job description fetching (HTTP + headless)
│   │   └── browserless.py            # Browserless.io client wrapper
│   │
│   ├── feedback/                     # Weekly feedback loops
│   │   ├── __init__.py
│   │   ├── not_a_fit.py
│   │   └── applied.py
│   │
│   ├── clients/                      # API client wrappers
│   │   ├── __init__.py
│   │   ├── airtable_client.py        # Airtable CRUD (pyairtable)
│   │   ├── claude_client.py          # Anthropic API wrapper
│   │   ├── gmail_client.py           # Gmail OAuth2 client
│   │   └── email_sender.py           # SMTP/Gmail send for alerts
│   │
│   ├── scoring/                      # Evaluation framework
│   │   ├── __init__.py
│   │   ├── tide_pool_lens.py         # Fetch + cache the north star doc
│   │   └── prompts.py                # All Claude prompt templates
│   │
│   └── config/                       # Configuration
│       ├── __init__.py
│       ├── settings.py               # Central settings (from env vars)
│       ├── vc_sources.py             # VC portfolio URL definitions
│       └── constants.py              # Airtable IDs, field names, thresholds
│
├── tests/
│   ├── __init__.py
│   ├── test_parsers/                 # Unit tests for email parsers
│   ├── test_pipelines/               # Tests for evaluation logic
│   ├── test_enrichment/              # Tests for enrichment
│   └── fixtures/                     # Sample HTML, API responses
│
├── evaluation-config.json            # Keep as-is (scoring rules reference)
├── tide-pool-agent-lens-v2.8.md      # Keep as-is (north star)
├── requirements.txt
├── pyproject.toml
└── README.md                         # Updated for Python project
```

---

## Migration Phases

### Phase 1: Foundation (Clients + Config)

Build the shared infrastructure that everything else depends on.

**Deliverables:**
- `src/clients/airtable_client.py` — Wrapper around `pyairtable` with table IDs, field mappings, upsert logic
- `src/clients/claude_client.py` — Thin wrapper around `anthropic` SDK, model selection (Haiku for scoring, Sonnet for feedback), retry logic
- `src/clients/gmail_client.py` — OAuth2 token management, email fetch by sender/label, label application
- `src/clients/email_sender.py` — Gmail SMTP send for alerts (urgent CX job matches, feedback reports)
- `src/enrichment/browserless.py` — Browserless.io REST client for headless scraping
- `src/enrichment/brave_search.py` — Brave Search API for company enrichment
- `src/config/settings.py` — Load all config from environment variables
- `src/config/constants.py` — Airtable base/table IDs, field names, scoring thresholds
- `src/scoring/prompts.py` — Extract all Claude prompt templates from n8n workflow JSON

**GitHub Secrets to configure (one-time manual setup):**

| Secret Name | Source |
|-------------|--------|
| `ANTHROPIC_API_KEY` | Currently in Airtable Config table |
| `AIRTABLE_API_TOKEN` | n8n credential store |
| `GMAIL_CREDENTIALS_JSON` | OAuth2 credentials (client ID, secret, refresh token) |
| `BROWSERLESS_TOKEN` | Currently in Airtable Config table |
| `BRAVE_API_KEY` | Currently in Airtable Config table |
| `YC_EMAIL` | Currently in Airtable Config table |
| `YC_PASSWORD` | Currently in Airtable Config table |

**How to test:** Unit tests against mock API responses. Integration test with real Airtable read.

---

### Phase 2: Dedup + Evaluation Pipelines

Port the shared subworkflows that all scrapers depend on.

**Deliverables:**
- `src/pipelines/dedup.py` — Check + register in Seen Opportunities table
- `src/pipelines/evaluate_job.py` — Full job evaluation: dedup check → JD fetch → Claude scoring → Airtable upsert → dedup register
- `src/pipelines/evaluate_company.py` — Full company evaluation: dedup check → Brave enrichment → Claude scoring → job cross-reference → Airtable upsert → dedup register → email alert (if CX match)
- `src/scoring/tide_pool_lens.py` — Fetch lens from GitHub raw URL, cache locally
- `src/enrichment/jd_fetcher.py` — HTTP fetch with Browserless fallback for JS-heavy pages

**Key logic to port:**
- 100-point scoring system with category breakdowns
- Auto-disqualifiers (PE-backed, 1000+ employees, $500M+ funding, public company, zombie)
- Scoring penalties (500-999 employees: -15pts, Support without Director/VP/Head: -15pts)
- Builder vs Maintainer classification
- Network connection override (Google VP contact)
- Job Listings cross-reference for VC companies (Has Active Job Posting, Has CX Job Posting)
- Immediate Action status assignment

**How to test:** Feed known job/company data through pipeline, verify scores match n8n output. Run both systems in parallel for a week.

---

### Phase 3: Email Parser

Port the highest-value, most frequently run workflow.

**Deliverables:**
- `src/scrapers/email_parser.py` — Main orchestrator: fetch emails → route to parser → evaluate → label
- `src/parsers/*.py` — One parser per job board (10 parsers)
- `.github/workflows/email-parser.yml` — Hourly cron trigger

**Parser complexity (rough ordering):**

| Parser | Complexity | Notes |
|--------|-----------|-------|
| LinkedIn | Medium | Two sender formats, structured HTML |
| Indeed | Low | Simple table layout |
| Google Careers | Low | Clean HTML |
| Built In | Low | Standard email format |
| Himalayas | Low | Standard format |
| Remotive | Low | Standard format |
| Bloomberry | Low | Standard format |
| Wellfound | Medium | Variable format |
| Welcome to the Jungle | Medium | SendGrid tracking links need resolution |
| Jobright | Medium | Variable format |

**GitHub Actions workflow example:**
```yaml
name: Email Parser
on:
  schedule:
    - cron: '0 * * * *'  # Every hour
  workflow_dispatch: {}   # Manual trigger
jobs:
  parse-emails:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -r requirements.txt
      - run: python -m src.scrapers.email_parser
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          AIRTABLE_API_TOKEN: ${{ secrets.AIRTABLE_API_TOKEN }}
          GMAIL_CREDENTIALS_JSON: ${{ secrets.GMAIL_CREDENTIALS_JSON }}
          BROWSERLESS_TOKEN: ${{ secrets.BROWSERLESS_TOKEN }}
```

**How to test:** Parse same emails through both n8n and Python, compare outputs. Gradually shift n8n to longer intervals, then disable.

---

### Phase 4: VC Portfolio Scrapers

Port all VC scraper workflows. These share a common pattern.

**Deliverables:**
- `src/scrapers/vc_scraper.py` — Generic VC scraper with per-VC config
- `src/config/vc_sources.py` — All VC portfolio URL definitions + scrape methods
- `.github/workflows/vc-*.yml` — 5 scheduled workflows (one per sector)

**Scraping methods to support:**

| Method | VCs Using It | Implementation |
|--------|-------------|----------------|
| Browserless headless | WhatIf, Leadout, Cade, Khosla, Unusual, Notable, Headline, Trilogy, GoAhead | `browserless.py` → parse returned HTML |
| Sitemap XML | Kapor, Costanoa, Precursor, M25 | `requests.get()` → XML parse |
| Static company list | Flare, 7wire, Oak, Congruent, Prelude, Lowercarbon, Backstage, Harlem, Collab, First Round, Essence, WXR, Golden, PSL, K9 | Hardcoded lists in `vc_sources.py` |
| Y Combinator | YC (in Micro-VC) | Browserless, extract batch from cards |

**Config-driven design:**
```python
# vc_sources.py (example structure)
VC_SOURCES = {
    "healthcare": [
        {"name": "WhatIf Ventures", "url": "...", "method": "browserless", "selector": "..."},
        {"name": "Flare Capital", "url": "...", "method": "sitemap"},
        {"name": "Oak HC/FT", "method": "static", "companies": [...]},
        # ...
    ],
    "climate": [...],
    "social_justice": [...],
    "enterprise": [...],
    "micro_vc": [...],
}
```

**How to test:** Run Python scraper for one VC, compare extracted companies against n8n output.

---

### Phase 5: Remaining Scrapers + Feedback Loops

**Deliverables:**
- `src/scrapers/startup_scraper.py` — YC Work at a Startup (Browserless login) + Costanoa
- `src/scrapers/indeed_scraper.py` — Indeed direct scrape
- `src/feedback/not_a_fit.py` — Weekly rejection pattern analysis (Claude Sonnet)
- `src/feedback/applied.py` — Weekly calibration analysis (Claude Sonnet)
- `.github/workflows/startup-scraper.yml`
- `.github/workflows/indeed-scraper.yml`
- `.github/workflows/feedback-not-a-fit.yml`
- `.github/workflows/feedback-applied.yml`

**How to test:** Run feedback loops manually, compare report quality with n8n versions.

---

### Phase 6: Parallel Run + Cutover

1. **Run both systems in parallel for 1-2 weeks** — Python writes to a staging Airtable view or adds a `source: python` tag
2. **Compare outputs** — Spot-check scores, dedup behavior, email alerts
3. **Gradual cutover** — Disable n8n workflows one at a time, starting with lowest-risk (feedback loops)
4. **Full cutover** — Disable n8n entirely, archive workflow JSON files to `archive/` directory
5. **Remove n8n dependency** — Cancel n8n hosting (if self-hosted) or subscription

---

## Key Design Decisions

### 1. Gmail OAuth2 in GitHub Actions

Gmail OAuth2 requires a refresh token. Options:
- **A) Store refresh token as GitHub Secret** — simplest. The `google-auth` library handles token refresh automatically. Store `credentials.json` (client config) and the initial refresh token. Token auto-renews.
- **B) Use a Google Service Account** — cleaner for automation, but requires Google Workspace domain-wide delegation. Only viable if using Google Workspace (not personal Gmail).
- **Recommendation:** Option A (refresh token in secret). One-time setup via OAuth consent flow.

### 2. Browserless.io vs. Playwright in GitHub Actions

- **Browserless.io** — keep using the existing service. Simple REST API, no browser install needed in GHA.
- **Playwright** — install in GHA runner, run headless locally. Free (no Browserless cost), but slower setup per run (~30s install step).
- **Recommendation:** Start with Browserless (zero migration risk), evaluate switching to Playwright later for cost savings.

### 3. Error handling + Alerting

- **Retry logic** — `tenacity` library for API retries with exponential backoff
- **GHA failure notifications** — GitHub's built-in email on workflow failure
- **Structured logging** — Python `logging` module, visible in GHA run logs
- **Optional:** Send failure summary to email via `email_sender.py`

### 4. Secrets Rotation

- Store API keys in GitHub Secrets (encrypted at rest)
- Remove the Airtable Config table dependency for credentials (currently stores ANTHROPIC_API_KEY, BROWSERLESS_TOKEN, etc.)
- Document which secrets are needed in README

### 5. Cron Timezone Handling

GitHub Actions cron runs in UTC. All current schedules are in US Eastern:
- `8am ET` = `13:00 UTC` (EST) or `12:00 UTC` (EDT)
- Recommend pinning to UTC times and accepting slight seasonal drift, or using a timezone-aware cron action

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Email parser regressions | Medium | High | Extensive fixture-based tests; parallel run |
| Gmail OAuth token expiry | Low | High | google-auth auto-refreshes; monitor for 401s |
| GHA minutes exhaustion | Low | Medium | Current estimate: ~300 min/month (well under 2,000 free) |
| Browserless rate limits | Low | Low | Same usage as today; no change |
| VC site layout changes | Medium | Medium | Same risk as today; Python makes fixes easier to push |
| Airtable API rate limits | Low | Medium | pyairtable has built-in rate limiting; same volume as today |

---

## Estimated GHA Minutes Usage

| Workflow | Frequency | Est. Runtime | Monthly Minutes |
|----------|-----------|-------------|-----------------|
| Email Parser | 24x/day | 2 min | 1,440 |
| Startup Scraper | 4x/day | 2 min | 240 |
| VC Scrapers (5) | 2x/week each | 3 min | 120 |
| Feedback Loops (2) | 1x/week each | 2 min | 16 |
| Indeed | 1x/day | 1 min | 30 |
| **Total** | | | **~1,850** |

This is close to the 2,000 free minute limit. Options if exceeded:
- Reduce email parser to every 2 hours (halves to ~720 min → total ~1,130)
- Use a self-hosted runner (unlimited free minutes, runs on your own machine)
- Pay for additional minutes ($0.008/min = ~$15/month for overage)

---

## Dependencies (requirements.txt)

```
anthropic>=0.40.0
pyairtable>=2.0.0
google-api-python-client>=2.0.0
google-auth-oauthlib>=1.0.0
google-auth-httplib2>=0.2.0
beautifulsoup4>=4.12.0
lxml>=5.0.0
requests>=2.31.0
tenacity>=8.0.0
```

---

## What Claude Can Fully Own After Migration

After the one-time secrets setup, Claude can autonomously:
- Add new email job board parsers (write parser + update email_parser.py)
- Add new VC portfolio sources (add config to vc_sources.py)
- Modify scoring logic (edit evaluate_job.py or evaluate_company.py)
- Update Claude prompts (edit prompts.py)
- Adjust schedules (edit .yml cron expressions)
- Add new enrichment sources (add module to enrichment/)
- Fix scraper breakage when sites change layouts
- Add new workflows (write new .py + .yml)
- Run tests before pushing (GHA can run pytest on PR)

The only things requiring human intervention:
- Initial GitHub Secrets setup (one-time)
- Rotating expired API keys (infrequent)
- Gmail OAuth re-authorization (rare, if refresh token revoked)
