# n8n Job Alert Parser - Improvement Suggestions

## Workflow Overview

This n8n workflow automates job search by:
1. Fetching job alert emails from Gmail every minute
2. Identifying email sources (LinkedIn, Indeed, Built In, Wellfound, Himalayas, Remotive, Google Careers, Jobright)
3. Parsing email content using source-specific parsers
4. Filtering for customer support/success leadership roles
5. Deduplicating against existing Airtable records
6. Saving new jobs to Airtable and labeling processed emails

---

## 1. Modularize Parser Functions

### Current Issue
The `Parse Jobs` node contains 200+ lines with all parsers in one function, making it difficult to maintain and debug.

### Recommendation
Split into source-specific nodes or use a switch/router pattern.

### Example Structure
```javascript
// Option A: Use n8n Switch node to route by source
// Then have separate Code nodes for each source

// Option B: Create reusable function library
const PARSERS = {
  LinkedIn: (textContent, htmlContent) => {
    const jobs = [];
    const sections = textContent.split(/[-]{10,}/);
    
    for (const section of sections) {
      const urlMatch = section.match(/linkedin\.com\/(?:comm\/)?jobs\/view\/(\d+)/);
      if (!urlMatch) continue;
      
      const jobId = urlMatch[1];
      const jobUrl = `https://www.linkedin.com/jobs/view/${jobId}`;
      const textBefore = section.split(/View job/i)[0].trim();
      
      const parts = textBefore
        .replace(/https?:\/\/[^\s]+/g, '')
        .split(/\n/)
        .map(p => p.replace(/\s+/g, ' ').trim())
        .filter(p => p.length > 1);
      
      const noise = ['high skills match', 'fast growing', 'actively hiring'];
      const cleanParts = parts.filter(p => !noise.some(n => p.toLowerCase().includes(n)));
      
      if (cleanParts.length >= 2) {
        jobs.push({
          title: cleanParts[0],
          company: cleanParts[1],
          location: cleanParts[2] || 'United States',
          salary: 'Not specified',
          source: 'LinkedIn',
          url: jobUrl,
          jobId: `linkedin-${jobId}`
        });
      }
    }
    return jobs;
  },
  
  Himalayas: (textContent, htmlContent) => {
    const jobs = [];
    const seenJobs = new Set();
    
    // URL-decode content
    let decodedContent = textContent;
    try {
      decodedContent = decodeURIComponent(decodeURIComponent(textContent));
    } catch (e) {
      try {
        decodedContent = decodeURIComponent(textContent);
      } catch (e2) {
        // Keep original if decoding fails
      }
    }
    
    // Extract jobs from URLs
    const urlPattern = /himalayas\.app\/companies\/([^\/]+)\/jobs\/([^\s\/\]"&<>]+)/gi;
    let urlMatch;
    
    while ((urlMatch = urlPattern.exec(decodedContent)) !== null) {
      const companySlug = urlMatch[1];
      const titleSlug = urlMatch[2];
      
      const company = companySlug.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
      const title = titleSlug
        .replace(/-\d+$/, '')
        .split('-')
        .map(w => w.charAt(0).toUpperCase() + w.slice(1))
        .join(' ');
      
      const key = `${title.toLowerCase()}-${company.toLowerCase()}`;
      if (seenJobs.has(key)) continue;
      seenJobs.add(key);
      
      jobs.push({
        title,
        company,
        location: 'Remote',
        salary: 'Not specified',
        source: 'Himalayas',
        url: `https://himalayas.app/companies/${companySlug}/jobs/${titleSlug}`,
        jobId: `himalayas-${Date.now()}-${jobs.length}`
      });
    }
    
    return jobs;
  }
  
  // Add other parsers...
};

// Main parsing logic
const source = $input.item.json._source;
const parserFn = PARSERS[source] || PARSERS.Generic;
const jobs = parserFn(textContent, htmlContent);
```

---

## 2. Extract and Reuse Helper Functions

### Current Issue
Helper functions like `decodeBase64Url`, `stripHtml`, `normalize` are defined multiple times across different nodes.

### Recommendation
Create a shared utility node or npm module (if self-hosted).

### Example: Shared Utilities Node
```javascript
// Create a node called "Utilities" that exports helper functions
// This can be referenced by other nodes using $('Utilities').item.json.helpers

