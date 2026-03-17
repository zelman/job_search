# Tide Pool Job Search System Architecture

## Overview

This document details the technical architecture of the Tide Pool job search automation system, with emphasis on the modular evaluation sub-routine that enables consistent AI-powered job scoring across all workflows.

---

## System Components

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              DATA SOURCES                                        │
├─────────────────────┬─────────────────────┬─────────────────────────────────────┤
│   Email Parsers     │   Web Scrapers      │   VC Portfolio Miners               │
│   (10 job boards)   │   (YC, CS Insider)  │   (5 thematic scrapers)             │
└──────────┬──────────┴──────────┬──────────┴──────────────┬──────────────────────┘
           │                     │                         │
           ▼                     ▼                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     CROSS-SOURCE DEDUPLICATION LAYER                             │
│  ├── Dedup Check Subworkflow (before evaluation)                                │
│  ├── Seen Opportunities Table (central registry)                                │
│  └── Dedup Register Subworkflow (after Airtable upsert)                        │
└──────────┬──────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                 STANDARDIZED EVALUATION SUB-ROUTINES                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ JOBS: Job Evaluation Pipeline v6.6                                       │    │
│  │  JD Fetch → Parse → Build Prompt → Claude Evaluate → Parse Response     │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ COMPANIES: Enrich & Evaluate Pipeline v9.9                               │    │
│  │  Phase 0: Entity Validation                                              │    │
│  │  Phase 1: Brave Search Enrichment                                        │    │
│  │  Phase 2: Pre-Evaluation Gates (5 Tiers)                                │    │
│  │  Phase 3: Customer Persona Classification                                │    │
│  │  Phase 4: CS Hire Readiness Threshold                                    │    │
│  │  Phase 5: Full Evaluation + Domain Distance                              │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────┬──────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              AIRTABLE STORAGE                                    │
│  ├── Job Listings (scored job opportunities)                                    │
│  ├── Funding Alerts (VC portfolio company evaluations)                          │
│  ├── LinkedIn Connections (network cross-reference)                             │
│  ├── Seen Opportunities (cross-source dedup registry)                          │
│  └── Indeed Searches (Indeed job search configs)                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│  Review Status: New → Reviewing → Applied / Not a Fit → Archived                 │
└──────────────────────────────────┬──────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           FEEDBACK LOOP LAYER                                    │
│  ├── Feedback Loop - Not a Fit (weekly pattern analysis)                        │
│  └── Feedback Loop - Applied (weekly calibration analysis)                      │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Enrich & Evaluate Pipeline v9.9 Architecture

The v9.9 pipeline represents a **full redesign** addressing a 4% signal rate (1/25 companies worth pursuing).

### Six-Phase Flow

