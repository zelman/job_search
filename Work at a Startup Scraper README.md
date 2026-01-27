# Work at a Startup Scraper v3

An n8n workflow that scrapes YC's [Work at a Startup](https://www.workatastartup.com) job board for customer support/success leadership roles, with AI-powered job fit scoring.

## Overview

This workflow runs on a schedule (every 6 hours) to:
1. Authenticate with Y Combinator using stored credentials
2. Scrape the Work at a Startup job listings via Browserless.io
3. Filter for customer support/success leadership roles
4. **Rate job fit using Claude AI** (0-100 score with rationale)
5. Add new jobs to Airtable with AI-generated insights

## How It Works

Since Work at a Startup requires YC authentication and n8n cloud doesn't support Puppeteer community nodes, this workflow uses [Browserless.io](https://browserless.io) as a headless browser service.

### Workflow Nodes

1. **Schedule Trigger** - Runs every 6 hours
2. **Get Config** - Fetches credentials from Airtable Config table
3. **Parse Config** - Extracts BROWSERLESS_TOKEN, YC_USER, YC_PASSWORD, ANTHROPIC_API_KEY
4. **Scrape via Browserless** - Sends Puppeteer script to Browserless API
5. **Parse & Filter** - Filters for support/success + leadership keywords
6. **Has Jobs?** - Routes based on whether jobs were found
7. **Rate Job Fit** - Calls Claude AI to evaluate each job against candidate profile
8. **Add to Airtable** - Appends new jobs to the Jobs table

### Browser Script

The Puppeteer script:
1. Navigates to YC's authenticate endpoint with continue URL
2. Enters username and password
3. Submits the login form (auto-redirects to jobs page)
4. Scrolls to load all listings
5. Extracts job data: title, company, YC batch, industry, location, salary, URL

### AI Job Rating

The Rate Job Fit node:
1. Fetches candidate profile from GitHub (`tide-pool-agent-lens.md`)
2. Sends job details to Claude AI (Haiku model)
3. Returns: Tide-Pool Score (0-100), rationale, industry, company stage
4. Uses scraped YC batch (e.g., "YC S24") as fallback for Company Stage

## Role Filtering

Jobs are filtered to only include **customer support/success leadership roles**:

**Support keywords:** support, success, customer, client, cx, experience

**Leadership keywords:** manager, director, vp, vice president, head, lead, chief, supervisor, team lead

## Configuration

### Airtable Config Table

Add these keys to your Airtable Config table (same one used by Job Alert Email Parser):

| Key | Value |
|-----|-------|
| BROWSERLESS_TOKEN | Your Browserless.io API token |
| YC_USER | Your Y Combinator username |
| YC_PASSWORD | Your Y Combinator password |
| ANTHROPIC_API_KEY | Your Anthropic API key for Claude |

### Browserless.io Setup

1. Sign up at [browserless.io](https://browserless.io)
2. Get your API token from the dashboard
3. Add it to Airtable Config as `BROWSERLESS_TOKEN`

Free tier includes 1000 sessions/month.

### Anthropic API Setup

1. Get an API key from [console.anthropic.com](https://console.anthropic.com)
2. Add it to Airtable Config as `ANTHROPIC_API_KEY`
3. Uses Claude 3 Haiku model (~$0.001 per job)

### Airtable Setup

Uses the same Jobs table as Job Alert Email Parser:
- Base ID: `appFEzXvPWvRtXgRY`
- Table ID: `tbl6ZV2rHjWz56pP3`

## Airtable Fields

| Field Name | Type | Description |
|------------|------|-------------|
| Job Title | Text | The job title |
| Company | Text | Company name |
| Location | Text | Job location |
| Source | Text | "Work at a Startup" |
| Job URL | URL | Link to job posting |
| Job ID | Text | Unique identifier (waas-{timestamp}-{index}) |
| Salary Info | Text | Salary if displayed |
| Date Found | Date | When job was scraped |
| Review Status | Single Select | Default: "New" |
| Tide-Pool Score | Number | AI-generated fit score (0-100) |
| Tide-Pool Rationale | Long Text | AI explanation for the fit score |
| Tide Pool Fit | Formula | Auto-calculated from score (Strong/Good/Moderate/Weak Fit) |
| Industry | Text | Company industry (AI or scraped) |
| Company Stage | Text | YC batch (e.g., "YC S24") or funding stage |

## Troubleshooting

### "module is not defined" error
The workflow uses ES modules format (`export default`) for Browserless v2. If you see this error, ensure you're using the latest workflow version.

### No jobs found
- Verify YC credentials are correct in Airtable Config
- Check if you can log into account.ycombinator.com manually
- The job filter may not find any support/success leadership roles

### Timeout errors
- Browserless has a 2-minute timeout configured
- If consistently timing out, the YC site may have changed structure

### 404 error in Tide-Pool Rationale
- The profile URL may be incorrect
- Verify `tide-pool-agent-lens.md` exists in the tidepool repo

### Empty Company Stage or Industry
- Claude may not know the company's funding stage
- YC batch is used as fallback (e.g., "YC S24")
- Industry is scraped from page when possible

## Version History

- **v3**: Added Claude AI job rating (Tide-Pool Score, rationale, industry, company stage); extracts YC batch for Company Stage; extracts industry from page
- **v2**: Fixed Browserless v2 compatibility (ES modules instead of CommonJS); fixed cross-domain auth flow
- **v1**: Initial version using Browserless.io REST API