module.exports = {
  // Decode base64url (Gmail API format)
  decodeBase64Url: (data) => {
    if (!data) return '';
    if (/\s{2,}/.test(data) && /[a-z]{4,}\s+[a-z]{4,}/i.test(data)) return data;
    
    const sample = data.substring(0, 100);
    if (!/\s/.test(sample) && /^[A-Za-z0-9_-]+=*$/.test(sample.replace(/\s/g, ''))) {
      try {
        const cleaned = data.replace(/\s/g, '');
        const base64 = cleaned.replace(/-/g, '+').replace(/_/g, '/');
        const decoded = Buffer.from(base64, 'base64').toString('utf-8');
        if (/[a-z]{3,}/i.test(decoded) && !/[\x00-\x08\x0B\x0C\x0E-\x1F]/.test(decoded)) {
          return decoded;
        }
      } catch (e) {}
    }
    return data;
  },
  
  // Strip HTML tags
  stripHtml: (html) => {
    if (!html) return '';
    return html
      .replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '')
      .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '')
      .replace(/<[^>]+>/g, ' ')
      .replace(/&nbsp;/g, ' ')
      .replace(/&amp;/g, '&')
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/&#39;/g, "'")
      .replace(/&quot;/g, '"')
      .replace(/\s+/g, ' ')
      .trim();
  },
  
  // Normalize string for comparison
  normalize: (str) => {
    if (!str) return '';
    return str
      .toLowerCase()
      .replace(/[^a-z0-9\s]/g, '')
      .replace(/\s+/g, ' ')
      .trim();
  },
  
  // Extract text from Gmail MIME parts
  extractTextFromParts: (parts) => {
    if (!parts || !Array.isArray(parts)) return '';
    
    for (const part of parts) {
      const mimeType = part.mimeType || '';
      
      if (mimeType === 'text/plain' && part.body && part.body.data) {
        return module.exports.decodeBase64Url(part.body.data);
      }
      
      if (mimeType.startsWith('multipart/') && part.parts) {
        const nested = module.exports.extractTextFromParts(part.parts);
        if (nested) return nested;
      }
    }
    
    // Fallback to text/html
    for (const part of parts) {
      if (part.mimeType === 'text/html' && part.body && part.body.data) {
        const html = module.exports.decodeBase64Url(part.body.data);
        return module.exports.stripHtml(html);
      }
      if (part.parts) {
        const nested = module.exports.extractTextFromParts(part.parts);
        if (nested) return nested;
      }
    }
    
    return '';
  },
  
  // Extract HTML from Gmail MIME parts
  extractHtmlFromParts: (parts) => {
    if (!parts || !Array.isArray(parts)) return '';
    
    for (const part of parts) {
      if (part.mimeType === 'text/html' && part.body && part.body.data) {
        return module.exports.decodeBase64Url(part.body.data);
      }
      if (part.parts) {
        const nested = module.exports.extractHtmlFromParts(part.parts);
        if (nested) return nested;
      }
    }
    return '';
  }
};

return { json: { helpers: module.exports } };
```

### Using Utilities in Other Nodes
```javascript
// Reference utilities from another node
const utils = $('Utilities').item.json.helpers;

// Use the helpers
const cleanText = utils.stripHtml(htmlContent);
const normalizedTitle = utils.normalize(jobTitle);
```

---

## 3. Add Comprehensive Error Handling

### Current Issue
No error handling means one parser failure could break the entire workflow.

### Recommendation
Wrap each parser in try-catch blocks with logging.

### Example
```javascript
const allJobs = [];
const errors = [];

