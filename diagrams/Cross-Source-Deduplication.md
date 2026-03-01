flowchart LR
    subgraph Callers["Calling Workflows"]
        JOB_PIPE[Job Evaluation<br/>Pipeline v3]
        COMP_PIPE[Enrich & Evaluate<br/>Pipeline v4]
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
