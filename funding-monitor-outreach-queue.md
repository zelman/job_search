# Funding Announcement Monitor & Outreach Queue

## Implementation Guide for Tide Pool Job Search System

**Date:** February 27, 2026
**Context:** Two new features to add to the existing n8n-based Tide Pool job search automation system. These bridge the gap between reactive job discovery (current system) and proactive outreach to companies at the moment they receive funding, before roles are posted.

**Prerequisites:** Familiarity with the existing system architecture documented in `ARCHITECTURE.md` and `SYSTEM-OVERVIEW.md`. All new work builds on top of the existing Enrich & Evaluate Pipeline v2 subworkflow.

---

## Feature 1: Funding Announcement Monitor

### Purpose

Create a new n8n workflow that monitors RSS feeds and email alerts for startup funding announcements, extracts company names and funding details, and feeds them into the existing Enrich & Evaluate Pipeline v2 subworkflow. This captures companies at the moment of funding (when they're about to hire urgently) rather than weeks/months later when they appear on VC portfolio pages.

### Why This Matters

- Companies typically begin hiring within 30 days of closing a funding round
- Technical and operations roles are first priority hires post-funding
- Proactive outreach during this window has the highest signal-to-noise ratio
- Current VC scrapers only catch companies after they've been sitting in a portfolio page, missing the time-sensitive window

### Data Sources

Use free RSS/email signal sources rather than Crunchbase API (paid, $29/mo minimum, not worth it):

**RSS Feeds (primary):**
- TechCrunch Startups: `https://techcrunch.com/category/startups/feed/` — publishes funding announcements with structured titles like "Company X raises $YM Series A to do Z"
- Crunchbase News (free RSS, separate from paid API): `https://news.crunchbase.com/feed/`
- StrictlyVC newsletter/RSS
- Axios Pro Rata

**Google Alerts via Gmail (secondary):**
- Set up 3-5 Google Alerts that deliver to Gmail:
  - `"startup Series A funding customer success"`
  - `"startup seed round customer support"`
  - `"B2B SaaS Series A funding"`
  - `"startup raises Series A"`
  - `"seed funding round B2B"`
- These arrive as emails, parseable with a dedicated Gmail label filter, similar pattern to the existing 10-source email parser but simpler extraction

### n8n Workflow Structure

```
Schedule (every 6 hours)
       │
       ├──→ RSS Read Node (TechCrunch Startups feed)
       ├──→ RSS Read Node (Crunchbase News feed)
       ├──→ RSS Read Node (StrictlyVC feed)
       │
       ▼
Merge All Items
       │
       ▼
Filter Node:
  title contains "raises" OR "Series A" OR "seed round"
  OR "Series B" OR "funding" OR "closes round"
  OR "secures" OR "announces"
       │
       ▼
Code Node: Extract Company Name + Funding Details
  - Regex on RSS title/description to pull:
    - Company name
    - Funding amount
    - Funding stage (Seed, Series A, Series B, etc.)
  - Common title patterns to parse:
    - "[Company] raises $[X]M in [Stage] funding"
    - "[Company] closes $[X]M [Stage] round"
    - "[Company] secures $[X] million [Stage]"
    - "[Company] announces $[X]M [Stage] led by [Investor]"
       │
       ▼
Map to Enrich & Evaluate Pipeline input format:
{
  "Company": extracted_name,
  "Source": "Funding Alert - [feed name]",
  "fundingContext": "Just raised $XM Series A",
  "announcementDate": item.pubDate,
  "announcementURL": item.link
}
       │
       ▼
Execute Enrich & Evaluate Pipeline v2
(existing shared subworkflow — handles dedup, Brave
enrichment, Claude scoring, Airtable write)
```

### Code Node: RSS Title Parsing

Example parsing logic for the extraction Code node:

```javascript
// Input: RSS items from merged feeds
// Output: Structured company + funding data

const items = $input.all();
const results = [];

for (const item of items) {
  const title = item.json.title || '';
  const description = item.json.description || '';
  const text = `${title} ${description}`;

  // Pattern 1: "Company raises $XM in Stage funding"
  let match = title.match(/^(.+?)\s+raises?\s+\$?([\d.]+)\s*[Mm](?:illion)?\s+(?:in\s+)?(.+?)(?:\s+funding|\s+round|\s+led\s+by)/i);

  // Pattern 2: "Company closes $XM Stage round"
  if (!match) {
    match = title.match(/^(.+?)\s+closes?\s+\$?([\d.]+)\s*[Mm](?:illion)?\s+(.+?)(?:\s+round|\s+funding)/i);
  }

  // Pattern 3: "Company secures $X million Stage"
  if (!match) {
    match = title.match(/^(.+?)\s+secures?\s+\$?([\d.]+)\s*[Mm](?:illion)?\s+(.+?)(?:\s+to\s+|\s+for\s+|\s*$)/i);
  }

  if (match) {
    const companyName = match[1].trim();
    const amount = match[2];
    const stage = match[3].trim();

    results.push({
      json: {
        Company: companyName,
        Source: `Funding Alert - ${item.json.feedSource || 'RSS'}`,
        fundingContext: `Just raised $${amount}M ${stage}`,
        fundingAmount: parseFloat(amount),
        fundingStage: stage,
        announcementDate: item.json.pubDate || item.json.isoDate,
        announcementURL: item.json.link,
        rawTitle: title
      }
    });
  }
}

return results;
```

### Airtable Schema Changes

Add these fields to the existing **Funding Alerts** table:

| Field | Type | Description |
|-------|------|-------------|
| Discovery Type | Single Select | Values: `VC Portfolio`, `Funding Announcement`. Distinguishes time-sensitive funding alerts from standard portfolio discoveries |
| Announcement Date | Date | When the funding round was announced (from RSS pubDate) |
| Announcement URL | URL | Link to the funding announcement article |

### Integration with Existing Dedup

The existing Dedup Check Subworkflow already handles company-level deduplication via the Seen Opportunities table with `company:` prefixed keys. Funding announcement companies will be caught by this dedup layer if they've already been discovered via a VC portfolio scraper. This is correct behavior — you don't want to re-evaluate a company you've already scored.

However, consider adding logic to UPDATE an existing Funding Alerts record if the company was previously discovered via VC Portfolio but now has a funding announcement. The announcement date and URL are new, valuable context even for an already-known company. This would require a modification to the Dedup Check Subworkflow's "skip if duplicate" branch to instead route to an "update with funding context" path when the source is a Funding Announcement.

### Schedule

Every 6 hours, matching the Work at a Startup Scraper cadence. Funding announcements aren't minute-sensitive — reaching out within 24-48 hours of an announcement is still well within the optimal window.

---

## Feature 2: High-Fit Company Outreach Queue

### Purpose

Add a conditional routing branch to the Enrich & Evaluate Pipeline v2 that identifies high-scoring companies (especially those from funding announcements) and routes them to an "Outreach Queue" with automated email notifications. This turns passive discovery into actionable outreach prompts.

### Current State

Every company that passes through Enrich & Evaluate lands in the Funding Alerts table with a score, rationale, and recommendation. Then it sits there. A company scoring 85 with no matching job posting gets the same treatment as one scoring 45 — both become rows that might get reviewed on Monday morning.

### Implementation

#### Step 1: Airtable Schema Changes

Add these fields to the existing **Funding Alerts** table:

| Field | Type | Description |
|-------|------|-------------|
| Review Status | Single Select | Values: `New`, `Outreach Candidate`, `Message Sent`, `Response Received`, `No Response`, `Not a Fit`, `Archived` |
| Founder LinkedIn | URL | Manually filled when doing outreach prep |
| Outreach Notes | Long Text | Notes on outreach attempts and responses |
| Outreach Date | Date | When first outreach message was sent |

#### Step 2: Airtable View

Create a filtered view in the Funding Alerts table called **"Outreach Queue"**:
- Filter: Review Status = "Outreach Candidate"
- Sort: Tide-Pool Score descending, then Announcement Date descending
- This becomes the daily action list for proactive outreach

#### Step 3: Conditional Branch in Enrich & Evaluate Pipeline v2

After the existing Parse Response node and before the Airtable upsert, add an IF node:

```
IF Tide-Pool Score >= 70
  → Set Review Status = "Outreach Candidate"
  → Continue to Airtable upsert (with Outreach Candidate status)
  → THEN route to notification email node
ELSE
  → Set Review Status = "New"
  → Continue to Airtable upsert (normal flow)
```

The score threshold of 70 captures both "STRONG FIT" (80-100) and upper "GOOD FIT" (70-79) companies. Adjust based on volume — if you're getting too many outreach candidates, raise to 80.

#### Step 4: Notification Email

Add a Gmail Send node after the Airtable upsert for high-scoring companies. Uses the existing Gmail OAuth2 credentials already configured in n8n.

**Email configuration:**

```
To: [your email]
Subject: Outreach candidate: {{ $json.Company }} (Score: {{ $json["Tide-Pool Score"] }})

{{ $json.Company }} just raised {{ $json.fundingContext || "funding details unavailable" }}.

Tide-Pool Score: {{ $json["Tide-Pool Score"] }}/100
Stage: {{ $json["Company Stage"] }}
Role Type Assessment: {{ $json["Role Type"] }}

Rationale: {{ $json["Tide-Pool Rationale"].substring(0, 300) }}

{{ $json.announcementURL ? "Announcement: " + $json.announcementURL : "" }}
Airtable: [link to Funding Alerts table filtered to this company]

--- Suggested Action ---
1. Find founder on LinkedIn
2. Send congratulatory note referencing the round
3. Mention your CX/support buildout experience
4. Reference something specific about their product or mission
5. Keep it to 3-4 sentences max
```

**Important:** Do NOT use em dashes in the email template. Use regular dashes or rewrite to avoid them entirely. This matches Eric's communication style preferences.

#### Step 5: Weekly Outreach Review

Optionally, add to the existing Monday morning feedback loop schedule: a summary email of all Outreach Candidate records where Outreach Status is still "Not Started" after 7 days. This prevents high-value leads from going stale.

---

## Implementation Sequence

**Build order (effort estimates are for n8n workflow construction):**

### Phase 1: Outreach Queue (30-60 minutes)
Do this first. It immediately improves how you handle high-scoring companies already flowing through your VC scrapers, before the funding monitor even exists.

1. Add new fields to Funding Alerts table in Airtable (5 min)
2. Create the "Outreach Queue" filtered view in Airtable (5 min)
3. Modify Enrich & Evaluate Pipeline v2:
   - Add IF node after Parse Response (10 min)
   - Add Set node to assign Review Status based on score (5 min)
   - Add Gmail Send node for high-score notifications (15 min)
4. Test with a manual trigger passing a known high-scoring company (10 min)

### Phase 2: Funding Announcement Monitor (2-3 hours)
New workflow, more moving parts, RSS parsing requires tuning.

1. Create new n8n workflow "Funding Announcement Monitor" (10 min)
2. Add RSS Read nodes for each feed source (15 min)
3. Add Merge + Filter nodes (10 min)
4. Build and test the Code node for RSS title parsing (45-60 min — this is the fiddly part, title formats vary)
5. Add Map node to format output for Enrich & Evaluate Pipeline input (15 min)
6. Connect to Execute Subworkflow node calling Enrich & Evaluate Pipeline v2 (10 min)
7. Add Discovery Type field mapping so records are tagged as "Funding Announcement" (5 min)
8. Test end-to-end with recent RSS items (15 min)
9. Set schedule to every 6 hours (2 min)

### Phase 3: Google Alerts Integration (optional, 1 hour)
Add Gmail-based funding alerts as a secondary signal source.

1. Set up Google Alerts with funding-related queries (10 min)
2. Create Gmail filter to auto-label these as "Funding Alerts" (5 min)
3. Add Gmail fetch + parse section to the Funding Announcement Monitor workflow (30 min)
4. Test with incoming alert emails (15 min)

---

## File Inventory Updates

After implementation, update ARCHITECTURE.md and SYSTEM-OVERVIEW.md to include:

| File | Version | Description |
|------|---------|-------------|
| `Funding Announcement Monitor v1.json` | v1 | RSS + email-based funding round monitoring |
| `Enrich & Evaluate Pipeline v3.json` | v3 | Updated with outreach queue routing + notification |

### Architecture Diagram Addition

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA SOURCES                                    │
├─────────────────────┬─────────────────────┬─────────────────────────────────┤
│   Email Parsers     │   Web Scrapers      │   VC Portfolio Miners           │
│   (10 job boards)   │   (YC, Costanoa)    │   (5 thematic scrapers)         │
├─────────────────────┴─────────────────────┴─────────────────────────────────┤
│   NEW: Funding Announcement Monitor                                          │
│   (RSS feeds: TechCrunch, Crunchbase News, StrictlyVC)                      │
│   (Google Alerts via Gmail)                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│   NEW: YC Batch Monitor                                                      │
│   (Demo Day batches - twice yearly)                                         │
└──────────┬──────────────────────┬──────────────────────────┬────────────────┘
           │                      │                          │
           ▼                      ▼                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     STANDARDIZED EVALUATION SUB-ROUTINE                      │
│                     (unchanged - same 7-node chain)                          │
└──────────────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     NEW: JOB LISTINGS CROSS-REFERENCE                        │
│  Query Job Listings table for matching company                              │
│  Set hasActiveJobPosting / hasCxJobPosting flags                            │
└──────────────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     NEW: OUTREACH ROUTING LAYER                              │
│  IF hasCxJobPosting = true                                                  │
│    → Set Review Status = "Immediate Action"                                 │
│    → Send URGENT notification email                                         │
│  ELSE IF Score >= 70                                                        │
│    → Set Review Status = "Outreach Candidate"                               │
│    → Send standard notification email                                       │
│  ELSE                                                                       │
│    → Normal flow                                                            │
└──────────────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AIRTABLE STORAGE                               │
│  ├── Job Listings (scored opportunities)  <─────────────────────────┐       │
│  │       ▲                                                          │       │
│  │       └──────────── cross-reference query ───────────────────────┘       │
│  ├── Funding Alerts (VC portfolio + funding + accelerators)                 │
│  │   ├── NEW: "Outreach Queue" view (score >= 70, outreach-ready)          │
│  │   └── NEW: "Immediate Action" view (has active CX job posting)          │
│  ├── Seen Opportunities (cross-source dedup)                                │
│  └── Config (API keys, credentials)                                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Feature 3: YC Demo Day / Accelerator Batch Monitor

### Purpose

Add YC batch companies as a data source for the Funding Announcement Monitor. YC Demo Days produce 200+ uniformly early-stage companies twice yearly, all of whom will be hiring within weeks. This is higher signal than general RSS feeds because every company is pre-vetted, well-funded, and at the exact same stage.

### Why This Matters

- YC companies are pre-filtered for quality and ambition
- All batch companies are at identical stage (just received ~$500K + follow-on commitments)
- Demo Day creates a predictable twice-yearly surge of hiring
- Founders are highly accessible in the first 30 days post-Demo Day
- YC network effects mean these companies often grow fastest

### Data Source

YC publishes all batch companies at:
```
https://www.ycombinator.com/companies?batch=W26
```

The page uses JavaScript hydration, but the company data is embedded in the page as JSON. Two approaches:

**Option A: Browserless scrape (reliable)**
Use the existing Browserless.io integration to render the page and extract company cards.

**Option B: Direct JSON extraction (faster, may break)**
The page embeds company data in a `<script>` tag. Parse it directly without rendering.

### n8n Workflow Structure

```
Schedule: Run twice yearly
  - March 20 (after W batch Demo Day, typically March 10-15)
  - September 20 (after S batch Demo Day, typically September 10-15)
  - Also run monthly to catch late additions
       │
       ▼
Set Node: Define current batch
  - batchCode: "W26" or "S26" (update manually each cycle)
       │
       ▼
HTTP Request or Browserless Node:
  URL: https://www.ycombinator.com/companies?batch={{ $json.batchCode }}
       │
       ▼
Code Node: Extract Company Data
  - Parse company cards from HTML/JSON
  - Extract: name, oneLiner, batch, industries[], teamSize
       │
       ▼
Split In Batches Node:
  - Process 10 companies at a time (rate limiting)
       │
       ▼
Map to Enrich & Evaluate Pipeline input:
{
  "Company": name,
  "Source": "YC Demo Day W26",
  "fundingContext": "YC W26 - just completed Demo Day",
  "discoveryType": "Accelerator",
  "ycOneLiner": oneLiner,
  "ycBatch": batch
}
       │
       ▼
Execute Enrich & Evaluate Pipeline v2
```

### Code Node: YC Page Parsing

```javascript
// Input: Raw HTML from YC companies page
// Output: Structured company data

const html = $input.first().json.data;

// YC embeds company data in a Next.js JSON blob
// Look for the __NEXT_DATA__ script tag
const nextDataMatch = html.match(/<script id="__NEXT_DATA__"[^>]*>(.*?)<\/script>/s);

if (!nextDataMatch) {
  return [{ json: { error: "Could not find company data on page" } }];
}

const nextData = JSON.parse(nextDataMatch[1]);
const companies = nextData.props?.pageProps?.companies || [];

return companies.map(company => ({
  json: {
    Company: company.name,
    Source: `YC Demo Day ${company.batch}`,
    fundingContext: `YC ${company.batch} - just completed Demo Day`,
    discoveryType: "Accelerator",
    ycOneLiner: company.one_liner,
    ycBatch: company.batch,
    ycIndustries: company.industries?.join(", ") || "",
    ycTeamSize: company.team_size || null,
    ycUrl: `https://www.ycombinator.com/companies/${company.slug}`
  }
}));
```

### Airtable Schema Changes

Add these fields to the existing **Funding Alerts** table:

| Field | Type | Description |
|-------|------|-------------|
| YC Batch | Single Line Text | e.g., "W26", "S25". Populated only for YC companies |
| YC One-Liner | Single Line Text | YC's summary of what the company does |
| Discovery Type | Single Select | Add value: `Accelerator` (in addition to existing `VC Portfolio`, `Funding Announcement`) |

### Schedule

Unlike RSS monitoring (every 6 hours), YC batch scraping should run:
- **Twice yearly:** ~1 week after Demo Day (mid-March, mid-September)
- **Monthly:** To catch companies added late or batch corrections

This avoids hammering YC's servers and aligns with when companies actually appear.

### Filtering Considerations

YC batches include companies across all verticals. If you want to focus on specific industries (B2B, Healthcare, etc.), add a filter node after extraction:

```javascript
const targetIndustries = ['B2B', 'SaaS', 'Healthcare', 'Developer Tools', 'Enterprise'];
return items.filter(item =>
  targetIndustries.some(ind =>
    item.json.ycIndustries?.toLowerCase().includes(ind.toLowerCase())
  )
);
```

Or skip filtering and let the scoring layer handle relevance (simpler, more flexible).

---

## Feature 4: Job Listings Cross-Reference

### Purpose

After a company passes through the Enrich & Evaluate Pipeline (from any source), check if that company already has open job postings in the Job Listings table. If a company just raised funding AND has an active CX/Support role posted, that's a "drop everything" priority - they're actively hiring for your target role right now.

### Why This Matters

- Funding announcement + active job posting = immediate actionable opportunity
- These leads should skip the "Outreach Queue" thinking and go straight to application
- Currently, Funding Alerts and Job Listings are siloed - a company can appear in both without you noticing the overlap

### Implementation

#### Step 1: Add Cross-Reference Node to Enrich & Evaluate Pipeline

After the Parse Response node, before the outreach routing IF node, add:

```
Parse Response
       │
       ▼