// Process each email
for (const emailItem of allEmails) {
  try {
    const email = emailItem.json;
    const source = email._source || 'Other';
    
    // Extract content (wrap this too)
    let textContent = '';
    let htmlContent = '';
    
    try {
      // Content extraction logic
      textContent = extractTextFromEmail(email);
      htmlContent = extractHtmlFromEmail(email);
    } catch (contentError) {
      errors.push({
        emailId: email.id,
        source,
        stage: 'content_extraction',
        error: contentError.message
      });
      continue; // Skip this email
    }
    
    // Parse jobs by source
    let jobs = [];
    try {
      if (source === 'LinkedIn') {
        jobs = parseLinkedInJobs(textContent, htmlContent);
      } else if (source === 'Himalayas') {
        jobs = parseHimalayasJobs(textContent, htmlContent);
      }
      // ... other sources
    } catch (parseError) {
      errors.push({
        emailId: email.id,
        source,
        stage: 'parsing',
        error: parseError.message,
        stack: parseError.stack
      });
      // Continue to next email instead of failing entirely
      continue;
    }
    
    // Add jobs to results
    for (const job of jobs) {
      allJobs.push({
        ...job,
        _dateFound: new Date().toISOString().split('T')[0],
        _emailId: email.id
      });
    }
    
  } catch (error) {
    errors.push({
      emailId: emailItem.json.id,
      stage: 'email_processing',
      error: error.message,
      stack: error.stack
    });
  }
}

// Log errors for debugging
if (errors.length > 0) {
  console.error('Parsing errors:', JSON.stringify(errors, null, 2));
}

// Return results even if some emails failed
return allJobs.length > 0 
  ? allJobs.map(job => ({ json: job }))
  : [{ json: { _noJobs: true, _errors: errors } }];
```

---

## 4. Make Role Filtering Configurable

### Current Issue
Keywords are hardcoded, making it difficult to adjust filtering criteria.

### Recommendation
Use workflow variables or environment variables for configuration.

### Example: Using Workflow Variables
```javascript
// In n8n, you can set workflow static data or use environment variables
// For this example, we'll use workflow settings

// Define configuration (could be in a separate "Config" node)
const CONFIG = {
  supportKeywords: [
    'support', 'success', 'customer', 'client', 
    'cx', 'experience', 'service', 'care'
  ],
  leadershipKeywords: [
    'manager', 'director', 'vp', 'vice president', 
    'head', 'lead', 'chief', 'supervisor', 'team lead',
    'senior manager', 'sr manager', 'senior director'
  ],
  excludeKeywords: [
    'intern', 'internship', 'junior', 'jr', 
    'entry level', 'associate', 'part-time'
  ],
  minTitleLength: 5,
  minCompanyLength: 2
};

// Or use environment variables (if available in your n8n setup)
// const CONFIG = {
//   supportKeywords: $env.SUPPORT_KEYWORDS?.split(',') || ['support', 'success'],
//   leadershipKeywords: $env.LEADERSHIP_KEYWORDS?.split(',') || ['manager', 'director']
// };

// Enhanced filtering function
const isRelevantRole = (title, config = CONFIG) => {
  const titleLower = (title || '').toLowerCase();
  
  // Check if title is long enough
  if (titleLower.length < config.minTitleLength) return false;
  
  // Exclude certain roles
  const hasExcluded = config.excludeKeywords.some(kw => titleLower.includes(kw));
  if (hasExcluded) return false;
  
  // Must have both support/success AND leadership keywords
  const hasSupport = config.supportKeywords.some(kw => titleLower.includes(kw));
  const hasLeadership = config.leadershipKeywords.some(kw => titleLower.includes(kw));
  
  return hasSupport && hasLeadership;
};

// Apply filtering
const items = $input.all().filter(item => !item.json._empty);
const filteredItems = items.filter(item => isRelevantRole(item.json.title));

// Log filtering stats
console.log(`Filtered ${items.length} jobs down to ${filteredItems.length} relevant roles`);

if (filteredItems.length === 0) {
  return [{ json: { _empty: true } }];
}

return filteredItems.map(item => ({
  json: {
    "Job Title": item.json.title,
    "Company": item.json.company,
    "Location": item.json.location,
    "Source": item.json.source,
    "Job URL": item.json.url,
    "Job ID": item.json.jobId,
    "Salary Info": item.json.salary,
    "Date Found": item.json._dateFound,
    "Review Status": "New",
    "_emailId": item.json._emailId
  }
}));
```

---

## 5. Improve Deduplication with Fuzzy Matching

### Current Issue
Exact matching may miss duplicates like "Sr. Manager" vs "Senior Manager".

### Recommendation
Add fuzzy matching or similarity scoring.

### Example: Enhanced Deduplication
```javascript
const crypto = require('crypto');

