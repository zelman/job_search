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

    subgraph Disqualifiers["Auto-Disqualifiers (Company Pipeline)"]
        CHECK_PE{PE-backed?}
        CHECK_150{>150<br/>employees?}
        CHECK_FUND{>$75M<br/>funding?}
        CHECK_PUBLIC{Public or<br/>Acquired?}
        CHECK_SECTOR{Not B2B SaaS?}
        DISQ[Auto-Disqualify<br/>Score: 0]
    end

    subgraph Output["To Build Prompt"]
        PENALTIES_ARR["scoringPenalties[]"]
        DISQ_ARR["autoDisqualifiers[]"]
    end

    EMP --> CHECK_EMP
    EMP --> CHECK_150
    TITLE --> CHECK_TITLE

    CHECK_EMP -->|Yes| PEN_EMP
    CHECK_EMP -->|No| PENALTIES_ARR
    PEN_EMP --> PENALTIES_ARR

    CHECK_TITLE -->|Yes| PEN_TITLE
    CHECK_TITLE -->|No| PENALTIES_ARR
    PEN_TITLE --> PENALTIES_ARR

    CHECK_PE -->|Yes| DISQ
    CHECK_150 -->|Yes| DISQ
    CHECK_FUND -->|Yes| DISQ
    CHECK_PUBLIC -->|Yes| DISQ
    CHECK_SECTOR -->|Yes| DISQ
    DISQ --> DISQ_ARR
