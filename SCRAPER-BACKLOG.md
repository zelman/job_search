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

## In Progress

### Bessemer Jobs (jobs.bvp.com)
- **Status:** ❌ Skipped - requires two-stage scraping
- **Platform:** Consider (client-side rendered)
- **Volume:** 6,966 jobs / 305 companies (unfiltered)
- **Filtered URL:** `?jobTypes=Customer+Support&...&stages=Seed&stages=Series+A&staffCountRanges=1-10&staffCountRanges=10-100`
- **Challenge:** Even with tight filters, Consider shows company pages first ("All jobs at X"), not individual job listings
- **Would require:** Two-stage scrape (1. get companies, 2. loop each company page)
- **Notes:** Portfolio skews late-stage. Not worth the complexity given low expected signal.

### GTMfund (jobs.gtmfund.com)
- **Status:** ❌ Skipped - too complex
- **Platform:** Consider (client-side rendered)
- **Volume:** 766 jobs / 150 companies
- **Challenge:** Job links are company pages, not individual jobs. Would need multi-level scraping.
- **Notes:** GTM-focused (sales/marketing) - limited CX roles anyway.

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

*Last updated: Mar 2026*
