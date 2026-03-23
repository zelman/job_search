# Tide Pool Job Search Automation System

## Executive Summary

This is a comprehensive, AI-powered job search automation platform that combines:
- **Multi-source job aggregation** (email alerts, web scraping, VC portfolio mining)
- **AI-driven candidate-job fit scoring** using a personal "agent lens"
- **Automated enrichment** with company data (funding, employee count, investor type)
- **Intelligent multi-tier filtering** with 5 gate tiers and CS hire readiness threshold
- **Centralized tracking** in Airtable with review status workflow

The system is designed around a unique personal positioning framework called "Tide Pool" that evaluates opportunities through the lens of: energy (fill vs. empty), authenticity (sincere vs. perform), and purpose (flourishing vs. process).

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           JOB SOURCE LAYER                                   │
├─────────────────┬─────────────────┬─────────────────┬───────────────────────┤
│  Email Alerts   │   VC Portfolio  │  Direct Scrape  │   API-Based           │
│  (10 sources)   │   Scrapers (5)  │  (YC, Costanoa) │   (First Round)       │
└────────┬────────┴────────┬────────┴────────┬────────┴───────────────────────┘
         │                 │                 │
         ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CROSS-SOURCE DEDUPLICATION LAYER                          │
│  Dedup Check → Seen Opportunities Table → Dedup Register                    │
│  Saves Claude API costs by skipping already-seen jobs/companies             │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ENRICHMENT & EVALUATION LAYER                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ COMPANIES: Enrich & Evaluate Pipeline v9.13 (6-Phase Architecture)    │  │
│  │  Phase 0: Entity Validation (is this a company?)                      │  │
│  │  Phase 1: Brave Search Enrichment + Enhanced Detection                │  │
│  │  Phase 2: Pre-Evaluation Gates (5 Tiers)                             │  │
│  │  Phase 3: Customer Persona Classification                             │  │
│  │  Phase 4: CS Hire Readiness Threshold (>=10)                         │  │
│  │  Phase 5: Full Evaluation + Domain Distance Scoring                   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ JOBS: Job Evaluation Pipeline v6.8                                    │  │
│  │  JD Fetch (Browserless) → Build Prompt → Claude Evaluate → Upsert    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           STORAGE & WORKFLOW LAYER                           │
├─────────────────────────────────────────────────────────────────────────────┤
│  Airtable Base: "Job Search"                                                 │
│  ├── Job Listings (scored job opportunities)                               │
│  ├── Funding Alerts (VC portfolio company evaluations)                      │
│  ├── LinkedIn Connections (network cross-reference)                         │
│  ├── Seen Opportunities (cross-source dedup tracking)                      │
│  └── Indeed Searches (job search configs)                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  Review Status: New → Reviewing → Applied / Not a Fit → Archived             │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FEEDBACK LOOP LAYER                                │
│  ├── Feedback Loop - Not a Fit (weekly pattern analysis)                    │
│  └── Feedback Loop - Applied (weekly calibration analysis)                  │
│  → Email reports → Manual lens updates → Improved scoring                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## v9.13 Pipeline Highlights

The v9.13 pipeline addresses a **4% signal rate** (1/25 companies worth pursuing) from v8.5 through a full redesign:

### Key Features (v9 → v9.13)

| Feature | Purpose | Impact |
|---------|---------|--------|
| **Phase 0: Entity Validation** | Catch non-companies (podcasts, media, nonprofits) | Saves API calls on invalid entities |
| **Enhanced Acquisition Detection** | PE portfolio patterns (Jonas, Constellation, Volaris) | Catches PE-owned companies |
| **GTM Motion Gates** | PLG-dominant detection, pre-sales function companies | Filters companies without enterprise CS need |
| **Stale Company Gates** | 3+ years since funding, shrinking headcount | Filters zombie companies |
| **Software-First Check** | Services businesses, hardware-with-software | Filters non-SaaS companies |
| **CS Hire Readiness Threshold** | Quick Claude call, must score >=10 | Filters timing mismatches |
| **Domain Distance Scoring** | +5 healthcare to -10 physical security | Penalizes high-distance domains |
| **Unicorn Gate** (v9.8) | >$1B valuation = DQ | Catches late-stage unicorns |
| **Company Age Gate** (v9.8) | >8 years old = DQ, 5-8 years = flag | Filters stale startups |
| **Employee Corroboration** (v9.9) | Median of multiple mentions, suspicious count flagging | Catches inflated/deflated headcounts |
| **Funding Recency Penalty** (v9.9) | 2yr=-5pts, 3yr=-10pts, 4yr=-15pts | Penalizes zombie startups |
| **CX Tooling Detection** (v9.9) | Helpdesk/chatbot vendors flagged | They sell to CS, don't need CS leadership |
| **PE Merger/Rebrand Detection** (v9.10) | 45+ merger keywords, predecessor name extraction | Catches PE roll-ups masquerading as startups |
| **Bucket Enforcement** (v9.13) | Score floor detection, VC category labels | Ensures PASS/WATCH/APPLY consistency |

