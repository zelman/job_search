# Job Scraper Backlog

*Updated March 25, 2026*

Tracking potential job sources, scrapability assessments, and implementation status.

---

## Active Scrapers

| Scraper | Status | Platform | Schedule | Notes |
|---------|--------|----------|----------|-------|
| Health Tech Nerds v1 | ✅ Working | Static JSON | Every 6 hrs | CX leadership filter, dedup against Airtable, feeds Job Eval Pipeline |
| CS Insider v1.7 | ✅ Working | Browserless (Notion embed) | Tue/Fri 7am | Role-first discovery. Highest signal source for CS leadership roles. Fragile: Notion iframe URL extraction could break if CS Insider changes embed structure. |
| Work at a Startup v12 | ✅ Working | Browserless | Varies | YC portfolio |
| Job Alert Email Parser v3-43 | ✅ Working | Gmail + Browserless | Hourly | 10 email sources + OmniJobs |
| Indeed v4 | ✅ Working | API | Varies | Airtable search configs |
| First Round v1 | ✅ Working | API | Tue/Fri 7am | Session cookie auth |
| VC Scraper - Healthcare v27 | ✅ Working | Browserless | Tue/Fri 8am | 14 VCs: Flare, 7wire, Oak HC/FT, Digitalis, a16z Bio+Health, Healthworx, Cade, Hustle Fund (health), Martin, Town Hall, Transformation Capital, Brewer Lane, Mainsail, Five Elms |
| VC Scraper - Enterprise v27 | ✅ Working | Browserless | Mon/Thu 8am | Unusual, First Round, Khosla, Kapor, WhatIf, WXR, Leadout, Notable, Headline, PSL, Trilogy, K9, Precursor, M25, GoAhead (15 VCs) |
| VC Scraper - Social Justice v25 | ✅ Working | Browserless | Wed/Sat 8am | Kapor, Backstage, Harlem, Collab |
| ~~VC Scraper - Climate Tech v23~~ | Archived | - | - | Low signal, hardware/deeptech DQs |
| VC Scraper - Micro-VC v15 | ✅ Working | Browserless | Tue/Fri 8am | Pear, Afore, Unshackled, 2048, Y Combinator (5 VCs) |
| VC Scraper - Growth Stage v2.6 | ✅ Working | Browserless | Wed/Sat 8am | Emergence, General Catalyst (2 VCs active). **v2.6: BRAVE COST REDUCTION** - Disconnected 3 zero-signal VCs (Insight Partners 0/768, Iconiq 0/100, SignalFire 0/12 Apply rate). Nodes left in place for documentation. ~26% query reduction. v1.3: Parser fixes. v1.2: Fixed Emergence URL. |

---

## Completed Removals (Mar 16, 2026) ✅

Removed 4 low-signal VCs that produced predominantly developer-as-customer companies failing persona gates:

| Scraper | VCs Removed | Reason |
|---|---|---|
| Enterprise v26 → v27 | Essence VC | 80%+ developer tools |
| Enterprise v26 → v27 | Costanoa Ventures | Heavy dev tools/data infrastructure |
| Enterprise v26 → v27 | Golden Ventures | Canadian early-stage, geographic mismatch |
| Micro-VC v14 → v15 | Floodgate | Mixed dev/consumer portfolio |

**Result:** Eliminated ~40-60 companies per scrape cycle that auto-disqualified. Reduced Haiku token spend and Airtable clutter.

---

## Recommended Additions (Low Effort, High Signal)

### ~~Priority 0: Enterprise B2B SaaS VCs~~ ✅ COMPLETED

**Implemented:** `VC Scraper - Growth Stage v1.3.json` (Mar 25, 2026)

| VC | Status |
|----|--------|
| Emergence Capital | ✅ Added |
| Insight Partners | ✅ Added |
| Iconiq Growth | ✅ Added |
| General Catalyst | ✅ Added |
| SignalFire | ✅ Added |

**Schedule:** Wed/Sat 8am
**Note:** Update `Execute Enrich & Evaluate Pipeline` workflow ID after importing to n8n.

### Priority 1: GTMfund Job Board (jobs.gtmfund.com)
- **Why:** B2B SaaS-focused VC with 350+ GTM executives in network. Portfolio board frequently has CS/CX leadership roles. Role-first discovery like CS Insider and Health Tech Nerds.
- **Platform:** Consider (React, client-side rendering)
- **Approach:** Browserless with pre-filtered URL, 5-8 sec wait for React render, extract from DOM
- **Complexity:** Medium. Same Consider platform as Bessemer. Build one, get both.
- **Expected signal:** Higher than company-first scrapers because roles are pre-filtered to GTM/CS functions.

### Priority 2: Rock Health Portfolio (rockhealth.com/companies)
- **Why:** Premier digital health fund. 100% healthcare portfolio. Not yet in Healthcare VC scraper despite being the most focused healthcare VC in the market.
- **Complexity:** Low. Standard portfolio page scrape, same pattern as existing VC scrapers.
- **Expected signal:** Moderate. Will surface healthcare SaaS companies not in the other 14 healthcare VC portfolios.

