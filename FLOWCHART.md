# Job Search Automation - System Flowchart

## Complete System Overview

```mermaid
flowchart TB
    subgraph Sources["Data Sources"]
        EMAIL[/"Email Alerts<br/>(10 job boards)"/]
        YC[/"Work at a Startup<br/>(YC + Costanoa)"/]
        VC[/"VC Portfolio Scrapers<br/>(Healthcare, Climate, Social Justice, Enterprise, Micro-VC)"/]
    end

    subgraph JobPipeline["Job Evaluation Pipeline v3"]
        JP_DEDUP{Dedup Check}
        JP_SKIP[Skip Duplicate]
        JP_BRAVE[Brave Search<br/>Company Enrichment]
        JP_JD[Fetch Job Description<br/>HTTP + Browserless]
        JP_ENRICH[Parse Enrichment<br/>+ Scoring Penalties]
        JP_PROMPT[Build Prompt<br/>w/ Tide Pool Lens]
        JP_CLAUDE[Claude Haiku<br/>Scoring]
        JP_PARSE[Parse Response]
    end

    subgraph CompanyPipeline["Enrich & Evaluate Pipeline v2"]
        CP_DEDUP{Dedup Check}
        CP_SKIP[Skip Duplicate]
        CP_BRAVE[Brave Search<br/>Company Enrichment]
        CP_ENRICH[Parse Enrichment]
        CP_PROMPT[Build Prompt<br/>w/ Tide Pool Lens]
        CP_CLAUDE[Claude Haiku<br/>Scoring]
        CP_PARSE[Parse Response]
    end

    subgraph Storage["Airtable Storage"]
        JOBS[(Job Listings)]
        COMPANIES[(Funding Alerts)]
        SEEN[(Seen Opportunities)]
    end

    subgraph Feedback["Feedback Loops (Weekly)"]
        FB_NAF[Not a Fit Analysis<br/>Mon 9am]
        FB_APP[Applied Analysis<br/>Mon 9:30am]
        REPORT[/"Email Reports"/]
    end

    LENS[("Tide Pool<br/>Agent Lens<br/>(GitHub)")]

    %% Source to Pipeline connections
    EMAIL --> JP_DEDUP
    YC --> JP_DEDUP
    VC --> CP_DEDUP

    %% Job Pipeline flow
    JP_DEDUP -->|Duplicate| JP_SKIP
    JP_DEDUP -->|New| JP_BRAVE
    JP_BRAVE --> JP_JD
    JP_JD --> JP_ENRICH
    JP_ENRICH --> JP_PROMPT
    LENS -.->|Fetch at runtime| JP_PROMPT
    JP_PROMPT --> JP_CLAUDE
    JP_CLAUDE --> JP_PARSE
    JP_PARSE --> JOBS
    JOBS --> SEEN

    %% Company Pipeline flow
    CP_DEDUP -->|Duplicate| CP_SKIP
    CP_DEDUP -->|New| CP_BRAVE
    CP_BRAVE --> CP_ENRICH
    CP_ENRICH --> CP_PROMPT
    LENS -.->|Fetch at runtime| CP_PROMPT
    CP_PROMPT --> CP_CLAUDE
    CP_CLAUDE --> CP_PARSE
    CP_PARSE --> COMPANIES
    COMPANIES --> SEEN

    %% Feedback loops
    JOBS -->|"Not a Fit + Passed*"| FB_NAF
    JOBS -->|Applied| FB_APP
    FB_NAF --> REPORT
    FB_APP --> REPORT
    REPORT -.->|Manual updates| LENS
```

---

## Job Evaluation Pipeline v3 (Detailed)