```
INPUT (company from scraper)
    │
    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ PHASE 0: ENTITY VALIDATION                                                 │
│   • Is this an operating company? (not podcast/media/nonprofit)           │
│   • Pattern matching: .org, .edu, podcast, blog, newsletter               │
│   • Fail → Exit: "Invalid Entity"                                          │
└───────────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ PHASE 1: ENRICHMENT (Brave Search)                                         │
│   • Fetch company data via Brave Search API                                │
│   • Extract: employees, funding, stage, geography                          │
│   • NEW: Enhanced acquisition detection (PE portfolio patterns)           │
│   • NEW: GTM motion signals (PLG vs enterprise)                           │
│   • NEW: Software-first check (not services/hardware)                     │
│   • NEW: Stale company detection (shrinking headcount)                    │
└───────────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ PHASE 2: PRE-EVALUATION GATES (5 Tiers)                                    │
│                                                                            │
│ TIER 1 - HARD GATES (binary, immediate exit):                             │
│   PE-backed, >350 emp, >$500M funding, >$1B valuation, public,            │
│   Series D+, acquired, Fortune 500, invalid entity, >8yr old              │
│                                                                            │
│ TIER 2 - SECTOR GATES:                                                    │
│   Biotech, hardware, crypto, consumer, HR Tech, marketplace,              │
│   not software-first (services, hardware+software)                        │
│                                                                            │
│ TIER 3 - GTM MOTION GATES:                                                │
│   PLG-dominant (no enterprise CS need), pre-sales function company        │
│                                                                            │
│ TIER 4 - STALE COMPANY GATES:                                             │
│   3+ years since funding, shrinking headcount signals                     │
│                                                                            │
│ TIER 5 - SOFT FLAGS (proceed but flag):                                   │
│   <15 employees, 200-350 employees, $75M+ funding, 5-8yr old              │
└───────────────────────────────────────────────────────────────────────────┘
    │
    ├──────────────────────┐
    │ Disqualified         │
    ▼                      ▼
┌─────────────┐     ┌───────────────────────────────────────────────────────┐
│ Exit:       │     │ PHASE 3: PERSONA CLASSIFICATION (Claude Haiku)        │
│ Score = 0   │     │   • Classify: business-user, employee-user,           │
│ Auto-DQ     │     │     developer, mixed                                  │
└─────────────┘     │   • Developer + <50 emp → Auto-pass                   │
                    │   • Developer + 50+ emp + <3 enterprise signals →     │
                    │     Auto-pass                                          │
                    │   • Developer + 50+ emp + 3+ signals → Proceed        │
                    │   • Employee-user + <50 emp → Auto-pass               │
                    │   • Business-user/mixed → Proceed to CS Readiness     │
                    └───────────────────────────────────────────────────────┘
                        │
                        ├──────────────────────┐
                        │ Auto-pass            │
                        ▼                      ▼
                 ┌─────────────┐     ┌───────────────────────────────────────┐
                 │ Exit:       │     │ PHASE 4: CS HIRE READINESS (Haiku)    │
                 │ Developer/  │     │   • Quick Claude call: "Is company    │
                 │ Employee    │     │     actively building CS?"            │
                 │ Auto-Pass   │     │   • Must score >= 10 to proceed       │
                 └─────────────┘     │   • Fail → Exit: "Below Threshold"    │
                                     └───────────────────────────────────────┘
                                         │
                                         ├──────────────────────┐
                                         │ Below threshold      │
                                         ▼                      ▼
                                  ┌─────────────┐     ┌─────────────────────┐
                                  │ Exit:       │     │ PHASE 5: FULL EVAL  │
                                  │ CS Below    │     │   • 100-pt scoring  │
                                  │ Threshold   │     │   • Domain distance │
                                  └─────────────┘     │   • APPLY/WATCH/PASS│
                                                      └──────────┬──────────┘
                                                                 │
                                                                 ▼
                                                      ┌─────────────────────┐
                                                      │ OUTPUT              │
                                                      │ Airtable record     │
                                                      │ with score + status │
                                                      └─────────────────────┘
```

### New Detection Patterns (v9)

| Pattern Type | Implementation | Purpose |
|--------------|----------------|---------|
| **PE Portfolio** | Jonas Software, Constellation, Volaris, Harris Computer, TSS | Catch PE-owned via acquisition |
| **Current Ownership** | "currently owned by", "majority stake", "portfolio of" | Distinguish from investor history |
| **PLG Signals** | free tier, self-serve, freemium, community edition, open source | Identify PLG-dominant companies |
| **Enterprise Signals** | enterprise sales, account executive, implementation team, ACV | Identify enterprise CS need |
| **Services Business** | creative services, consulting, staffing, managed services | Not software-first |
| **Hardware+Software** | sensor platform, device+cloud, physical product | Hardware masquerading as SaaS |
| **Pre-Sales Function** | presales platform, demo automation, CPQ, sales engineering | Pre-sales tools |
| **Stale Signals** | layoff, restructuring, downsizing, workforce reduction | Shrinking company |
| **Geography** | headquartered in, based in, US city names, EMEA/APAC | US vs non-US market |

---

## Job Evaluation Pipeline v6.6 Architecture

