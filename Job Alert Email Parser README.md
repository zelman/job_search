# Job Alert Email Parser v3-14

An n8n workflow that automatically processes job alert emails from multiple sources, filters for relevant roles, uses AI to rate job fit, and adds them to an Airtable database.

## Overview

This workflow runs on a schedule (every hour) to:
1. Fetch unread job alert emails from Gmail
2. Identify the source of each email
3. Parse job listings using source-specific parsers
4. Filter for customer support/success leadership roles only
5. Deduplicate against existing Airtable records
6. **Rate job fit using Claude AI** (0-100 score with rationale)
7. Add new jobs to Airtable
8. Label processed emails in Gmail

## Supported Job Sources

| Source | Email Domain | Data Extracted |
|--------|--------------|----------------|
| LinkedIn | jobs-listings@linkedin.com, jobalerts-noreply@linkedin.com, jobs-noreply@linkedin.com | Title, Company, Location, Job URL |
| Himalayas | himalayas.app | Title, Company, Location (Remote), Job URL |
| Wellfound | wellfound.com | Title, Company, Location, Company Size, Job URL |
| Built In | builtin.com | Title, Company, Location, Salary, Job URL |
| Remotive | remotive.com | Title, Company, Location, Job URL |
| Indeed | indeed.com | Title, Company, Salary, Job URL |
| Welcome to the Jungle | welcometothejungle.com | Title, Company, Location, Salary, Job URL |
| Google Careers | careers-noreply@google.com | Title, Company (Google), Location, Job URL |
| Jobright | jobright.ai | Title, Company, Location, Salary, Job URL |

## Role Filtering

The workflow filters jobs to only include **customer support/success leadership roles**. A job must contain:

**At least one support/success keyword:**
- support, success, customer, client, cx, experience

**AND at least one leadership keyword:**
- manager, director, vp, vice president, head, lead, chief, supervisor, team lead

### Examples

**Included:**
- Customer Support Manager
- Director of Customer Success
- VP, Client Experience
- Head of Support
- Customer Success Team Lead

**Excluded:**
- Field Sales Representative (no support keyword)
- Customer Support Engineer (no leadership keyword)
- Software Engineer (neither)

## Workflow Nodes

### 1. Schedule Trigger
- Runs every 5 minutes
- Triggers the workflow automatically

### 2. Get many messages (Gmail)
- Fetches unread emails from inbox
- Filters by sender domains for supported job sources
- Only retrieves emails newer than 21 days

### 3. Mark as Read (Gmail)
- Immediately marks fetched emails as read
- Prevents duplicate processing in subsequent runs (race condition fix)

### 4. Identify Source
- Analyzes the "From" header of each email
- Tags email with `_source` field (e.g., "LinkedIn", "Jobright", "Google Careers")

### 5. Parse Jobs (Code Node)
- Source-specific parsers extract job data from email content
- Handles various email formats (HTML, plain text, base64 encoded)
- Extracts: title, company, location, salary, job URL, job ID
- Deduplicates jobs within each email
- Includes try-catch error handling to prevent parser failures from breaking the workflow

### 6. Has Jobs (IF Node)
- Filters out emails where no jobs were found

### 7. Search records (Airtable)
- Retrieves existing job URLs and title+company combinations
- Filters to records from last 30 days for performance
- Used for deduplication

### 8. Merge Inputs
- Combines parsed jobs with existing Airtable records

### 9. Dedup Against Airtable (Code Node)
- Removes jobs that already exist in Airtable
- Matches by Job URL or by Title + Company combination

### 10. Map Fields for Airtable (Code Node)
- Transforms field names to match Airtable schema
- **Applies role filter** (support/success + leadership keywords)
- Preserves email ID for labeling

### 11. Rate Job Fit (4-node sequence)
Calls Claude AI (Haiku) to evaluate each job against candidate profile:
- **Fetch Profile** (HTTP Request) - Gets candidate profile from GitHub
- **Build Prompt** (Code) - Constructs the evaluation prompt
- **Call Claude API** (HTTP Request) - Sends request to Anthropic API using `$env.ANTHROPIC_API_KEY`
- **Parse Response** (Code) - Extracts score, rationale, industry, company stage

Returns a **Tide-Pool Score** (0-100) and **Tide-Pool Rationale** (1-2 sentences). Profile updates take effect immediately on new jobs.

### 12. Filter Empty
- Removes empty items from the flow

### 13. Add to Airtable
- Appends new job records to the Airtable table
- Fields: Job Title, Company, Location, Source, Job URL, Job ID, Salary Info, Date Found, Review Status, **Tide-Pool Score**, **Tide-Pool Rationale**

### 14. Add label to message (Gmail)
- Labels processed emails with "Job Alerts/Processed"
- Uses tracked email ID from earlier in the pipeline

## Airtable Schema