Airtable Search Node: "Job Listings"
  - Filter formula: SEARCH(LOWER("{{ $json.Company }}"), LOWER({Company}))
  - Return fields: Record ID, Title, Review Status, Company
       │
       ▼
Code Node: Check for Active Job Matches
       │
       ▼
IF Node (existing outreach routing, now enhanced)
       │
       ▼
Airtable Upsert
```

#### Step 2: Code Node - Match Detection

```javascript
// Input: Company data from Parse Response + Job Listings search results
// Output: Original data enriched with job match info

const companyData = $('Parse Response').first().json;
const jobMatches = $input.all();

// Filter to only active jobs (not "Not a Fit" or "Archived")
const activeStatuses = ['New', 'Reviewing', 'Applied', 'Interviewing'];
const activeMatches = jobMatches.filter(job =>
  activeStatuses.includes(job.json.fields?.['Review Status'])
);

// Check if any matches are CX/Support related
const cxKeywords = ['customer', 'support', 'success', 'cx', 'experience', 'service'];
const cxMatches = activeMatches.filter(job => {
  const title = (job.json.fields?.Title || '').toLowerCase();
  return cxKeywords.some(kw => title.includes(kw));
});

return [{
  json: {
    ...companyData,
    hasActiveJobPosting: activeMatches.length > 0,
    hasCxJobPosting: cxMatches.length > 0,
    matchingJobCount: activeMatches.length,
    matchingCxJobCount: cxMatches.length,
    matchingJobIds: activeMatches.map(j => j.json.id),
    matchingJobTitles: activeMatches.map(j => j.json.fields?.Title).join(', ')
  }
}];
```

#### Step 3: Enhanced Outreach Routing Logic

Update the existing IF node to include job match context:

```
IF hasCxJobPosting = true
  → Set Review Status = "Immediate Action"
  → Set Priority = "High"
  → Send URGENT notification email (different template)