```
INPUT (job from scraper/email parser)
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ JD FETCH (Browserless)                                                       │
│   • Fetch full job description from URL                                      │
│   • Extract company info, requirements, responsibilities                     │
└───────────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ BUILD PROMPT                                                                 │
│   • Construct evaluation prompt with Tide Pool Agent Lens                   │
│   • Include JD content, enrichment data                                      │
└───────────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ CLAUDE EVALUATE (Haiku)                                                      │
│   • 100-point scoring                                                        │
│   • Builder vs Maintainer classification                                     │
│   • Recommendation: apply/research/skip                                      │
└───────────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ AIRTABLE UPSERT                                                              │
│   • v6.6: Batch 4 fixes (employee corroboration, funding recency,          │
│     CS readiness capping, CX tooling vendor detection)                      │
│   • Source field preserved with fallback lookups                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## Cross-Source Deduplication

### Purpose

Prevent duplicate evaluations when the same job/company appears from multiple sources. Saves Claude API costs and keeps records clean.

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           DEDUP CHECK SUBWORKFLOW                                │
│                                                                                  │
│  Input: { company, title, source, recordType }                                  │
│         │                                                                        │
│         ▼                                                                        │
│  ┌──────────────────┐                                                           │
│  │ Generate Key     │  job:acme:headofcx  or  company:acme                      │
│  │ (normalize)      │  Lowercase, remove non-alphanumeric, trim                 │
│  └────────┬─────────┘                                                           │
│           │                                                                      │
│           ▼                                                                      │
│  ┌──────────────────┐                                                           │
│  │ Query Airtable   │  Check Seen Opportunities table                           │
│  │ Seen Opps        │                                                           │
│  └────────┬─────────┘                                                           │
│           │                                                                      │
│  Output: { isDuplicate, key, existingRecordId }                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                          DEDUP REGISTER SUBWORKFLOW                              │
│                                                                                  │
│  Input: { key, company, title, source, recordType, airtableRecordId }           │
│         │                                                                        │
│         ▼                                                                        │
│  ┌──────────────────┐                                                           │
│  │ Create Seen      │  Airtable create in Seen Opportunities table              │
│  │ Record           │  Links to Job Listings or Funding Alerts record          │
│  └──────────────────┘                                                           │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Key Generation

| Record Type | Key Format | Example |
|-------------|------------|---------|
| Job | `job:{normalized_company}:{normalized_title}` | `job:acme:headofcx` |
| Company | `company:{normalized_company}` | `company:acme` |

---

## Job Listings Cross-Reference

The Enrich & Evaluate Pipeline v9.9 checks if a company already has active job postings.

**Fields in Funding Alerts:**
- `Has Active Job Posting` (checkbox)
- `Has CX Job Posting` (checkbox)
- `Matching Job Titles` (text)

**Status:**
- `Immediate Action` - Company has both funding alert AND active CX job posting

**Note:** LinkedIn network matching is currently **disabled in v9** to fix a duplicate record bug. The two parallel merge paths (Job Check + LinkedIn Check) both fed into the downstream node. Re-enabling requires single-path architecture.

---

## Feedback Loop Architecture

### Feedback Loop - Not a Fit

**Schedule:** Weekly, Monday 9:00am

```
Query "Not a Fit" Jobs → Aggregate → Claude (Sonnet) Analysis → Email Report

Output:
- Patterns in rejected jobs
- Suggested new disqualifiers
- Scoring adjustments
- What's working well
```

### Feedback Loop - Applied

**Schedule:** Weekly, Monday 9:30am

```
Query "Applied" Jobs → Calculate Stats → Claude (Sonnet) Analysis → Email Report