// Aggressive normalization
const normalize = (str) => {
  if (!str) return '';
  return str
    .toLowerCase()
    // Normalize common abbreviations
    .replace(/\bsr\.?\s/g, 'senior ')
    .replace(/\bjr\.?\s/g, 'junior ')
    .replace(/\bmgr\.?\s/g, 'manager ')
    .replace(/\bvp\.?\s/g, 'vice president ')
    .replace(/\bcx\b/g, 'customer experience')
    .replace(/\bcs\b/g, 'customer success')
    // Remove special characters
    .replace(/[^a-z0-9\s]/g, '')
    // Collapse multiple spaces
    .replace(/\s+/g, ' ')
    .trim();
};

// Generate consistent hash for job
const generateJobHash = (title, company) => {
  const normalizedTitle = normalize(title);
  const normalizedCompany = normalize(company);
  return crypto.createHash('md5')
    .update(`${normalizedTitle}|${normalizedCompany}`)
    .digest('hex');
};

// Simple Levenshtein distance for fuzzy matching (optional)
const levenshteinDistance = (str1, str2) => {
  const matrix = [];
  
  for (let i = 0; i <= str2.length; i++) {
    matrix[i] = [i];
  }
  
  for (let j = 0; j <= str1.length; j++) {
    matrix[0][j] = j;
  }
  
  for (let i = 1; i <= str2.length; i++) {
    for (let j = 1; j <= str1.length; j++) {
      if (str2.charAt(i - 1) === str1.charAt(j - 1)) {
        matrix[i][j] = matrix[i - 1][j - 1];
      } else {
        matrix[i][j] = Math.min(
          matrix[i - 1][j - 1] + 1,
          matrix[i][j - 1] + 1,
          matrix[i - 1][j] + 1
        );
      }
    }
  }
  
  return matrix[str2.length][str1.length];
};

// Check if two jobs are similar
const areSimilarJobs = (job1, job2, threshold = 0.85) => {
  const title1 = normalize(job1.title || '');
  const title2 = normalize(job2.title || '');
  const company1 = normalize(job1.company || '');
  const company2 = normalize(job2.company || '');
  
  // Exact match after normalization
  if (title1 === title2 && company1 === company2) return true;
  
  // Fuzzy match on title if companies match
  if (company1 === company2) {
    const distance = levenshteinDistance(title1, title2);
    const maxLen = Math.max(title1.length, title2.length);
    const similarity = 1 - (distance / maxLen);
    return similarity >= threshold;
  }
  
  return false;
};

// Main deduplication logic
const allItems = $input.all();

const newJobs = allItems.filter(item => 
  item.json.title && item.json.source && !item.json.fields && !item.json["Job Title"]
);

const existingRecords = allItems.filter(item => 
  item.json.fields || item.json["Job Title"] || (item.json["Job URL"] && !item.json.source)
);

// Build existing job index
const existingUrls = new Set();
const existingHashes = new Set();
const existingJobs = [];

for (const item of existingRecords) {
  const fields = item.json.fields || item.json;
  
  // Normalize and store URL
  let url = fields["Job URL"] || "";
  if (url) {
    url = url.split('?')[0].replace(/\/$/, '');
    existingUrls.add(url);
  }
  
  // Generate and store hash
  const title = fields["Job Title"] || "";
  const company = fields["Company"] || "";
  if (title && company) {
    const hash = generateJobHash(title, company);
    existingHashes.add(hash);
    existingJobs.push({ title, company, url });
  }
}

// Filter new jobs
const results = [];
const duplicateReasons = [];

