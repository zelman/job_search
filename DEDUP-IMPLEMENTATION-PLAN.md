# Cross-Source Deduplication Implementation Plan

## Overview

Implement a lookup table approach to prevent duplicate job/company evaluations across all sources. This saves Claude API costs and reduces noise in Airtable.

**Problem:**
- Same job appears from multiple sources (LinkedIn email + Work at a Startup + VC scraper)
- Same company appears in both Job Listings and Funding Alerts tables
- Currently each workflow only deduplicates against its own target table
- Result: Duplicate evaluations, wasted API calls, cluttered views

**Solution:**
Create a central `Seen Opportunities` lookup table that all workflows check before evaluation.

---

## Step 1: Create Airtable Table

**Use Airtable MCP to create this table in base `appFEzXvPWvRtXgRY`:**

### Table: `Seen Opportunities`

| Field Name | Field Type | Configuration |
|------------|------------|---------------|
| `Key` | Single line text | Primary field |
| `Company` | Single line text | |
| `Title` | Single line text | Blank for VC company records |
| `Record Type` | Single select | Options: `job`, `company` |
| `First Source` | Single line text | e.g., "LinkedIn", "Work at a Startup", "Pear VC" |
| `All Sources` | Long text | Comma-separated, updated when dupe found |
| `First Seen` | Date | Include time field |
| `Job Record ID` | Single line text | Airtable record ID from Job Listings |
| `Company Record ID` | Single line text | Airtable record ID from Funding Alerts |

---

## Step 2: Key Generation Logic

The `Key` field uses a normalized hash to catch variations:

```javascript
// For jobs (from Job Listings workflows):
const normalizeKey = (company, title) => {
  const normCompany = company.toLowerCase().replace(/[^a-z0-9]/g, '').trim();
  const normTitle = title.toLowerCase().replace(/[^a-z0-9]/g, '').trim();
  return `job:${normCompany}:${normTitle}`;
};

// For companies (from VC scraper workflows):
const normalizeKey = (company) => {
  const normCompany = company.toLowerCase().replace(/[^a-z0-9]/g, '').trim();
  return `company:${normCompany}`;
};
```

**Examples:**
- Job: `job:acmecorp:headsupportoperations`
- Company: `company:acmecorp`

---

## Step 3: Create Dedup Subworkflow

**File:** `Dedup Check Subworkflow.json`

### Workflow Logic:

```
Execute Workflow Trigger (receives job/company data)
       │
       ▼
Generate Normalized Key
       │
       ▼
Query Seen Opportunities (filterByFormula: {Key} = 'generated_key')
       │
       ├── Found → Return { isDuplicate: true, existingRecordId, allSources }
       │
       └── Not Found → Return { isDuplicate: false }
```

### Input Schema (what calling workflows pass in):
```json
{
  "company": "Acme Corp",
  "title": "Head of Support",       // optional, blank for companies
  "source": "LinkedIn",
  "recordType": "job"               // or "company"
}
```

### Output Schema:
```json
{
  "isDuplicate": false,
  "key": "job:acmecorp:headsupportoperations",
  "existingRecordId": null,         // or the Seen Opportunities record ID if dupe
  "allSources": null                // or "LinkedIn, Indeed" if dupe
}
```

---

## Step 4: Create Dedup Registration Subworkflow

**File:** `Dedup Register Subworkflow.json`

Called AFTER successful Airtable record creation to register the new opportunity.

### Input Schema:
```json
{
  "key": "job:acmecorp:headsupportoperations",
  "company": "Acme Corp",
  "title": "Head of Support",
  "source": "LinkedIn",
  "recordType": "job",
  "airtableRecordId": "rec123abc"   // the newly created Job Listings or Funding Alerts record
}
```

### Workflow Logic:
```
Execute Workflow Trigger
       │
       ▼
Create Record in Seen Opportunities
  - Key: input.key
  - Company: input.company
  - Title: input.title
  - Record Type: input.recordType
  - First Source: input.source
  - All Sources: input.source
  - First Seen: NOW()
  - Job Record ID: input.airtableRecordId (if job)
  - Company Record ID: input.airtableRecordId (if company)
```

---

## Step 5: Update Existing Workflows

### Workflows to Update:

1. **Job Alert Email Parser v3-35.json**
2. **Work at a Startup Scraper v12.json**
3. **Indeed Job Scraper v4.json**
4. **Job Evaluation Pipeline.json** (shared subworkflow for jobs)
5. **Enrich & Evaluate Pipeline.json** (shared subworkflow for VC companies)

### Integration Points:

**For Job Evaluation Pipeline.json:**
```
[Before Build Prompt]
       │
       ▼
Execute Dedup Check Subworkflow
       │
       ├── isDuplicate: true → Skip (optionally update All Sources field)
       │
       └── isDuplicate: false → Continue to Build Prompt → ... → Airtable Create
                                                                      │
                                                                      ▼
                                                        Execute Dedup Register Subworkflow
```

**For Enrich & Evaluate Pipeline.json:**
Same pattern, but use `recordType: "company"` and only pass company name (no title).

---

## Step 6: Backfill Existing Records (Optional)

After implementation, run a one-time backfill to populate `Seen Opportunities` with existing records:

1. Query all records from `Job Listings`
2. Query all records from `Funding Alerts`
3. Generate keys for each
4. Insert into `Seen Opportunities`

This ensures existing records are recognized as duplicates if they reappear.

---

## File Locations

All workflow files are in:
```
/Users/zelman/Desktop/Quarantine/Side Projects/Job Search/
```

Key files to modify:
- `Job Evaluation Pipeline.json` - shared job evaluation subworkflow
- `Enrich & Evaluate Pipeline.json` - shared company evaluation subworkflow

New files to create:
- `Dedup Check Subworkflow.json`
- `Dedup Register Subworkflow.json`

---

## Airtable Base Info

- **Base ID:** `appFEzXvPWvRtXgRY`
- **Job Listings Table ID:** `tbl6ZV2rHjWz56pP3`
- **Funding Alerts Table:** `Funding Alerts` (need to get ID)
- **Config Table ID:** `tblofzQpzGEN8igVS`

---

## Version Updates Required

After implementation, update:
- `Job Evaluation Pipeline.json` → increment version in name
- `Enrich & Evaluate Pipeline.json` → increment version in name
- `CLAUDE.md` → update version list
- `ARCHITECTURE.md` → add Dedup layer to system diagram
- `SYSTEM-OVERVIEW.md` → document the dedup system

---

## Summary Checklist

- [ ] Create `Seen Opportunities` table in Airtable (use MCP)
- [ ] Create `Dedup Check Subworkflow.json`
- [ ] Create `Dedup Register Subworkflow.json`
- [ ] Update `Job Evaluation Pipeline.json` to call dedup subworkflows
- [ ] Update `Enrich & Evaluate Pipeline.json` to call dedup subworkflows
- [ ] Test with manual workflow execution
- [ ] Optional: Run backfill for existing records
- [ ] Update documentation (CLAUDE.md, ARCHITECTURE.md, SYSTEM-OVERVIEW.md)