### Gate Tiers

| Tier | Gate Type | Examples |
|------|-----------|----------|
| **Tier 1** | Hard Gates | PE-backed, >350 emp, >$500M funding, >$1B valuation, acquired, >8yr old |
| **Tier 2** | Sector Gates | Biotech, hardware, crypto, fintech, insurtech, not software-first |
| **Tier 3** | GTM Motion | PLG-dominant, pre-sales function company, developer-as-customer |
| **Tier 4** | Stale Company | 3+ years since funding, shrinking signals |
| **Tier 5** | Soft Flags | <15 employees, 200-350 employees, 5-8 years old |

---

## Workflow Inventory

### Job Sources

| Workflow | Version | Description | Schedule |
|----------|---------|-------------|----------|
| **Job Alert Email Parser** | v3-43 | 10 email job boards + OmniJobs scraping | Hourly |
| **Work at a Startup Scraper** | v12 | YC Work at a Startup job board | Every 6 hours |
| **Indeed Job Scraper** | v6 | Indeed scraping with internal loop architecture | Configurable |
| **First Round Jobs Scraper** | v1 | First Round Capital talent network API | Tue/Fri 7am |
| **Health Tech Nerds Scraper** | v1 | jobs.healthtechnerds.com static JSON | Every 6 hours |
| **CS Insider Scraper** | v1.7 | csinsider.co/job-board (Notion embed) | Tue/Fri 7am |

### VC Portfolio Scrapers

| Scraper | Version | VCs Covered |
|---------|---------|-------------|
| **Healthcare** | v27 | 14 VCs: Flare Capital, 7wireVentures, Oak HC/FT, Digitalis, a16z Bio+Health, Healthworx, Cade, Hustle Fund, Martin Ventures, Town Hall Ventures, Transformation Capital, Brewer Lane, Mainsail Partners, Five Elms |
| **Climate Tech** | v23 | Khosla Ventures, Congruent, Prelude, Lowercarbon |
| **Social Justice** | v25 | Kapor Capital, Backstage, Harlem, Collab |
| **Enterprise** | v27 | 15 VCs: Unusual, First Round, Khosla, Kapor, WhatIf, WXR, Leadout, Notable, Headline, PSL, Trilogy, K9, Precursor, M25, GoAhead |
| **Micro-VC** | v15 | 5 VCs: Pear VC, Afore, Unshackled, 2048, **Y Combinator** |

All VC scrapers use the shared **Enrich & Evaluate Pipeline v9.13**.

### Shared Subworkflows

| Workflow | Version | Purpose |
|----------|---------|---------|
| **Enrich & Evaluate Pipeline** | v9.13 | Company evaluation (6-phase architecture) |
| **Job Evaluation Pipeline** | v6.8 | Job evaluation with JD fetching |
| **Dedup Check Subworkflow** | v1 | Cross-source dedup lookup |
| **Dedup Register Subworkflow** | v1 | Cross-source dedup registration |
| **Funding Alerts Rescore** | v4.9.2 | Standalone rescore workflow |

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
- **Company Stage**: Series A to Series B (20-100 people) ideal
- **Role Type**: "Builder" - creating/scaling support operations from scratch
- **Sectors**: Healthcare B2B SaaS, enterprise SaaS, developer tools with enterprise motion
- **Compensation**: $125K+ base
- **Location**: Remote preferred; Providence, Boston, NYC, LA, SF, EU/UK acceptable

### Builder vs. Maintainer Classification

**Critical distinction** that drives the entire system.

