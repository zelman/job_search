flowchart LR
    subgraph External["External APIs"]
        GMAIL[Gmail API]
        BRAVE[Brave Search API]
        CLAUDE[Anthropic Claude API]
        BROWSER[Browserless.io]
        GITHUB[GitHub Raw]
    end

    subgraph n8n["n8n Workflows"]
        PARSE[Email Parser<br/>v3-35]
        SCRAPE[Web Scrapers<br/>YC Jobs, VC Portfolios,<br/>YC Companies]
        EVAL_JOB[Job Evaluation<br/>Pipeline v3]
        EVAL_COMP[Enrich & Evaluate<br/>Pipeline v4]
        DEDUP[Dedup<br/>Subworkflows]
        FEEDBACK[Feedback<br/>Loops]
    end

    subgraph Airtable["Airtable Storage"]
        JOBS[(Job Listings)]
        FUNDING[(Funding Alerts)]
        SEEN[(Seen Opportunities)]
        CONFIG[(Config)]
    end

    GMAIL --> PARSE
    PARSE --> EVAL_JOB
    SCRAPE --> EVAL_JOB
    SCRAPE --> EVAL_COMP

    GITHUB -->|Tide Pool Lens| EVAL_JOB
    GITHUB -->|Tide Pool Lens| EVAL_COMP
    BRAVE --> EVAL_JOB
    BRAVE --> EVAL_COMP
    BROWSER --> SCRAPE
    BROWSER --> EVAL_JOB
    CLAUDE --> EVAL_JOB
    CLAUDE --> EVAL_COMP
    CLAUDE --> FEEDBACK

    EVAL_JOB --> JOBS
    EVAL_COMP --> FUNDING
    DEDUP --> SEEN
    JOBS --> FEEDBACK
    CONFIG --> PARSE
    CONFIG --> SCRAPE