| Field Name | Type | Description |
|------------|------|-------------|
| Job Title | Text | The job title |
| Company | Text | Company name |
| Location | Text | Job location (city, remote, etc.) |
| Source | Text | Where the job was found |
| Job URL | URL | Link to the job posting |
| Job ID | Text | Unique identifier for deduplication |
| Salary Info | Text | Salary range if available |
| Date Found | Date | When the job was added |
| Review Status | Single Select | Default: "New" |
| Tide-Pool Score | Number | AI-generated fit score (0-100) |
| Tide-Pool Rationale | Long Text | AI explanation for the fit score |
| Tide Pool Fit | Formula | Auto-calculated from score (Strong/Good/Moderate/Weak Fit) |
| Industry | Text | AI-identified company industry |
| Company Stage | Text | AI-identified funding stage (Seed, Series A, etc.) |

## Configuration

### Gmail Setup
- OAuth2 authentication required
- Needs access to read emails and modify labels

### Airtable Setup
- Personal Access Token authentication
- Base ID: `appFEzXvPWvRtXgRY`
- Table ID: `tbl6ZV2rHjWz56pP3`

### Gmail Label
- Label ID: `Label_3146569228785124450` (Job Alerts/Processed)

### n8n Environment Variables

Set this environment variable in your n8n instance (Settings > Variables):

| Variable | Description |
|----------|-------------|
| ANTHROPIC_API_KEY | Your Anthropic API key for Claude |

### Anthropic API (Claude) Setup
- Required for AI job fit scoring
- Get an API key from [console.anthropic.com](https://console.anthropic.com)
- Add it as n8n environment variable `ANTHROPIC_API_KEY`
- Uses Claude 3 Haiku model (most cost-effective, ~$0.001 per job)

## Customization

### Adding New Job Sources

1. Add the email domain to the Gmail query filter in "Get many messages"
2. Add source detection in "Identify Source" node
3. Add a parser in "Parse Jobs" node following the existing pattern

### Modifying Role Filter

Edit the keywords in the "Map Fields for Airtable" node:

```javascript
const supportKeywords = ['support', 'success', 'customer', 'client', 'cx', 'experience'];
const leadershipKeywords = ['manager', 'director', 'vp', 'vice president', 'head', 'lead', 'chief', 'supervisor', 'team lead'];
```

### Changing Schedule

Modify the Schedule Trigger node to run at different intervals.

## Troubleshooting

### No jobs being added
- Check if emails are being marked as read before processing completes
- Verify the source is detected correctly in "Identify Source"
- Check "Parse Jobs" output for `_noJobs: true` with `_rawText` to see what content was parsed

### Duplicate jobs
- Verify the Airtable deduplication is working
- Check that Job URL or Title+Company combination is unique

### Label not being applied
- Ensure the email ID is being passed through the pipeline
- Verify Gmail label exists and ID is correct

## Version History

- **v3-22**: Increased rate limit wait to 2 seconds (1 second wasn't enough)
- **v3-21**: Added 1-second wait between Claude API calls to prevent rate limiting
- **v3-20**: Fixed LinkedIn parser - filter out email header lines ("Your job alert for...", "New jobs match your preferences")
- **v3-19**: Fixed API key access - fetch from Airtable Config instead of env vars (n8n Cloud blocks all env var access)
- **v3-18**: Changed schedule from every 5 minutes to every hour (90% execution savings)
- **v3-17**: Refactored Claude API to use HTTP Request node (n8n Cloud blocks env vars in Code/Set nodes); split into Fetch Profile → Build Prompt → Call Claude API → Parse Response
- **v3-16**: Updated Jobright parser for new email format (Jan 2026) - supports inline styles instead of HTML IDs
- **v3-15**: Moved ANTHROPIC_API_KEY to n8n environment variable for efficiency; removed Airtable Config dependency
- **v3-14**: Updated Welcome to the Jungle parser to extract unique job URLs; fixed fetch() error; added Industry and Company Stage fields via Claude AI; fixed Jobright parser to detect salary vs location by content and ignore referral tags
- **v3-13**: Store API key in Airtable Config table (no secrets in workflow file)
- **v3-12**: Added Claude AI integration to rate job fit (0-100 score with rationale)
- **v3-11**: Added try-catch error handling, increased schedule to 5 minutes, added Airtable 30-day date filter
- **v3-10**: Fixed LinkedIn parser to correctly split job listings by newlines
- **v3-9**: Added role filtering, fixed email ID tracking for labeling, added Jobright and Google Careers support
- **v3-8**: Added role filter for support/success leadership
- **v3-7**: Added Google Careers support
- **v3-6**: Added Jobright.ai support
- **v3-5**: Fixed Built In job URL extraction
- **v3-4**: Fixed Built In parser for new email format, rewrote Parse Jobs to use "Run Once for All Items" mode
- **v3-3**: Added Mark as Read early to prevent race conditions