**Builder Signals** (positive):
- "Build from scratch", "first hire", "founding team"
- "Greenfield", "define playbook", "no playbook"
- "Series A/B", "hypergrowth", "player-coach"

**Maintainer Signals** (negative):
- "Book of business", "portfolio of accounts"
- "Established processes", "proven playbook"
- "Existing team of", "maintain existing"

---

## Scoring System (100 Points + Domain Distance)

### Base Categories

| Category | Points | What It Measures |
|----------|--------|------------------|
| CS Hire Readiness | 0-25 | Does company need this hire NOW? |
| Stage & Size Fit | 0-25 | Right inflection point for builder role? |
| Role Mandate | 0-20 | Builder (0-to-1) vs Maintainer (scale existing)? |
| Sector & Mission | 0-15 | Alignment with healthcare/B2B SaaS experience? |
| Outreach Feasibility | 0-15 | Network access, warm intro potential? |

### Domain Distance Modifier

| Domain | Modifier |
|--------|----------|
| Healthcare B2B SaaS | +5 |
| Clinical Operations | +5 |
| Care Coordination | +4 |
| Patient Engagement | +3 |
| Developer Tools | +2 |
| IT Operations/ITSM | -8 |
| Vertical Retail POS | -8 |
| Physical Security | -10 |

### Decision Thresholds

| Score | Classification | Action |
|-------|----------------|--------|
| 60+ | **APPLY** | Worth pursuing |
| 40-59 | **WATCH** | Monitor for changes |
| <40 | **PASS** | Not a fit |

---

## Unique Differentiators

### 1. Personal Agent Lens
Unlike generic job matching, this system uses a deeply personal "lens" document that encodes career philosophy, values-based criteria, and role type preferences.

### 2. Multi-Source Aggregation
Combines 10+ email-based job boards with direct web scraping, VC portfolio mining, and API-based sources - sources most job seekers don't systematically track.

### 3. VC Portfolio Mining
Proactively scrapes investor portfolio pages to find companies before they post jobs publicly. Organized by thesis (Healthcare, Climate, Social Justice, Enterprise, Micro-VC).

### 4. Six-Phase Evaluation Architecture
Multi-tier filtering that saves 90%+ on API costs while catching false positives at every stage: entity validation, enrichment, gates, persona, CS readiness, and full evaluation.

### 5. Domain Distance Scoring
Novel approach to penalizing companies in domains far from the candidate's experience while rewarding target domains.

### 6. Closed-Loop Feedback System
Weekly automated analysis of user decisions creates a self-improving system that continuously refines the evaluation criteria.

---

## Technical Stack

| Component | Technology |
|-----------|------------|
| Workflow Automation | n8n (self-hosted or cloud) |
| AI Scoring | Anthropic Claude API (Haiku 4.5) |
| Company Enrichment | Brave Search API |
| Headless Scraping | Browserless.io |
| Email Integration | Gmail API |
| Data Storage | Airtable |
| Version Control | GitHub |

---

## FigJam Diagrams

Interactive diagrams for visual reference:

- **[System Architecture v9.5](https://www.figma.com/online-whiteboard/create-diagram/b857c91d-d47d-4e6b-a2ff-352e76022940)** - Overview of all scrapers, pipelines, and Airtable tables
- **[v9.5 Pipeline Gate Flow](https://www.figma.com/online-whiteboard/create-diagram/8f8d33b6-7b5f-44ce-b606-45a74ef3e2d8)** - 6-phase architecture with decision points
- **[v9.5 Scoring Architecture](https://www.figma.com/online-whiteboard/create-diagram/916baf11-8e56-4d7a-a2f7-5def6b74042f)** - 100-point scoring with domain distance modifiers

---

## Related Documentation

- `CLAUDE.md` - Claude Code project instructions and workflow IDs
- `ARCHITECTURE.md` - Detailed technical architecture and data flow
- `SCORING-ARCHITECTURE.md` - Six-phase scoring system details
- `ENHANCEMENT-IDEAS.md` - Future improvement roadmap
- `tide-pool-agent-lens.md` - Personal evaluation criteria (GitHub)

---

*Document updated: March 23, 2026*
*System Version: Enrich & Evaluate Pipeline v9.13, Job Evaluation Pipeline v6.8, Funding Alerts Rescore v4.9.2, Job Alert Email Parser v3-43, VC Scrapers v15-v27*