Output:
- Score distribution (min, max, avg, median)
- Calibration issues (good jobs scoring too low)
- New positive signals to add
- What's working well
```

---

## Workflow Inventory

### Job Sources

| Workflow | Version | Sources | Schedule |
|----------|---------|---------|----------|
| Job Alert Email Parser | v3-43 | 10 email job boards + OmniJobs | Hourly |
| Work at a Startup Scraper | v12 | YC Work at a Startup | Every 6 hours |
| Indeed Job Scraper | v6 | Indeed search configs | Configurable |
| First Round Jobs Scraper | v1 | First Round Capital talent network | Tue/Fri 7am |
| Health Tech Nerds Scraper | v1 | jobs.healthtechnerds.com static JSON | Every 6 hours |
| CS Insider Scraper | v1.7 | csinsider.co/job-board (Notion embed) | Tue/Fri 7am |

### VC Portfolio Scrapers

| Scraper | Version | VCs Covered | Schedule |
|---------|---------|-------------|----------|
| Healthcare | v27 | 14 VCs: Flare, 7wireVentures, Oak HC/FT, Digitalis, etc. | Tue/Fri 8am |
| Climate Tech | v23 | Khosla, Congruent, Prelude, Lowercarbon | Mon/Thu 8am |
| Social Justice | v25 | Kapor, Backstage, Harlem, Collab | Wed/Sat 8am |
| Enterprise | v27 | 15 VCs: Unusual, First Round, Khosla, Kapor, WhatIf, WXR, Leadout, Notable, Headline, PSL, Trilogy, K9, Precursor, M25, GoAhead | Mon/Thu 8am |
| Micro-VC | v15 | 5 VCs: Pear, Afore, Unshackled, 2048, **Y Combinator** | Tue/Fri 8am |

All VC scrapers use the shared **Enrich & Evaluate Pipeline v9.9**.

### Shared Subworkflows

| Workflow | Version | Purpose |
|----------|---------|---------|
| Enrich & Evaluate Pipeline | v9.9 | Company evaluation with 6-phase architecture |
| Job Evaluation Pipeline | v6.6 | Job evaluation with JD fetching |
| Dedup Check Subworkflow | v1 | Cross-source dedup lookup |
| Dedup Register Subworkflow | v1 | Cross-source dedup registration |
| Funding Alerts Rescore | v4.6 | Standalone rescore (HTTP Request bypass) |

---

## API Dependencies

| Service | Purpose | Rate Limit |
|---------|---------|------------|
| **Anthropic Claude API** | Scoring (Haiku) | ~1 req/30s |
| **Brave Search API** | Company enrichment | 2,000/month free |
| **Gmail API** | Email fetching/labeling | Generous |
| **Airtable API** | Data storage | 5 req/sec |
| **Browserless.io** | Headless scraping | Usage-based |

---

## Airtable Reference

**Base ID:** `appFEzXvPWvRtXgRY` (Job Search)

| Table | ID | Purpose |
|-------|-----|---------|
| **Funding Alerts** | `tbl7yU6QYfIFSC2nD` | Company evaluations from VC scrapers |
| **Job Listings** | `tbl6ZV2rHjWz56pP3` | Job evaluations from job scrapers |
| **LinkedIn Connections** | `tbliKHRPEVI6SceJX` | Imported LinkedIn network |
| **Seen Opportunities** | `tbll8igHTftSqsTtQ` | Cross-source dedup registry |
| **Indeed Searches** | `tblofzQpzGEN8igVS` | Indeed job search configs |

---

## n8n Workflow IDs

| Workflow | ID | Used By |
|----------|-----|---------|
| **Enrich & Evaluate Pipeline v9.9** | `UPDATE_AFTER_IMPORT` | All VC scrapers |
| **Job Evaluation Pipeline v6.6** | `v24qHkIsp8GVCwFkscHP8` | Job scrapers |
| **Dedup Check Subworkflow** | `bBjeG_RXRI10eAA5TiN7n` | Both pipelines |
| **Dedup Register Subworkflow** | `MDzcHPZMySqn1DrGh8J0-` | Both pipelines |

---

## FigJam Diagrams

Interactive diagrams for visual reference:

- **[System Architecture v9.5](https://www.figma.com/online-whiteboard/create-diagram/b857c91d-d47d-4e6b-a2ff-352e76022940)** - Overview of all scrapers, pipelines, and Airtable tables
- **[v9.5 Pipeline Gate Flow](https://www.figma.com/online-whiteboard/create-diagram/8f8d33b6-7b5f-44ce-b606-45a74ef3e2d8)** - 5-phase architecture with decision points
- **[v9.5 Scoring Architecture](https://www.figma.com/online-whiteboard/create-diagram/916baf11-8e56-4d7a-a2f7-5def6b74042f)** - 100-point scoring with domain distance

---

## Version History

| Date | Change |
|------|--------|
| 2026-03-16 | **v9.9 Batch 4 Fixes**: Employee corroboration (median), funding recency penalties, CS readiness capping, CX tooling vendor detection |
| 2026-03-16 | VC scraper cleanup: Removed Essence, Costanoa, Golden (Enterprise v27), Floodgate (Micro-VC v15) |
| 2026-03-16 | Job Evaluation Pipeline v6.6: Ported Batch 4 fixes from company pipeline |
| 2026-03-15 | v9.8: Unicorn gate (>$1B), company age gate (>8yr), evidence-based CS readiness |
| 2026-03-15 | Job Evaluation Pipeline v6.3-v6.5: Major overhaul, sector gates, code review fixes |
| 2026-03-14 | v9.7: Expanded sector gates (fintech, construction, insurtech, etc.), developer persona gate |
| 2026-03-11 | **v9 Full Redesign**: 6-phase architecture, entity validation, GTM motion gates, CS readiness threshold, domain distance scoring |
| 2026-03-09 | v8.5: 8 scoring fixes, employee-user persona, stricter SaaS gate |
| 2026-03-06 | v8.4: Customer Persona Gate, two-tier architecture |
| 2026-02-27 | Y Combinator added to Micro-VC v13 |
| 2026-02-27 | Job Evaluation Pipeline v3 with scoring penalties |
| 2026-02-26 | Cross-source deduplication system |
| 2026-02-24 | Feedback loops (Not a Fit, Applied) |

---

*Last updated: March 16, 2026*