for (const job of newJobs) {
  // Normalize URL
  let url = job.json.url || "";
  if (url) {
    url = url.split('?')[0].replace(/\/$/, '');
  }
  
  const isGenericUrl = url.endsWith('/jobs') || url.endsWith('/remote-jobs');
  
  // Check URL duplicate
  if (url && !isGenericUrl && existingUrls.has(url)) {
    duplicateReasons.push({ job: job.json.title, reason: 'URL match', url });
    continue;
  }
  
  // Check hash duplicate
  const hash = generateJobHash(job.json.title, job.json.company);
  if (existingHashes.has(hash)) {
    duplicateReasons.push({ job: job.json.title, reason: 'Hash match', hash });
    continue;
  }
  
  // Check fuzzy duplicate (optional, more expensive)
  let isFuzzyDupe = false;
  for (const existingJob of existingJobs) {
    if (areSimilarJobs(job.json, existingJob)) {
      duplicateReasons.push({ 
        job: job.json.title, 
        reason: 'Fuzzy match',
        matchedWith: existingJob.title 
      });
      isFuzzyDupe = true;
      break;
    }
  }
  if (isFuzzyDupe) continue;
  
  // Add to results
  if (url && !isGenericUrl) existingUrls.add(url);
  existingHashes.add(hash);
  existingJobs.push({ title: job.json.title, company: job.json.company, url });
  
  results.push(job);
}

// Log deduplication stats
console.log(`Deduplication: ${newJobs.length} new jobs -> ${results.length} unique jobs`);
console.log(`Filtered out ${duplicateReasons.length} duplicates`);

return results.length ? results : [{ json: { _empty: true } }];
```

---

## 6. Optimize Execution Interval and API Calls

### Current Issue
Running every minute may be excessive and could hit rate limits.

### Recommendations

#### Option A: Increase Interval
```javascript
// In Schedule Trigger node, change from:
{ "field": "minutes" }

// To (every 15 minutes):
{ 
  "field": "minutes",
  "minutesInterval": 15
}

// Or (hourly at specific times):
{
  "field": "hours",
  "hoursInterval": 1,
  "triggerAtMinute": 0
}
```

#### Option B: Optimize Airtable Query
```javascript
// Instead of fetching ALL records, use date filter in "Search records" node

// In the Airtable node options, add a formula:
{
  "filterByFormula": "IS_AFTER({Date Found}, DATEADD(TODAY(), -30, 'days'))"
}

// This reduces the data fetched and speeds up deduplication
```

#### Option C: Add Caching
```javascript
// Use workflow static data to cache recent jobs for faster lookups
// In the deduplication node:

const workflowData = this.getWorkflowStaticData('global');

// Initialize cache if not exists
if (!workflowData.recentJobsCache) {
  workflowData.recentJobsCache = {
    urls: new Set(),
    hashes: new Set(),
    lastCleared: Date.now()
  };
}

// Clear cache daily
const oneDayMs = 24 * 60 * 60 * 1000;
if (Date.now() - workflowData.recentJobsCache.lastCleared > oneDayMs) {
  workflowData.recentJobsCache = {
    urls: new Set(),
    hashes: new Set(),
    lastCleared: Date.now()
  };
}

// Use cache for quick lookups
const cache = workflowData.recentJobsCache;

// ... deduplication logic using cache ...

// Update cache with new jobs
for (const job of results) {
  if (job.url) cache.urls.add(job.url);
  cache.hashes.add(generateJobHash(job.title, job.company));
}
```

---

## 7. Add Error Recovery and Notifications

### Recommendation
Create an error handling sub-workflow.

### Example: Error Notification Node
```javascript
// Add after critical nodes to catch errors
// Use n8n's "Error Trigger" node to catch workflow errors

// In a separate error workflow:
const errorInfo = {
  workflow: $workflow.name,
  execution: $execution.id,
  error: $json.error,
  node: $json.node,
  timestamp: new Date().toISOString(),
  data: $json.data
};

// Send to Slack or email
return [{
  json: {
    text: `🚨 n8n Workflow Error: ${errorInfo.workflow}`,
    blocks: [
      {
        type: "section",
        text: {
          type: "mrkdwn",
          text: `*Error in workflow:* ${errorInfo.workflow}\n*Node:* ${errorInfo.node}\n*Time:* ${errorInfo.timestamp}\n*Error:* \`${errorInfo.error.message}\``
        }
      }
    ]
  }
}];
```

### Add Retry Logic
```javascript
// Wrap API calls with retry logic
const retryWithBackoff = async (fn, maxRetries = 3, initialDelay = 1000) => {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      
      const delay = initialDelay * Math.pow(2, i);
      console.log(`Retry ${i + 1}/${maxRetries} after ${delay}ms`);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
};