### Priority 3: Bessemer Portfolio Jobs (jobs.bvp.com)
- **Why:** Published "Roadmap to Vertical SaaS" thesis. Portfolio includes healthcare, insurance, compliance SaaS with business-user customers. Rimsys (your current Monitor) is Bessemer-backed.
- **Platform:** Consider (same as GTMfund)
- **Approach:** Build with GTMfund; same scraper pattern works for both.
- **Risk:** Late-stage portfolio. Many companies will be Series D+ and auto-disqualify. Filter hard on stage in scoring, not just in scraper.

### Not Recommended

| Source | Why Skip |
|---|---|
| Transformation Capital | **Already in Healthcare VCs v27.** |
| Catalyst Health Ventures | Diminishing returns - already scraping 14 healthcare VCs. |
| TCV (Technology Crossover) | Late-stage focus (100-300 employees). High DQ rate expected. |
| a16z Growth (separate scraper) | Already have a16z Bio+Health. Growth fund overlaps with other sources. Test if Priority 0 VCs underperform. |
| TrueUp | Auth wall + surfaces too many late-stage companies. More noise, worse signal rate. |
| Getro / Jobs in VC | Covers VC firm jobs, not portfolio company jobs. Previously evaluated and excluded. Re-evaluate only if Getro changes to aggregate portfolio roles. |
| Wellfound direct scraper | Already get email alerts. Marginal gain vs. build effort. |
| CXPA Career Center | Low volume, enterprise CX roles at large companies. Wrong stage. |
| Aspireship | Training/placement platform, not a job board. Wrong model. |
| TalentWay | AI matching service, not scrapable. Would need to sign up as job seeker. |
| Additional healthcare VCs (Define, Optum, Longitude, Polaris, GSR) | Diminishing returns. Already scraping 14 healthcare VCs. Adding more produces incremental companies that overlap with existing portfolio coverage. |

---

## Skipped (Too Complex / Low ROI)

| Source | Platform | Reason |
|--------|----------|--------|
| Bessemer Jobs (jobs.bvp.com) | Consider | Two-stage scraping required; late-stage portfolio. Viable if GTMfund Consider scraper built first. |
| GTMfund (jobs.gtmfund.com) | Consider | Two-stage scraping required. Highest-priority new build. |

---

## Backlog - To Scout

### Success Hacker
- **URL:** successhacker.co → redirects to successcoaching.co
- **Finding:** Training company, no job board
- **Status:** ❌ Not viable

### CS Insider (csinsider.co/job-board)
- **Platform:** Webflow with Notion embed
- **Volume:** CX leadership roles filtered from aggregated board
- **Status:** ✅ Active (v1.7). Runs Tue/Fri 7am. Feeds Job Evaluation Pipeline.
- **Notes:** Extracts Notion iframe URL, fetches Notion page, parses job URLs. Company name extracted from ATS URL (Greenhouse, Lever, Ashby, Workday patterns). Fragile point: Notion embed URL extraction via iframe regex.

### TopCSjobs.com
- **Platform:** WordPress + WP Job Board Pro
- **Volume:** 2 jobs visible
- **Status:** ❌ Too low volume

### Customer Success Association
- **URL:** customersuccessassociation.com/customer-success-jobs-board/
- **Status:** 403 blocked - likely LinkedIn Group redirect
- **Notes:** Free to post, community-curated

---

## Consider Platform Notes (GTMfund + Bessemer)

GTMfund and Bessemer both use Consider. **Build GTMfund first** (higher signal, CS/CX roles), then reuse for Bessemer.

Key challenges:

1. **Client-side rendering** - Jobs load via React after page hydration
2. **No public API** - `/api/jobs` returns 404
3. **serverInitialData** contains config, not job listings
4. **Filtered URLs work** - `?jobTypes=X&postedSince=P30D` filters are applied on load

**Approach for Consider boards:**
- Use Browserless with pre-filtered URL
- Wait 5-8 seconds for React to render
- Extract job links from DOM (`/jobs/company/job-id` pattern)
- If extraction fails, jobs may be in infinite scroll (pagination needed)

---

## Scoring Notes for Late-Stage Sources

For Bessemer and similar late-stage portfolios:

> Filter hard on stage in the scoring prompt, not just in the scraper. A lot of Series D+ will come through.

**Pipeline should catch:**
- Series D+ stage
- >$500M funding
- >200 employees
- PE-backed (Bessemer itself is VC, but portfolio may have PE co-investors)

**Watch for IC roles:**
> CSM and Account Manager titles should be gated unless posting signals a build mandate.

Add to scoring prompt:
- "CSM" without leadership signals → lower score
- "Account Manager" without team-building language → skip

---

## Pipeline Enhancements Backlog

