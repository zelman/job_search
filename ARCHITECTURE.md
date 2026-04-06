# Tide Pool System Architecture

*Last updated: April 2026*
*Pipeline versions: Enrich & Evaluate v9.18, Job Evaluation v6.10, Rescore v4.15*

---

## System Overview

AI-powered job search automation combining multi-source aggregation, intelligent filtering, and centralized tracking.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           JOB SOURCE LAYER                                   │
├─────────────────┬─────────────────┬─────────────────┬───────────────────────┤
│  Email Alerts   │   VC Portfolio  │  Direct Scrape  │   API-Based           │
│  (10 sources)   │   Scrapers (6)  │  (YC, CS Insider)│  (First Round, Indeed)│
└────────┬────────┴────────┬────────┴────────┬────────┴───────────────────────┘
         │                 │                 │
         ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CROSS-SOURCE DEDUPLICATION LAYER                          │
│  Dedup Check → Seen Opportunities Table → Dedup Register                    │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ENRICHMENT & EVALUATION LAYER                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  COMPANIES: Enrich & Evaluate Pipeline v9.18 (6-Phase Architecture)         │
│  JOBS: Job Evaluation Pipeline v6.10                                         │
│  RESCORE: Funding Alerts Rescore v4.15 (config-driven)                       │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AIRTABLE STORAGE                                   │
│  ├── Job Listings (scored jobs)                                              │
│  ├── Funding Alerts (VC portfolio evaluations)                               │
│  ├── LinkedIn Connections (network cross-reference)                          │
│  └── Seen Opportunities (dedup registry)                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  Status: New → Reviewing → Applied / Not a Fit → Archived                    │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FEEDBACK LOOP LAYER                                │
│  ├── Feedback Loop - Not a Fit (weekly pattern analysis)                    │
│  └── Feedback Loop - Applied (weekly calibration)                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Six-Phase Scoring Architecture

The company evaluation pipeline uses a 6-phase architecture optimizing for cost, speed, and reliability.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ENRICH & EVALUATE PIPELINE v9.18                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  PHASE 0: ENTITY VALIDATION                                                  │
│  • Catches non-companies (podcasts, nonprofits, university labs)            │
│  • Invalid entities exit immediately (no API calls)                         │
│                                                                              │
│  PHASE 1: ENRICHMENT (Brave Search)                                         │
│  • Employee count, funding, stage, valuation                                │
│  • PE/acquisition detection, GTM motion, software-first check              │
│  • Merger/rebrand detection, geography flags                                │
│                                                                              │
│  PHASE 2: PRE-EVALUATION GATES (5 Tiers)                                    │
│  ├── Tier 1: Hard gates (>150 emp, >$75M, PE-backed, Series C+, >12yr)     │
│  ├── Tier 2: Sector gates (biotech, hardware, crypto, consumer, etc.)      │
│  ├── Tier 3: GTM gates (PLG-dominant, pre-sales company)                   │
│  ├── Tier 4: Stale company (3+ yr funding, shrinking)                      │
│  └── Tier 5: Soft flags (warnings, proceed with penalty)                   │
│                                                                              │
│  PHASE 3: CUSTOMER PERSONA CLASSIFICATION (Claude Haiku)                    │
│  • business-user, employee-user, developer, mixed                           │
│  • Developer + <50 emp → Auto-pass                                          │
│                                                                              │
│  PHASE 4: CS HIRE READINESS THRESHOLD (Claude Haiku)                        │
│  • Must score >= 10 to proceed                                              │
│  • Evidence-based (not inferred from stage)                                 │
│                                                                              │
│  PHASE 5: FULL EVALUATION (Claude Haiku)                                    │
│  • 100-point weighted model + domain distance modifier                      │
│  • Buckets: APPLY (>=70), WATCH (40-69), PASS (<40)                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Why Six Phases?

| Approach | Cost | Speed | Reliability |
|----------|------|-------|-------------|
| Claude-only | ~$78/month | 3-5s per company | LLM may miss obvious DQs |
| Six-phase | ~$8/month | <100ms for code gates | Deterministic gates |

**90% fewer full evaluation API calls** - code gates filter before expensive LLM calls.

---

## Scoring Categories (100 points)

| Category | Points | What It Measures |
|----------|--------|------------------|
| CS Hire Readiness | 25 | Active need for CS leadership hire |
| Stage & Size Fit | 25 | Right inflection point (20-100 emp, Series A/B) |
| Role Mandate | 20 | Builder (0-to-1) vs Maintainer |
| Sector & Mission | 15 | Healthcare B2B SaaS alignment |
| Outreach Feasibility | 15 | Network access, warm intro potential |

**Domain Distance Modifier:** +5 (healthcare B2B) to -10 (physical security)

---

## Hard DQ Gates (Tier 1)

| Gate | Threshold |
|------|-----------|
| Employee count | > 150 |
| Total funding | > $75M |
| Unicorn valuation | >= $1B |
| Stage | Series C or later |
| Company age | > 12 years |
| PE-backed | Any PE firm match |
| Acquired/merged | Acquisition detected |

See `SCORING-THRESHOLDS.md` for complete gate reference.

---

## Key Files

| File | Purpose |
|------|---------|
| `Enrich & Evaluate Pipeline v9.18.json` | Company evaluation (6-phase) |
| `Job Evaluation Pipeline v6.10.json` | Job scoring |
| `Funding Alerts Rescore v4.15-standalone.json` | Re-evaluation (config-driven) |
| `tide-pool-agent-lens-v2.17.md` | Personal lens (consumed by n8n) |
| `SCORING-THRESHOLDS.md` | Canonical threshold reference |
| `AUDIT-PROMPT.md` | Business logic audit procedure |

---

## Maintenance

| Change Type | Where to Update |
|-------------|-----------------|
| Threshold values | Airtable Config table (for rescore) or Parse Enrichment node |
| PE firms | PE Firms table (rescore) or peFirms array (main pipeline) |
| Sector exclusions | Parse Enrichment regex patterns |
| Scoring weights | Build Evaluation Prompt systemPrompt |
| Domain distance | Build Evaluation Prompt systemPrompt |

---

## Version History

| Version | Date | Key Changes |
|---------|------|-------------|
| v9.18 | Apr 2026 | Current production |
| v9.16 | Mar 30 | Threshold alignment ($75M funding, 150 emp), stage gate fallback |
| v9.15 | Mar 29 | Stage gate (Series C+ auto-PASS), mature company detection |
| v9.14 | Mar 24 | Gate tightening, data sufficiency gate |
| v9.9 | Mar 16 | Threshold alignment with reconciliation audit |
| v9.8 | Mar 15 | Unicorn gate, age gate, YC batch extraction |
| v9.7 | Mar 14 | Expanded sector gates (8 new), developer persona gate |
| v9 | Mar 11 | Full redesign: 6-phase architecture |
