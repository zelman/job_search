# Job Scraper Backlog

Tracking potential job sources, scrapability assessments, and implementation status.

---

## Active Scrapers

| Scraper | Status | Platform | Volume | Notes |
|---------|--------|----------|--------|-------|
| Health Tech Nerds v1 | ✅ Working | Static JSON | ~60 jobs | `/data/transformed_job_data.json` |
| Work at a Startup v12 | ✅ Working | Browserless | Varies | YC + Costanoa |
| Job Alert Email Parser v3-43 | ✅ Working | Gmail + Browserless | ~50/day | 10 email sources + OmniJobs |
| Indeed v4 | ✅ Working | API | Varies | Airtable search configs |
| First Round v1 | ✅ Working | API | ~20 | Session cookie auth |

---

## Skipped (Too Complex)

| Source | Platform | Reason |
|--------|----------|--------|
| Bessemer Jobs (jobs.bvp.com) | Consider | Two-stage scraping required; late-stage portfolio |
| GTMfund (jobs.gtmfund.com) | Consider | Two-stage scraping required; GTM-focused (limited CX) |

---

## Backlog - To Scout

### Success Hacker
- **URL:** successhacker.co → redirects to successcoaching.co
- **Finding:** Training company, no job board
- **Status:** ❌ Not viable

### CS Insider (csinsider.co/job-board)
- **Platform:** Webflow
- **Volume:** Claims 100k+ (aggregator)
- **Status:** Needs investigation - job data loaded dynamically
- **Notes:** AI-powered matching, may be scraping other boards

### TopCSjobs.com
- **Platform:** WordPress + WP Job Board Pro
- **Volume:** 2 jobs visible
- **Status:** ❌ Too low volume

### Customer Success Association
- **URL:** customersuccessassociation.com/customer-success-jobs-board/
- **Status:** 403 blocked - likely LinkedIn Group redirect
- **Notes:** Free to post, community-curated

---

## Consider Platform Notes

GTMfund and Bessemer both use Consider. Key challenges:

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

### Rescore: Add Job/Network Cross-Reference
- **Current state:** Rescore workflow only does enrichment + evaluation
- **Gap:** Doesn't populate Has Active Job, Has CX Job, Matching Job Titles, Has Network Connection, Connection Name, Connection LinkedIn URL
- **Enhancement:** Add Job Listings search, LinkedIn Connections search, and matching logic to Rescore workflow
- **Complexity:** Medium - requires 3 new nodes (2 Airtable searches + 1 code node for matching)
- **Benefit:** All companies would show job/network matches, not just new ones from main pipeline

### Re-enable LinkedIn Network Matching
- **Status:** Disabled in v9 to fix duplicate record bug
- **Issue:** Two parallel merge paths (Job Check + LinkedIn Check) both fed into downstream node
- **Fix needed:** Re-architect with single merge path that combines both job and LinkedIn data
- **Priority:** Low - limited startup contacts in LinkedIn currently

### Stale Job Cleanup
- Jobs >30 days old with no action → archive
- Recheck job URLs for 404s (position filled)

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

### Weekly Digest Email
- Top 10 new opportunities by score
- Pipeline summary (X new, Y applied, Z interviewing)
- Source effectiveness (which VCs/emails produce best matches)

### Cover Letter Drafting
- Trigger: Job marked "Apply"
- Input: Job description + resume
- Output: Draft cover letter in Google Doc, linked in Airtable

### Founder Research Automation
- For top Tide Pool companies, auto-research founder names, LinkedIn URLs, recent appearances
- Currently manual process

### Application Funnel Tracking
- Track conversion rates: Applied → Response → Interview → Offer
- Identify patterns in successful applications

---

*Last updated: Mar 2026*