// Usage in Gmail node or Airtable operations:
// (Note: This is conceptual - n8n has built-in retry mechanisms)
const emails = await retryWithBackoff(async () => {
  return await fetchGmailMessages();
});
```

---

## 8. Add Testing and Debugging Capabilities

### Recommendation
Create a test workflow with sample data.

### Example: Test Data Setup
```javascript
// Create a separate workflow called "Job Parser - Test"
// Add a "Manual Trigger" node with test data

const testEmails = [
  {
    id: "test-linkedin-1",
    _source: "LinkedIn",
    textPlain: `
Senior Customer Success Manager
Acme Corp
Remote
$120k - $150k
--------------------------------------
View job: https://linkedin.com/jobs/view/123456789
    `.trim()
  },
  {
    id: "test-himalayas-1",
    _source: "Himalayas",
    textPlain: `
Your top matches for 2024
Customer Success Director Globex Corporation
https://himalayas.app/companies/globex-corporation/jobs/customer-success-director-9491544946
    `.trim()
  },
  {
    id: "test-builtin-1",
    _source: "Built In",
    textPlain: `
Senior Level
Contoso Customer Support Director Remote $140,000 - $160,000
    `.trim()
  }
];

return testEmails.map(email => ({ json: email }));
```

### Add Debug Logging
```javascript
// Create a reusable debug function
const DEBUG = true; // Set to false in production

const debug = (label, data) => {
  if (DEBUG) {
    console.log(`[DEBUG] ${label}:`, JSON.stringify(data, null, 2));
  }
};

