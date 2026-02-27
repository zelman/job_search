# VC Date Enrichment

An n8n workflow that enriches VC portfolio companies with their investment dates by searching Brave and updating Airtable.

## Overview

This workflow finds companies in the Funding Alerts table that are missing a "Portfolio Addition Date" and attempts to find the investment year via Brave Search, then updates the Airtable record.

## How It Works

1. **Get Companies Missing Dates** - Queries Airtable for records where Portfolio Addition Date is blank and VC Firm is set
2. **Prepare Search Queries** - Builds search queries like `{Company} {VC Firm} funding`
3. **Batch Processing** - Processes 5 companies at a time with rate limiting
4. **Brave Search** - Searches for funding/investment information
5. **Parse Dates** - Extracts investment years (2005-2026) from search results using regex patterns
6. **Update Airtable** - Updates records with found dates via direct API call

## Date Parsing Patterns

The workflow looks for years near these keywords:
- raised, funding, investment, invested
- Series A/B/C/D/E, seed, round
- announced, closed, led, participated
- Dollar amounts ($5M, million, billion)

When a year is found, it's stored as `YYYY-01-01` (January 1st of that year as an approximation).

## Setup

1. Import `VC Date Enrichment v5.json` into n8n
2. Edit the **"Prepare Search Queries"** node
3. Replace the placeholder API keys:
   ```javascript
   const braveApiKey = 'YOUR_BRAVE_API_KEY';
   const airtableApiKey = 'YOUR_AIRTABLE_PERSONAL_ACCESS_TOKEN';
   ```
4. Connect your Airtable credential to the "Get Companies Missing Dates" node
5. Run the Manual Trigger

## API Keys Required

| Key | Source | Used For |
|-----|--------|----------|
| Brave Search API | [brave.com/search/api](https://brave.com/search/api/) | Searching for investment info |
| Airtable Personal Access Token | [airtable.com/create/tokens](https://airtable.com/create/tokens) | Updating records via API |

## Airtable Schema

Required fields in the Funding Alerts table:
- **Company Name** (text) - Name of the company
- **VC Firm** (single select) - The VC that invested
- **Portfolio Addition Date** (date) - When the VC invested (this gets populated)

## Rate Limiting

- Brave Search: 1.5s delay between requests within a batch
- Batches: 2s delay between batches of 5
- Full run of ~1000 companies takes approximately 30-40 minutes

## Version History

- **v5**: Working version using HTTP Request nodes for both Brave Search and Airtable updates. Bypasses n8n Airtable node limitations with record ID matching.
- **v4**: Attempted to fix Airtable node - failed due to node not supporting record ID matching
- **v3**: Used fetch() - failed because n8n Cloud doesn't support native fetch in Code nodes
- **v2**: Fixed data structure issues - failed due to HTTP Request node credential issues
- **v1**: Initial version - failed due to wrong Airtable data structure

## Troubleshooting

### No dates being found
- Check "Parse Dates" node output for `resultsCount` - if 0, Brave isn't returning results
- Try simplifying search queries if they're too specific

### Airtable update errors
- Verify your Airtable Personal Access Token has write permissions
- Check the token hasn't expired

### Rate limiting errors
- Increase the Wait node delay
- Reduce batch size
