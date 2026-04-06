# Job Scraper Backlog

*Updated April 2026*

Tracking job sources, scrapability assessments, and implementation status.

---

## Active Scrapers

| Scraper | Version | Platform | Schedule | Notes |
|---------|---------|----------|----------|-------|
| Health Tech Nerds | v1 | Static JSON | Every 6 hrs | CX leadership filter |
| CS Insider | v1.7 | Browserless (Notion) | Tue/Fri 7am | Highest signal for CS roles. Fragile: Notion iframe extraction |
| Work at a Startup | v12 | Browserless | Varies | YC portfolio |
| Job Alert Email Parser | v3-43 | Gmail + Browserless | Hourly | 10 email sources + OmniJobs |
| Indeed | v8.1 | API | Varies | Airtable search configs |
| First Round | v1 | API | Tue/Fri 7am | Session cookie auth |
| VC - Healthcare | v28 | Browserless | Tue/Fri 8am | 14 VCs |
| VC - Enterprise | v28 | Browserless | Mon/Thu 8am | 15 VCs |
| VC - Social Justice | v25 | Browserless | Wed/Sat 8am | 4 VCs |
| VC - Micro-VC | v15 | Browserless | Tue/Fri 8am | 5 VCs |
| VC - Growth Stage | v2.7 | Browserless | Wed/Sat 8am | 2 VCs active (Emergence, GC) |
| VC - Bessemer Battery | v2.7 | Browserless | - | Bessemer portfolio |
| VC - Lightspeed | v1 | Browserless | - | Lightspeed portfolio |
| Lightspeed Jobs | v1 | Browserless | - | Lightspeed jobs board |
| Top Startups | v2 | Browserless | - | Top startups list |
| SEC Form D | v2.4 | - | - | SEC filing scraper |

**Archived:** VC Scraper - Climate Tech (low signal, hardware DQs)

---

## Recommended Additions

### Priority 1: GTMfund Job Board (jobs.gtmfund.com)
- **Why:** B2B SaaS-focused VC, 350+ GTM executives. Role-first discovery.
- **Platform:** Consider (React, client-side rendering)
- **Approach:** Browserless, 5-8 sec wait, extract from DOM
- **Complexity:** Medium. Same pattern works for Bessemer.

### Priority 2: Rock Health Portfolio (rockhealth.com/companies)
- **Why:** Premier digital health fund. 100% healthcare portfolio. Not yet scraped.
- **Complexity:** Low. Standard portfolio page.

### Priority 3: Bessemer Portfolio Jobs (jobs.bvp.com)
- **Why:** Vertical SaaS thesis. Healthcare, insurance, compliance.
- **Platform:** Consider (same as GTMfund)
- **Risk:** Late-stage portfolio, many Series D+ will DQ.

### Not Recommended

| Source | Why Skip |
|--------|----------|
| Transformation Capital | Already in Healthcare VCs |
| TCV | Late-stage focus, high DQ rate |
| TrueUp | Auth wall, too many late-stage |
| Wellfound | Already get email alerts |
| CXPA Career Center | Enterprise CX, wrong stage |

---

## Pipeline Enhancements Backlog

### PRIORITY 1: Re-enable LinkedIn Network Matching
- **Status:** Disabled in v9 to fix duplicate record bug
- **Why critical:** Network analysis (Mar 16) revealed 1,137 connections with warm intro potential. Cold outreach produces near-zero responses.
- **Fix needed:** Re-architect with single merge path combining job + LinkedIn data
- **Workaround:** Manual network-to-pipeline matching identifies key connections

### Priority 2: Rescore — Add Job/Network Cross-Reference
- **Gap:** Rescore doesn't populate Has Active Job, Has Network Connection fields
- **Enhancement:** Add Job Listings search + LinkedIn Connections search to Rescore
- **Complexity:** Medium (3 new nodes)

### Priority 3: Stale Job Cleanup
- Jobs >30 days old with no action → archive
- Recheck job URLs for 404s

---

## Warm Intro Pipeline

Cold outreach has produced near-zero responses. Warm intros are the only channel converting.

**Key connectors identified:**
- Maranda Dziekonski (CCO, Fexa) — CS community connector
- Sabina Pons (CEO, Growth Molecules) — CS consulting, networker
- Scott Chaykin (Head CS & Support, Sentry) — dev tools with enterprise motion
- Meganne Harvey (VP CX, Gradient) — new connection
- Matt MacInnis (COO, Rippling) — REC relationship

**What's needed:**
- Automated network-to-pipeline matching (Priority 1 above)
- Periodic "who moved companies?" check
- Short list of CS leader connectors for outreach

---

## Consider Platform Notes

GTMfund and Bessemer use Consider. Build GTMfund first, reuse for Bessemer.

**Approach:**
- Browserless with pre-filtered URL
- Wait 5-8 seconds for React render
- Extract job links from DOM (`/jobs/company/job-id`)
- May need pagination for infinite scroll

---

*Last updated: April 2026*
