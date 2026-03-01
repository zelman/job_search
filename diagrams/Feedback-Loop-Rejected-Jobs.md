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