```mermaid
flowchart LR
    subgraph Input
        TRIGGER[Execute Workflow<br/>Trigger]
    end

    subgraph Dedup["Cross-Source Dedup"]
        PREP_DEDUP[Prepare<br/>Dedup Check]
        DEDUP_SUB[Dedup Check<br/>Subworkflow]
        IF_DUP{Is<br/>Duplicate?}
        SKIP[Skip Duplicate<br/>Return Early]
        RESTORE[Restore<br/>Job Data]
    end

    subgraph Enrichment["Company Enrichment"]
        FETCH_PROFILE[Fetch Profile<br/>GitHub]
        BRAVE[Brave Search<br/>Company]
        FETCH_JD_HTTP[Fetch JD<br/>HTTP]
        IF_HTTP{HTTP<br/>Success?}
        FETCH_JD_BROWSER[Fetch JD<br/>Browserless]
        PARSE_JD[Parse Job<br/>Description]
        PARSE_ENRICH[Parse<br/>Enrichment]
    end

    subgraph Evaluation["AI Evaluation"]
        BUILD[Build Prompt]
        WAIT[Wait 30s<br/>Rate Limit]
        CLAUDE[Call Claude<br/>Haiku API]
        PARSE_RESP[Parse<br/>Response]
    end

    subgraph Output["Storage & Registration"]
        AIRTABLE[(Upsert to<br/>Airtable)]
        PREP_REG[Prepare<br/>Dedup Register]
        REG_SUB[Dedup Register<br/>Subworkflow]
        MERGE[Merge<br/>Email ID]
    end

    %% Flow
    TRIGGER --> FETCH_PROFILE
    FETCH_PROFILE --> PREP_DEDUP
    PREP_DEDUP --> DEDUP_SUB
    DEDUP_SUB --> IF_DUP
    IF_DUP -->|Yes| SKIP
    IF_DUP -->|No| RESTORE
    RESTORE --> BRAVE
    BRAVE --> FETCH_JD_HTTP
    FETCH_JD_HTTP --> IF_HTTP
    IF_HTTP -->|Yes| PARSE_JD
    IF_HTTP -->|No| FETCH_JD_BROWSER
    FETCH_JD_BROWSER --> PARSE_JD
    PARSE_JD --> PARSE_ENRICH
    PARSE_ENRICH --> BUILD
    BUILD --> WAIT
    WAIT --> CLAUDE
    CLAUDE --> PARSE_RESP
    PARSE_RESP --> AIRTABLE
    AIRTABLE --> PREP_REG
    PREP_REG --> REG_SUB
    REG_SUB --> MERGE
```

---

## Scoring Penalties Applied in Parse Enrichment

```mermaid
flowchart TD
    subgraph Input["Enrichment Data"]
        EMP[Employee Count]
        TITLE[Job Title]
    end

    subgraph Penalties["Penalty Detection"]
        CHECK_EMP{500-999<br/>employees?}
        CHECK_TITLE{Support title<br/>without<br/>Director/VP/Head?}
        PEN_EMP["-15 pts<br/>Too large for builder"]
        PEN_TITLE["-15 pts<br/>Non-senior Support role"]
    end

    subgraph Disqualifiers["Auto-Disqualifiers"]
        CHECK_PE{PE-backed?}
        CHECK_1000{1000+<br/>employees?}
        CHECK_FUND{$500M+<br/>funding?}
        DISQ[Auto-Disqualify]
    end

    subgraph Output["To Build Prompt"]
        PENALTIES_ARR["scoringPenalties[]"]
        DISQ_ARR["autoDisqualifiers[]"]
    end

    EMP --> CHECK_EMP
    EMP --> CHECK_1000
    TITLE --> CHECK_TITLE

    CHECK_EMP -->|Yes| PEN_EMP
    CHECK_EMP -->|No| PENALTIES_ARR
    PEN_EMP --> PENALTIES_ARR

    CHECK_TITLE -->|Yes| PEN_TITLE
    CHECK_TITLE -->|No| PENALTIES_ARR
    PEN_TITLE --> PENALTIES_ARR

    CHECK_PE -->|Yes| DISQ
    CHECK_1000 -->|Yes| DISQ
    CHECK_FUND -->|Yes| DISQ
    DISQ --> DISQ_ARR
```

---

## Cross-Source Deduplication Flow

```mermaid
flowchart LR
    subgraph Callers["Calling Workflows"]
        JOB_PIPE[Job Evaluation<br/>Pipeline v3]
        COMP_PIPE[Enrich & Evaluate<br/>Pipeline v2]
    end

    subgraph Check["Dedup Check Subworkflow"]
        GEN_KEY[Generate Key<br/>job:company:title<br/>company:company]
        QUERY[(Query Seen<br/>Opportunities)]
        COMPARE{Key<br/>Exists?}
        RET_DUP[Return<br/>isDuplicate: true]
        RET_NEW[Return<br/>isDuplicate: false]
    end

    subgraph Register["Dedup Register Subworkflow"]
        CREATE[(Create Seen<br/>Record)]
        CONFIRM[Return<br/>registered: true]
    end

    subgraph SeenTable["Airtable: Seen Opportunities"]
        SEEN[(Key, Company, Title,<br/>Record Type, Sources,<br/>First Seen, Record IDs)]
    end

    JOB_PIPE -->|Before eval| GEN_KEY
    COMP_PIPE -->|Before eval| GEN_KEY
    GEN_KEY --> QUERY
    QUERY --> COMPARE
    COMPARE -->|Yes| RET_DUP
    COMPARE -->|No| RET_NEW

    JOB_PIPE -->|After Airtable| CREATE
    COMP_PIPE -->|After Airtable| CREATE
    CREATE --> CONFIRM
    CREATE --> SEEN
    QUERY -.-> SEEN
```

