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