### PRIORITY 1: Re-enable LinkedIn Network Matching
- **Status:** Disabled in v9 to fix duplicate record bug
- **Issue:** Two parallel merge paths (Job Check + LinkedIn Check) both fed into downstream node
- **Fix needed:** Re-architect with single merge path that combines both job and LinkedIn data
- **Why this is now highest priority:** Network analysis (Mar 16) revealed 1,137 connections with untapped warm intro potential. CS/CX leaders at mid-stage companies, former Bigtincan colleagues who've moved on, and decision-makers (CCOs, CROs) who hire CS leaders. Cold outreach produces near-zero responses. Warm intros (LeanData via Niels, Summize via Chris Picarde) are the only channel producing pipeline movement. Matching connections to pipeline companies is the highest-leverage enhancement.
- **Immediate workaround:** Manual network-to-pipeline matching done Mar 16 identified 17 CS/CX leaders, 62 Bigtincan/Showpad connections (some now at other companies), and multiple CCO/CRO connections. Full analysis output available.

### Priority 2: Rescore — Add Job/Network Cross-Reference
- **Current state:** Rescore workflow only does enrichment + evaluation
- **Gap:** Doesn't populate Has Active Job, Has CX Job, Matching Job Titles, Has Network Connection, Connection Name, Connection LinkedIn URL
- **Enhancement:** Add Job Listings search, LinkedIn Connections search, and matching logic to Rescore workflow
- **Complexity:** Medium — requires 3 new nodes (2 Airtable searches + 1 code node for matching)
- **Benefit:** All companies would show job/network matches, not just new ones from main pipeline

### Priority 3: Stale Job Cleanup
- Jobs >30 days old with no action → archive
- Recheck job URLs for 404s (position filled)

### Priority 4: Scoring Model Fixes (from Batch 3 analysis, Mar 16)
Eight new failure patterns documented in SCORING-ENHANCEMENTS-BATCH3-APPEND.md:
- 3.1 PE blocklist gaps (WCAS and other named PE firms)
- 3.2 Non-SaaS services businesses passing sector gate
- 3.3 Consumer products scoring as B2B
- 3.4 Grant-funded orgs not blocked
- 3.5 Stale funding not penalized
- 3.6 Services/consulting hybrids mimicking SaaS
- 3.7 Developer-as-customer gate execution order verification
- 3.8 Company-level vs. role-level evaluation gap (documentation only)
Quick wins: 3.1 (PE blocklist) and 3.7 (gate ordering). See SCORING-ENHANCEMENTS-BATCH3-APPEND.md for full specs.

---

## Enrichment Ideas

### Glassdoor/Blind Sentiment
- Scrape company ratings, CS/Support team reviews
- Flag companies with poor support team sentiment

### Company Growth Signals
- LinkedIn employee count delta (hiring velocity)
- Recent funding announcements (Crunchbase RSS/API)
- News mentions (Google News API or Brave News)

---

## Outreach & Reporting Ideas

### PRIORITY: Warm Intro Pipeline (not a scraper — a process)
Cold outreach has produced near-zero responses across ~30 InMails. Warm intros are the only channel converting to interviews (LeanData: HR screen in 8 days from warm intro). The system should support warm-intro workflows, not just cold discovery.

**What exists:**
- 1,137 LinkedIn connections with company/position data
- 46 recommendation relationships (strongest ties)
- 62 current Bigtincan/Showpad connections (former team, some now elsewhere)
- 17 CS/CX leaders at non-FAANG companies identified Mar 16
- Multiple CCO/CRO connections who hire CS leaders

**What's needed:**
- Automated network-to-pipeline matching (see Priority 1 above)
- Periodic "who in my network moved companies?" check (LinkedIn data export refresh)
- Short list of 3-5 CS leader connectors for "who's building a CS team?" outreach

**Key connectors identified (Mar 16 analysis):**
- Maranda Dziekonski (CCO, Fexa) — mid-market CCO, CS community connector
- Sabina Pons (CEO, Growth Molecules) — runs CS consulting firm, professional networker
- Scott Chaykin (Head CS & Support, Sentry) — right ecosystem (dev tools with enterprise motion)
- Meganne Harvey (VP CX, Gradient) — new connection (Mar 6), research Gradient
- Matt MacInnis (COO, Rippling) — REC relationship, knows everyone building CS teams

### Weekly Digest Email
- Top 10 new opportunities by score
- Pipeline summary (X new, Y applied, Z interviewing)
- Source effectiveness (which VCs/emails produce best matches)

### Cover Letter Drafting
- Trigger: Job marked "Apply"
- Input: Job description + resume
- Output: Draft cover letter in Google Doc, linked in Airtable

### Application Funnel Tracking
- Track conversion rates: Applied → Response → Interview → Offer
- Identify patterns in successful applications
- **First data point:** LeanData (Applied Mar 12 → HR Screen Mar 20 = 8 days, warm intro channel)

---

*Last updated: Mar 25, 2026 — Added Priority 0: Enterprise B2B SaaS VCs (Emergence, Insight Partners, Iconiq, General Catalyst, SignalFire). Noted Transformation Capital already covered. Deprioritized TCV, Catalyst Health Ventures, a16z Growth.*
