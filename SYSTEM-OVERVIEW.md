# Tide Pool Job Search Automation System

## Executive Summary

This is a comprehensive, AI-powered job search automation platform that combines:
- **Multi-source job aggregation** (email alerts, web scraping, VC portfolio mining)
- **AI-driven candidate-job fit scoring** using a personal "agent lens"
- **Automated enrichment** with company data (funding, employee count, investor type)
- **Intelligent filtering** based on builder vs. maintainer role classification
- **Centralized tracking** in Airtable with review status workflow

The system is designed around a unique personal positioning framework called "Tide Pool" that evaluates opportunities through the lens of: energy (fill vs. empty), authenticity (sincere vs. perform), and purpose (flourishing vs. process).

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           JOB SOURCE LAYER                                   │
├─────────────────┬─────────────────┬─────────────────┬───────────────────────┤
│  Email Alerts   │   VC Portfolio  │  Direct Scrape  │   Manual/Other        │
│  (10 sources)   │   Scrapers (5)  │  (YC, Costanoa) │                       │
└────────┬────────┴────────┬────────┴────────┬────────┴───────────────────────┘
         │                 │                 │
         ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ENRICHMENT & EVALUATION LAYER                         │
├─────────────────────────────────────────────────────────────────────────────┤
│  • Brave Search API (company data: funding, employees, investors)            │
│  • Claude AI (job fit scoring using Tide Pool Agent Lens)                    │
│  • Builder vs. Maintainer classification                                     │
│  • Auto-disqualification rules (PE-backed, 1000+ employees, etc.)           │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CROSS-SOURCE DEDUPLICATION LAYER                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  Dedup Check Subworkflow → Seen Opportunities Table → Dedup Register         │
│  • Prevents duplicate evaluations across all sources                         │
│  • Saves Claude API costs by skipping already-seen jobs/companies           │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           STORAGE & WORKFLOW LAYER                           │
├─────────────────────────────────────────────────────────────────────────────┤
│  Airtable Base: "Job Search"                                                 │
│  ├── Job Listings (email parser, direct scrapers)                           │
│  ├── Funding Alerts (VC portfolio companies)                                │
│  ├── Seen Opportunities (cross-source deduplication tracking)               │
│  └── Config (API keys, credentials)                                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Workflow Inventory

### 1. Job Alert Email Parser (v3-32)
**Purpose**: Automatically parse job alert emails from 10 different job boards and aggregate into Airtable.

**Supported Sources**:
| Source | Email Domain | Parse Method |
|--------|--------------|--------------|
| LinkedIn | jobs-listings@linkedin.com, jobalerts-noreply@linkedin.com | URL + text extraction |
| Indeed | indeed.com | URL + "at" pattern |
| Built In | builtin.com | HTML card structure (company div + title div) |
| Wellfound | wellfound.com | Job pattern + employee count |
| Himalayas | himalayas.app | URL slug parsing |
| Remotive | remotive.com | HTML list items |
| Welcome to the Jungle | welcometothejungle.com | SendGrid tracking links |
| Jobright | jobright.ai | HTML id-based selectors (updated 2026) |
| Google Careers | careers-noreply@google.com | Careers URL parsing |
| Bloomberry | bloomberry.com | Numbered job list pattern |

**Pipeline**:
```
Gmail API → Identify Source → Parse Jobs → Dedup → Map Fields →
Prefilter (Builder/Maintainer) → Brave Search Enrichment →
Claude AI Scoring → Airtable
```

**Key Features**:
- Base64/quoted-printable decoding
- Source-specific HTML parsers
- Deduplication against existing Airtable records
- Builder vs. Maintainer role classification
- Company enrichment via Brave Search API
- AI scoring using Tide Pool Agent Lens

---

### 2. Work at a Startup Scraper (v6)
**Purpose**: Scrape Y Combinator's Work at a Startup job board and Costanoa VC portfolio jobs.

**Sources**:
- **Work at a Startup** (workatastartup.com) - YC startups
- **Costanoa Ventures** (jobs.costanoa.vc) - Early-stage portfolio

**Technical Approach**:
- Browserless.io for headless browser scraping
- YC account authentication for full job access
- Consider platform (Costanoa) serverInitialData extraction
- Filters for support/success + leadership keywords

**Schedule**: Every 6 hours