ELSE IF Tide-Pool Score >= 70
  → Set Review Status = "Outreach Candidate"
  → Send standard notification email

ELSE
  → Set Review Status = "New"
  → Normal flow
```

#### Step 4: Airtable Schema Changes

Add these fields to the existing **Funding Alerts** table:

| Field | Type | Description |
|-------|------|-------------|
| Has Active Job Posting | Checkbox | True if company has any active job in Job Listings |
| Has CX Job Posting | Checkbox | True if company has active CX/Support job specifically |
| Matching Job IDs | Text | Comma-separated Record IDs for linking (or use Linked Record field) |
| Matching Job Titles | Long Text | Human-readable list of matching job titles |

#### Step 5: Urgent Notification Email Template

For companies with `hasCxJobPosting = true`:

```
To: [your email]
Subject: ACTIVE CX ROLE: {{ $json.Company }} (Score: {{ $json["Tide-Pool Score"] }})

{{ $json.Company }} has an ACTIVE job posting matching your target role AND just raised funding.

This is a "drop everything" lead.

Matching Jobs:
{{ $json.matchingJobTitles }}

Funding Context: {{ $json.fundingContext || "Recently discovered" }}
Tide-Pool Score: {{ $json["Tide-Pool Score"] }}/100

Action: Apply immediately, then follow up with founder outreach.

