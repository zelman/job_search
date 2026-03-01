flowchart TB
    subgraph Sources["Data Sources"]
        EMAIL[/"Email Alerts<br/>(10 job boards)"/]
        YC[/"Work at a Startup<br/>(YC + Costanoa)"/]
        VC[/"VC Portfolio Scrapers<br/>(Healthcare, Climate, Social Justice,<br/>Enterprise, Micro-VC + Y Combinator)"/]
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

    subgraph CompanyPipeline["Enrich & Evaluate Pipeline v4"]
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