**Pipeline** (v6 - uses standardized evaluation sub-routine):
```
Schedule → Get Config → Fetch Profile (GitHub) →
Browserless Scrape (YC + Costanoa) → Parse & Filter → Dedup →
Prefilter → Brave Search Enrichment → Build Prompt → Wait →
Call Claude API → Parse Response → Airtable
```

**v6 Changes**: Now uses the same 7-node modular evaluation chain as the Email Parser, enabling:
- Dynamic Tide Pool profile fetching from GitHub
- Brave Search company enrichment
- Consistent scoring across all job sources

---

### 3. VC Portfolio Scrapers (v22 series)
**Purpose**: Mine VC portfolio companies for potential job opportunities at early-stage startups.

**Four Thematic Scrapers**:

| Scraper | VCs Covered | Schedule | Method |
|---------|-------------|----------|--------|
| **Healthcare v25** | WhatIf, Leadout, Flare Capital, 7wireVentures, Oak HC/FT, Cade Ventures, Hustle Fund | Tue/Fri 8am | Browserless + Static |
| **Climate Tech v23** | Khosla Ventures, Congruent, Prelude, Lowercarbon | Mon/Thu 8am | Browserless + Static |
| **Social Justice v25** | Kapor Capital, Backstage, Harlem, Collab | Wed/Sat 8am | Sitemap + Static |
| **Enterprise v26** | Unusual, First Round, Essence, K9 Ventures, Precursor, M25, GoAhead | Mon/Thu 8am | Mixed (Sitemap, Static, Browserless) |
| **Micro-VC v13** | Pear VC, Floodgate, Afore, Unshackled, 2048, **Y Combinator** | Tue/Fri 8am | Browserless + Infinite Scroll |

**All VC scrapers use the shared `Enrich & Evaluate Pipeline.json` subworkflow** for deduplication, enrichment, and evaluation.

**Technical Approaches**:
- Sitemap XML parsing (Kapor Capital)
- Browserless headless scraping (dynamic sites)
- Static company lists (for VCs without scrapable portfolios)

**Pipeline** (all scrapers use shared subworkflow):
```
Schedule → Fetch Portfolio Data → Parse Companies → Merge →
Combine All VCs → Execute Enrich & Evaluate Pipeline
                              ↓
              ┌───────────────────────────────────┐
              │  SHARED PIPELINE SUBWORKFLOW      │
              │  - Airtable deduplication         │
              │  - Brave Search enrichment        │
              │  - Auto-disqualification          │
              │  - Claude AI evaluation           │
              │  - Airtable record creation       │
              └───────────────────────────────────┘
```

---

### 4. Standardized Evaluation Sub-Routine
**Purpose**: Modular 7-node evaluation chain shared across all workflows.

**Node Chain**:
```
Fetch Profile → Brave Search Company → Parse Enrichment →
Build Prompt → Wait (Rate Limit) → Call Claude API → Parse Response
```

**Design Principles**:
- **Modularity**: Each node has single responsibility
- **Swappable**: Can replace Brave with Clearbit, Claude with OpenAI, etc.
- **Consistent Output**: Same fields across all job sources
- **Dynamic Profile**: Tide Pool Agent Lens fetched from GitHub at runtime

**Enrichment Capabilities**:
- Company data enrichment via Brave Search API
- Employee count, funding stage, total funding extraction
- PE vs. VC investor detection (35+ PE firm names)
- Founded year / company age calculation
- Auto-disqualifier detection

**Auto-Disqualifiers**:
- PE-backed company
- 1,000+ employees
- $500M+ total funding
- Public company
- Known large companies (Anthropic, Google, Meta, etc.)
- Healthcare compliance requirements (skills mismatch)
- Zombie companies (7+ years old, still early stage, <100 employees)

**See Also**: `ARCHITECTURE.md` for detailed data flow diagrams

---

### 5. Feedback Loop Workflows
**Purpose**: Weekly AI-powered analysis to continuously improve the scoring system based on user decisions.

These workflows create a **closed-loop feedback system** that learns from manual review decisions (Applied, Not a Fit) to refine the Tide Pool Agent Lens over time.

#### Feedback Loop - Not a Fit (Rejected Jobs)
**Schedule**: Weekly, Monday 9:00am