Job Listings: [link to filtered view]
Funding Alerts: [link to this record]
```

#### Step 6: Airtable View

Create a new filtered view in Funding Alerts called **"Immediate Action"**:
- Filter: Has CX Job Posting = checked
- Sort: Date Added descending
- This is the "do this today" list

---

## Updated Implementation Sequence

### Phase 1: Outreach Queue (30-60 minutes)
*(unchanged from original)*

### Phase 2: Funding Announcement Monitor (2-3 hours)
*(unchanged from original)*

### Phase 3: Job Listings Cross-Reference (45-60 minutes)
Add this before Phase 4. It enhances the existing pipeline.

1. Add new fields to Funding Alerts table in Airtable (5 min)
2. Create "Immediate Action" filtered view in Airtable (5 min)
3. Modify Enrich & Evaluate Pipeline v2/v3:
   - Add Airtable Search node after Parse Response (10 min)
   - Add Code node for match detection (15 min)
   - Update IF node with hasCxJobPosting branch (10 min)
   - Add urgent notification email template (10 min)
4. Test with a company known to exist in both tables (10 min)

### Phase 4: YC Demo Day Monitor (1-2 hours)
New workflow, run after next Demo Day.

1. Create new n8n workflow "YC Batch Monitor" (10 min)
2. Add HTTP Request or Browserless node for YC companies page (15 min)
3. Build Code node for page parsing (30-45 min - depends on page structure)
4. Add Split In Batches node for rate limiting (5 min)
5. Add Map node and connect to Execute Subworkflow (10 min)
6. Test with current batch (15 min)
7. Set schedule for post-Demo Day runs (5 min)

### Phase 5: Google Alerts Integration (optional, 1 hour)
*(unchanged from original)*

---

## Updated File Inventory

After implementation, update ARCHITECTURE.md and SYSTEM-OVERVIEW.md to include:

| File | Version | Description |
|------|---------|-------------|
| `Funding Announcement Monitor v1.json` | v1 | RSS + email-based funding round monitoring |
| `YC Batch Monitor v1.json` | v1 | YC Demo Day batch scraper |
| `Enrich & Evaluate Pipeline v3.json` | v3 | Updated with outreach queue routing + job cross-reference + notification |

---

## Notes

- All RSS feed URLs should be verified before implementation as they can change
- The RSS title parsing Code node will need iterative tuning as you see real feed data — title formats are inconsistent across sources
- The outreach queue threshold (Score >= 70) should be adjusted based on volume after 1-2 weeks of data
- The notification email is the critical piece — without it, the outreach queue is just another Airtable view that gets forgotten
- Consider adding Funding Announcement context to the Claude scoring prompt so the LLM can factor in recency/urgency when scoring these companies