---

## Feedback Loop - Rejected Jobs Analysis

```mermaid
flowchart LR
    subgraph Schedule
        CRON[Weekly Mon 9am]
    end

    subgraph Query["Query Rejected Jobs"]
        FILTER["Filter:<br/>Review Status = 'Not a Fit'<br/>OR starts with 'Passed'"]
        AGG[Aggregate Jobs]
    end

    subgraph Analysis["Claude Sonnet Analysis"]
        FETCH_LENS[Fetch Tide Pool Lens]
        BUILD_PROMPT[Build Analysis Prompt]
        CLAUDE[Claude Sonnet<br/>Pattern Analysis]
        PARSE[Parse Response]
    end

    subgraph Output["Report Generation"]
        FORMAT[Format HTML Report]
        EMAIL[/"Email Report"/]
    end

    subgraph Patterns["Analysis Output"]
        PAT1[Patterns Identified]
        PAT2[Suggested Disqualifiers]
        PAT3[Scoring Adjustments]
        PAT4[Working Well]
    end

    CRON --> FILTER
    FILTER --> AGG
    AGG --> FETCH_LENS
    FETCH_LENS --> BUILD_PROMPT
    BUILD_PROMPT --> CLAUDE
    CLAUDE --> PARSE
    PARSE --> PAT1
    PARSE --> PAT2
    PARSE --> PAT3
    PARSE --> PAT4
    PAT1 --> FORMAT
    PAT2 --> FORMAT
    PAT3 --> FORMAT
    PAT4 --> FORMAT
    FORMAT --> EMAIL
```

---

## VC Scraper Architecture

```mermaid
flowchart TB
    subgraph Scrapers["VC Portfolio Scrapers"]
        HC[Healthcare v25<br/>WhatIf, Leadout, Flare,<br/>7wire, Oak HC/FT,<br/>Cade, Hustle Fund]
        CT[Climate Tech v23<br/>Khosla, Congruent,<br/>Prelude, Lowercarbon]
        SJ[Social Justice v25<br/>Kapor, Backstage,<br/>Harlem, Collab]
        ENT[Enterprise v26<br/>Unusual, First Round,<br/>Essence, K9, Precursor,<br/>M25, GoAhead]
        MICRO[Micro-VC v12<br/>Pear, Floodgate, Afore,<br/>Unshackled, 2048]
    end

    subgraph Methods["Scraping Methods"]
        SITEMAP[Sitemap XML]
        BROWSER[Browserless<br/>Headless]
        STATIC[Static Lists]
        INFINITE[Infinite Scroll<br/>2048 /function]
    end

    subgraph Pipeline["Shared Subworkflow"]
        ENRICH[Enrich & Evaluate<br/>Pipeline v2]
    end

    subgraph Storage
        FUNDING[(Funding Alerts)]
    end

    HC --> BROWSER
    HC --> STATIC
    CT --> BROWSER
    CT --> STATIC
    SJ --> SITEMAP
    SJ --> STATIC
    ENT --> SITEMAP
    ENT --> BROWSER
    ENT --> STATIC
    MICRO --> BROWSER
    MICRO --> INFINITE

    SITEMAP --> ENRICH
    BROWSER --> ENRICH
    STATIC --> ENRICH
    INFINITE --> ENRICH
    ENRICH --> FUNDING
```

---

## Data Flow Summary

```mermaid
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
        SCRAPE[Web Scrapers<br/>YC, VC Portfolios]
        EVAL_JOB[Job Evaluation<br/>Pipeline v3]
        EVAL_COMP[Enrich & Evaluate<br/>Pipeline v2]
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
```

---

*Generated: February 2026*
*Renders automatically in GitHub, VS Code (with Mermaid extension), or [mermaid.live](https://mermaid.live)*