**What it does**:
- Queries Airtable for jobs marked "Not a Fit" OR any "Passed*" variant (Passed, Passed (PE), Passed (Location), Passed (Company Specific)) in the past 7 days
- Sends aggregated data to Claude (Sonnet) for pattern analysis
- Identifies common rejection patterns and potential rule improvements
- Emails a structured HTML report with actionable recommendations

**Analysis Output**:
| Section | Description |
|---------|-------------|
| **Patterns Identified** | Common characteristics of rejected jobs |
| **Suggested New Disqualifiers** | Rules to add (e.g., "Requires agency experience") |
| **Scoring Adjustments** | Changes to existing point penalties |
| **Working Well** | Current rules that correctly filtered poor fits |

**Pipeline**:
```
Schedule → Query "Not a Fit" Jobs → Aggregate → Fetch Lens →
Build Analysis Prompt → Claude (Sonnet) → Parse Response → Email Report
```

#### Feedback Loop - Applied
**Schedule**: Weekly, Monday 9:30am

**What it does**:
- Queries Airtable for jobs marked "Applied" in the past 7 days
- Calculates score distribution statistics (min, max, avg, median)
- Sends to Claude (Sonnet) for calibration analysis
- Identifies if good jobs are scoring too low and patterns worth reinforcing
- Emails a structured HTML report with calibration recommendations

**Analysis Output**:
| Section | Description |
|---------|-------------|
| **Score Distribution** | Stats on applied job scores (identify calibration drift) |
| **Calibration Issues** | Jobs that scored low but were worth applying to |
| **New Positive Signals** | Patterns not currently scored that should boost points |
| **Positive Signals Found** | What made these jobs attractive |
| **Working Well** | Scoring rules that correctly identified good fits |

**Pipeline**:
```
Schedule → Query "Applied" Jobs → Aggregate → Calculate Stats →
Fetch Lens → Build Analysis Prompt → Claude (Sonnet) → Parse Response → Email Report
```

**Why Claude Sonnet (not Haiku)?**
These are weekly strategic analyses requiring nuanced pattern recognition across multiple jobs, not high-volume individual scoring. The higher capability model provides better insights for refining the evaluation framework.

---

### 6. Cross-Source Deduplication Subworkflows
**Purpose**: Prevent duplicate evaluations across all job sources, saving Claude API costs.

The dedup system uses a central `Seen Opportunities` table to track all processed jobs and companies.

#### Dedup Check Subworkflow
- **Called by**: Job Evaluation Pipeline v3, Enrich & Evaluate Pipeline v3
- **Input**: Job/company data with company name, title, source
- **Process**:
  1. Generate normalized dedup key (`job:{company}:{title}` or `company:{company}`)
  2. Query Seen Opportunities table for existing record
  3. Return `isDuplicate: true/false` with original data preserved
- **Output**: Dedup result with `_originalJobData` for downstream processing

#### Dedup Register Subworkflow
- **Called by**: Job Evaluation Pipeline v3, Enrich & Evaluate Pipeline v3 (after Airtable upsert)
- **Input**: Key, company, title, source, Airtable record ID
- **Process**: Create record in Seen Opportunities table
- **Output**: Confirmation with seen record ID

**Key Generation**:
- Jobs: `job:{normalized_company}:{normalized_title}`
- Companies: `company:{normalized_company}`

**Normalization**: Lowercase, remove non-alphanumeric characters, trim whitespace

---

### 7. Supporting Workflows

| Workflow | Purpose |
|----------|---------|
| **VC Date Enrichment v5** | Backfill founding dates for existing records |
| **VC Portfolio Backfill Classification** | Reclassify existing portfolio companies |
| **Evaluate Company Subworkflow** | Standalone company evaluation |

---

## The Tide Pool Agent Lens

### Core Concept
A "portable context document" that enables AI agents to understand the user's background, values, and decision-making framework. It transforms generic job matching into deeply personalized opportunity evaluation.

### Evaluation Framework
Three questions for any opportunity:
1. **Does this fill the pool or require emptying?** (Energy)
2. **Can I be sincere or must I perform?** (Authenticity)
3. **Does this create conditions for flourishing or just process flow?** (Purpose)

### Target Profile
- **Role**: VP/Head/Director of Customer Support/Success Operations
- **Company Stage**: Pre-Series A to Series A (0-50 people) ideal
- **Role Type**: "Builder" - creating/scaling support operations from scratch
- **Sectors**: Healthcare, environmental, life sciences, education, audio/music tech
- **Compensation**: $125K+ base
- **Location**: Remote preferred; Providence, Boston, NYC, LA, SF, EU/UK acceptable