// Use throughout your code
debug('Email received', { id: email.id, source: email._source });
debug('Parsed jobs', { count: jobs.length, jobs });
debug('After dedup', { count: filteredJobs.length });
```

---

## 9. Source Parser Specific Improvements

### LinkedIn Parser Enhancement
```javascript
// Add salary extraction for LinkedIn
const parseLinkedInJobs = (textContent, htmlContent) => {
  const jobs = [];
  const sections = textContent.split(/[-]{10,}/);

  for (const section of sections) {
    const urlMatch = section.match(/linkedin\.com\/(?:comm\/)?jobs\/view\/(\d+)/);
    if (!urlMatch) continue;

    const jobId = urlMatch[1];
    const jobUrl = `https://www.linkedin.com/jobs/view/${jobId}`;
    const textBefore = section.split(/View job/i)[0].trim();

    // Extract salary if present
    const salaryMatch = textBefore.match(/\$[\d,]+(?:\s*[-–]\s*\$?[\d,]+)?(?:\s*(?:\/|per)\s*(?:year|yr|hour|hr))?/i);
    const salary = salaryMatch ? salaryMatch[0] : 'Not specified';

    const parts = textBefore
      .replace(/https?:\/\/[^\s]+/g, '')
      .replace(/\$[\d,]+(?:\s*[-–]\s*\$?[\d,]+)?/g, '') // Remove salary from parts
      .split(/\n/)
      .map(p => p.replace(/\s+/g, ' ').trim())
      .filter(p => p.length > 1);

    const noise = [
      'high skills match', 'fast growing', 'actively hiring', 
      'connections', 'posted', 'applicants', 'promoted', 
      'apply with resume', 'this company is', 'school alum', 
      'connection', 'top job picks', 'easy apply'
    ];
    
    const cleanParts = parts.filter(p => 
      !noise.some(n => p.toLowerCase().includes(n))
    );

    if (cleanParts.length >= 2) {
      jobs.push({
        title: cleanParts[0],
        company: cleanParts[1],
        location: cleanParts[2] || 'United States',
        salary: salary,
        source: 'LinkedIn',
        url: jobUrl,
        jobId: `linkedin-${jobId}`
      });
    }
  }
  
  return jobs;
};
```

### Wellfound Parser Enhancement
```javascript
// Improved Wellfound parser with better location extraction
const parseWellfoundJobs = (textContent, htmlContent) => {
  const jobs = [];
  
  // Extract job URLs
  const urlMatches = [...textContent.matchAll(/wellfound\.com\/jobs\?job_listing_slug=(\d+[^\s>"'\]]*)/gi)];
  const jobSlugs = urlMatches.map(m => m[1]);
  
  // Enhanced pattern with better location capture
  const jobPattern = /([A-Za-z][A-Za-z\s&\-,\(\)]+?(?:Manager|Director|Specialist|Associate|Coordinator|Analyst|Engineer|Representative|Support|Success)(?:[A-Za-z\s&\-,\(\)]*?))\s+([A-Z][A-Za-z0-9\s&\.\-']+?)\s*\/\s*(\d+[-–]\d+|\d+\+?)\s*Employees\s*\|\s*([^\|]+?)(?:\s*\||$)/gi;
  
  let match;
  let index = 0;
  
  while ((match = jobPattern.exec(textContent)) !== null) {
    const title = match[1].trim();
    const company = match[2].trim();
    const size = match[3];
    const location = match[4].trim();
    
    // Clean location (remove extra info like "· Full-time")
    const cleanLocation = location.split('·')[0].trim();
    
    jobs.push({
      title: title,
      company: company,
      location: cleanLocation || 'Remote',
      salary: 'Not specified',
      source: 'Wellfound',
      url: jobSlugs[index] ? `https://wellfound.com/jobs?job_listing_slug=${jobSlugs[index]}` : 'https://wellfound.com',
      jobId: jobSlugs[index] ? `wellfound-${jobSlugs[index].split('-')[0]}` : `wellfound-${Date.now()}-${index}`,
      _companySize: `${size} Employees`
    });
    index++;
  }
  
  return jobs;
};
```

### Built In Parser Simplification
```javascript
// Simplified Built In parser with cleaner regex
const parseBuiltInJobs = (textContent, htmlContent) => {
  const jobs = [];
  
  // Extract URLs first
  const builtInUrls = [];
  const urlPattern = /https?:\/\/(?:www\.)?builtin\.com\/job\/[^\s"'<>]+/gi;
  let urlMatch;
  while ((urlMatch = urlPattern.exec(htmlContent || textContent)) !== null) {
    builtInUrls.push(urlMatch[0].replace(/&amp;/g, '&'));
  }
  
  // Find job section
  const sectionMatch = textContent.match(/(?:Senior Level|Expert Level|Entry Level|Mid Level)\s+([\s\S]*?)(?:Get More|©|Built In,)/i);
  if (!sectionMatch) return jobs;
  
  const jobSection = sectionMatch[1].trim();
  
  // Split by salary (reliable anchor point)
  const salaryPattern = /\$[\d,]+(?:\s*-\s*\$?[\d,]+)?/g;
  const salaries = [];
  let salaryMatch;
  
  while ((salaryMatch = salaryPattern.exec(jobSection)) !== null) {
    salaries.push({ text: salaryMatch[0], index: salaryMatch.index });
  }
  
  // Parse each job
  for (let i = 0; i < salaries.length; i++) {
    const startIdx = i === 0 ? 0 : salaries[i-1].index + salaries[i-1].text.length;
    const endIdx = salaries[i].index;
    const jobText = jobSection.substring(startIdx, endIdx).trim();
    const salary = salaries[i].text;
    
    if (jobText.length < 10) continue;
    
    // Extract location (end of string)
    const locationMatch = jobText.match(/((?:Remote(?:\s+[A-Za-z]+)*|[A-Z][a-z]+(?:,\s*[A-Z]{2})?))$/);
    const location = locationMatch ? locationMatch[1].trim() : 'Not specified';
    const textWithoutLoc = locationMatch ? jobText.substring(0, locationMatch.index).trim() : jobText;
    
    // Split into company and title
    // Title typically starts with role keywords
    const titlePattern = /((?:Sr\.?|Senior|Director|Manager|Lead|VP|Head|Chief)[\s\S]*?)$/i;
    const titleMatch = textWithoutLoc.match(titlePattern);
    
    let title = '';
    let company = '';
    
    if (titleMatch) {
      title = titleMatch[1].trim();
      company = textWithoutLoc.substring(0, titleMatch.index).trim();
    } else {
      // Fallback: split on last capital letter sequence
      const words = textWithoutLoc.split(/\s+/);
      company = words.slice(0, Math.ceil(words.length / 2)).join(' ');
      title = words.slice(Math.ceil(words.length / 2)).join(' ');
    }
    
    if (title && company && title.length > 3) {
      jobs.push({
        title: title,
        company: company,
        location: location,
        salary: salary,
        source: 'Built In',
        url: builtInUrls[jobs.length] || 'https://builtin.com/jobs',
        jobId: `builtin-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
      });
    }
  }
  
  return jobs;
};
```

---

## 10. Documentation and Maintenance

### Workflow Documentation Template

Add sticky notes in n8n or create a README for each node:

```
## Node: Parse Jobs
**Purpose:** Extract job listings from email content using source-specific parsers

**Input:** Email items with _source field
**Output:** Array of job objects with: title, company, location, salary, source, url, jobId

**Supported Sources:**
- LinkedIn: Parses dashed sections with "View job:" URLs
- Himalayas: Extracts from tracking URLs and text patterns
- Wellfound: Matches "Title Company / Size | Location" format
- Built In: Uses salary anchors to split job listings
- Remotive: Parses HTML <li> elements with tracking URLs
- Indeed: "Title at Company" pattern with optional salary
- Google Careers: HTML parser for Google job alerts
- Jobright: HTML parser for Jobright.ai emails

**Error Handling:** Continues on parser failure, logs errors

**Last Updated:** 2024-01-24
**Maintainer:** Your Name
```

### Maintenance Checklist

Create a document to track maintenance tasks:

```markdown
# n8n Job Parser Maintenance Checklist

## Weekly Tasks
- [ ] Check error logs for new parser failures
- [ ] Review "No Jobs Found" emails to identify new formats
- [ ] Verify deduplication is working correctly

## Monthly Tasks
- [ ] Update source parsers for format changes
- [ ] Review and update keyword filters
- [ ] Check Airtable record count and cleanup old entries
- [ ] Verify all job source URLs are still valid

## Quarterly Tasks
- [ ] Performance review (execution times, API usage)
- [ ] Add new job sources if needed
- [ ] Update documentation
- [ ] Review and optimize deduplication logic

## Parser Version History
- v3-10: Current version (2024-01-24)
  - Added Jobright parser
  - Enhanced Himalayas URL extraction
  - Improved deduplication
```

---

## Additional Best Practices

### 1. Rate Limiting
```javascript
// Add delays between API calls to avoid rate limits
const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// In loops with API calls:
for (let i = 0; i < items.length; i++) {
  // Process item
  await processItem(items[i]);
  
  // Wait between requests (e.g., 100ms)
  if (i < items.length - 1) {
    await sleep(100);
  }
}
```

### 2. Data Validation
```javascript
// Validate job data before saving
const isValidJob = (job) => {
  const checks = [
    job.title && job.title.length >= 5,
    job.company && job.company.length >= 2,
    job.source && job.source.length > 0,
    !job.title.toLowerCase().includes('unsubscribe'),
    !job.company.toLowerCase().includes('email preferences')
  ];
  
  return checks.every(check => check === true);
};

// Filter before saving
const validJobs = allJobs.filter(isValidJob);
```

### 3. Monitoring Dashboard
Create a separate workflow to track metrics:
- Jobs processed per day
- Jobs by source
- Deduplication rate
- Parser failure rate
- Most active companies

---

## Summary of Priority Improvements

### High Priority (Implement First)
1. ✅ Add error handling to prevent workflow failures
2. ✅ Extract helper functions for reusability
3. ✅ Add debugging/logging capabilities
4. ✅ Optimize Airtable query with date filters
5. ✅ Increase execution interval to reduce API calls

### Medium Priority (Implement Soon)
6. ✅ Enhance deduplication with normalization
7. ✅ Make role filtering configurable
8. ✅ Add retry logic for API calls
9. ✅ Create test workflow with sample data
10. ✅ Improve specific parsers (LinkedIn, Built In)

### Low Priority (Nice to Have)
11. ✅ Add fuzzy matching for deduplication
12. ✅ Create error notification system
13. ✅ Add caching for recent jobs
14. ✅ Create monitoring dashboard
15. ✅ Comprehensive documentation

---

## Questions?

Feel free to adapt these suggestions to your specific needs. The key principles are:
- **Modularity:** Break complex logic into smaller, reusable pieces
- **Reliability:** Add error handling and retry logic
- **Maintainability:** Document and organize code clearly
- **Performance:** Optimize API calls and data processing
- **Flexibility:** Make configurations adjustable without code changes

Good luck with your job search automation! 🚀
