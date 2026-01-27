# Work at a Startup Scraper

An n8n workflow that scrapes YC's [Work at a Startup](https://www.workatastartup.com) job board for customer support/success leadership roles.

## Overview

This workflow runs on a schedule (every 6 hours) to:
1. Authenticate with Y Combinator using stored credentials
2. Scrape the Work at a Startup job listings via Browserless.io
3. Filter for customer support/success leadership roles
4. Add new jobs to Airtable

## How It Works

Since Work at a Startup requires YC authentication and n8n cloud doesn't support Puppeteer community nodes, this workflow uses [Browserless.io](https://browserless.io) as a headless browser service.

### Workflow Nodes

1. **Schedule Trigger** - Runs every 6 hours
2. **Get Config** - Fetches credentials from Airtable Config table
3. **Parse Config** - Extracts BROWSERLESS_TOKEN, YC_USER, YC_PASSWORD
4. **Scrape via Browserless** - Sends Puppeteer script to Browserless API
5. **Parse & Filter** - Filters for support/success + leadership keywords
6. **Has Jobs?** - Routes based on whether jobs were found
7. **Add to Airtable** - Appends new jobs to the Jobs table

### Browser Script

The Puppeteer script:
1. Navigates to YC's login page (account.ycombinator.com)
2. Enters username and password
3. Submits the login form
4. Navigates to Work at a Startup with support role filter
5. Scrolls to load all listings
6. Extracts job cards (title, company, location, salary, URL)

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

### Browserless.io Setup

1. Sign up at [browserless.io](https://browserless.io)
2. Get your API token from the dashboard
3. Add it to Airtable Config as `BROWSERLESS_TOKEN`

Free tier includes 1000 sessions/month.

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

## Version History

- **v2**: Fixed Browserless v2 compatibility (ES modules instead of CommonJS)
- **v1**: Initial version using Browserless.io REST API