### Auto-Disqualifiers (Hard No)
- PE-backed company
- 1,000+ employees
- $500M+ total funding
- Fortune 500/Public company
- IT internal support role
- Quota-carrying CSM role

### Scoring Penalties (Non-Disqualifying)
- 500-999 employees: -15 pts (too large for builder roles but not auto-disqualify)
- Support role without Director/VP/Head title: -15 pts (e.g., "Support Manager", "Customer Support Supervisor")

### Scoring System (100 points)
| Category | Max Points |
|----------|------------|
| Company Stage & Fit | 50 |
| Role Type (Builder vs. Maintainer) | 30 |
| Mission Alignment | 20 |
| Compensation & Location | Bonus/Penalty |

**Decision Thresholds**:
- 80-100: STRONG FIT - Apply immediately
- 60-79: GOOD FIT - Research thoroughly
- 40-59: MARGINAL - Only if exceptional
- <40: SKIP

### Builder vs. Maintainer Classification
**Critical distinction** that drives the entire system.

**Builder Signals** (positive):
- "Build from scratch", "first hire", "founding team"
- "Greenfield", "define playbook", "no playbook"
- "Series A/B", "hypergrowth", "player-coach"
- "Wear many hats", "roll up sleeves", "ambiguity"

**Maintainer Signals** (negative):
- "Book of business", "portfolio of accounts"
- "Retention targets", "renewal rate", "NRR/GRR"
- "Established processes", "proven playbook"
- "Existing team of", "maintain existing"

---

## Data Model

### Airtable Tables

**Job Listings** (tbl6ZV2rHjWz56pP3)
| Field | Type | Description |
|-------|------|-------------|
| Job Title | Text | Role title |
| Company | Text | Company name |
| Location | Text | Work location |
| Source | Select | Origin (LinkedIn, Built In, etc.) |
| Job URL | URL | Link to posting |
| Job ID | Text | Dedup key |
| Salary Info | Text | Compensation if available |
| Date Found | Date | Discovery date |
| Review Status | Select | New, Reviewing, Applied, Not a Fit, Archived |
| Tide-Pool Score | Number | 0-100 fit score |
| Tide-Pool Rationale | Long Text | AI explanation |
| Industry | Text | Company sector |
| Company Stage | Text | Funding stage |
| Role Type | Select | builder/maintainer/hybrid |
| Builder Evidence | Text | Positive signals found |
| Maintainer Evidence | Text | Negative signals found |
| Recommendation | Select | apply/research/skip |

**Funding Alerts** (VC portfolio companies)
- Similar structure for company-level tracking

**Seen Opportunities** (tbll8igHTftSqsTtQ) - Cross-source deduplication
| Field | Type | Description |
|-------|------|-------------|
| Key | Text | Normalized dedup key (e.g., `job:acme:headofcx`) |
| Company | Text | Company name |
| Title | Text | Job title (empty for company records) |
| Record Type | Select | job / company |
| First Source | Text | Original discovery source |
| All Sources | Text | All sources that found this opportunity |
| First Seen | Date | First discovery timestamp |
| Job Record ID | Text | Link to Job Listings record |
| Company Record ID | Text | Link to Funding Alerts record |

**Config** (tblofzQpzGEN8igVS)
| Key | Purpose |
|-----|---------|
| ANTHROPIC_API_KEY | Claude AI scoring |
| BROWSERLESS_TOKEN | Headless browser scraping |
| YC_USER | Work at a Startup login |
| YC_PASSWORD | Work at a Startup login |
| BRAVE_API_KEY | Company enrichment |

---

## Technical Stack

| Component | Technology |
|-----------|------------|
| Workflow Automation | n8n (self-hosted or cloud) |
| AI Scoring | Anthropic Claude API (Haiku model) |
| Company Enrichment | Brave Search API |
| Headless Scraping | Browserless.io |
| Email Integration | Gmail API |
| Data Storage | Airtable |
| Version Control | GitHub (tidepool repo) |

---

## Unique Differentiators

### 1. Personal Agent Lens
Unlike generic job matching, this system uses a deeply personal "lens" document that encodes:
- Career philosophy (tide pool metaphor)
- Values-based evaluation criteria
- Role type preferences (builder vs. maintainer)
- Company stage preferences
- Industry alignment
- Auto-disqualification rules

### 2. Multi-Source Aggregation
Combines 11+ email-based job boards with direct web scraping and VC portfolio mining - sources most job seekers don't systematically track.

### 3. VC Portfolio Mining
Proactively scrapes investor portfolio pages to find companies before they post jobs publicly. Organized by thesis (Healthcare, Climate, Social Justice, Enterprise).

### 4. Builder vs. Maintainer Classification
Novel framework for distinguishing between:
- "Builder" roles (creating from scratch) - highly desired
- "Maintainer" roles (managing existing) - filtered out

### 5. Company Enrichment Pipeline
Automatically enriches every opportunity with:
- Employee count
- Funding stage and total raised
- Investor type (VC vs. PE - critical signal)
- Company age
- Auto-disqualification detection

### 6. AI-Powered Scoring
Claude AI scores every opportunity against the personal lens, providing:
- Numerical score (0-100)
- Role type classification
- Builder/maintainer evidence
- Specific recommendation (apply/research/skip)
- Detailed rationale

### 7. Closed-Loop Feedback System
Weekly automated analysis of user decisions creates a self-improving system:
- **Not a Fit Analysis**: Identifies patterns in rejected jobs to suggest new disqualifiers
- **Applied Analysis**: Calibrates scoring by analyzing what made jobs worth applying to
- AI-generated reports with specific, actionable recommendations
- Enables continuous refinement of the Tide Pool Agent Lens

---

## Productization Opportunities

### Potential Market Gaps This System Addresses

1. **Personal Context-Aware Job Matching**
   - Existing tools match keywords; this matches values, career stage, and working style
   - The "agent lens" concept could be a product category

2. **VC Portfolio Intelligence for Job Seekers**
   - No consumer tools systematically mine VC portfolios for job opportunities
   - Valuable for people targeting specific company stages/sectors

3. **Builder vs. Maintainer Role Classification**
   - Novel framework that could help both job seekers and recruiters
   - Particularly valuable for startup hiring

4. **Multi-Source Job Aggregation with Dedup**
   - Most people manually check multiple boards
   - Unified pipeline with intelligent deduplication

5. **Company Stage/Investor Due Diligence Automation**
   - Automating the "should I apply" research process
   - PE vs. VC detection is particularly valuable

6. **AI-Scored Job Recommendations**
   - Not just "jobs that match your resume"
   - "Jobs that match your career goals and values"

---

## Appendix: Tide Pool Agent Lens (Full Document)

The complete Tide Pool Agent Lens is maintained at:
- GitHub: `https://github.com/zelman/tidepool/blob/main/tide-pool-agent-lens.md`
- Local: `/Users/zelman/Desktop/Quarantine/Side Projects/tidepool/tide-pool-agent-lens.md`

Key sections:
- Core Essence & Pathway Statement
- Values Framework
- Job Search Parameters
- 100-Point Scoring Framework
- Pre-Application Research Checklist
- Investor Type Quick Reference

---

*Document updated: February 2026*
*System Version: Job Alert Email Parser v3-35, Work at a Startup Scraper v12, VC Scrapers v22-v26 + Micro-VC v13, Feedback Loops v1, Dedup Subworkflows v1, Job Evaluation Pipeline v3, Enrich & Evaluate Pipeline v3, evaluation-config v2.2*

**Related Documentation**:
- `ARCHITECTURE.md` - Detailed technical architecture and data flow diagrams
- `Job Alert Email Parser README.md` - Email parser configuration and usage
- `tide-pool-agent-lens.md` - Personal evaluation criteria (GitHub)
- `Feedback Loop - Not a Fit.json` - Weekly pattern analysis for rejected jobs
- `Feedback Loop - Applied.json` - Weekly calibration analysis for applied jobs
- `Dedup Check Subworkflow.json` - Cross-source deduplication lookup
- `Dedup Register Subworkflow.json` - Cross-source deduplication registration
- `Job Evaluation Pipeline v3.json` - Job evaluation with dedup, 500-999 employee penalty, Support title penalty
- `Enrich & Evaluate Pipeline v3.json` - Company evaluation with dedup + Job Listings cross-reference
