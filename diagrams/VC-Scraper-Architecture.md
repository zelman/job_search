flowchart TB
    subgraph Scrapers["VC Portfolio Scrapers"]
        HC[Healthcare v25<br/>WhatIf, Leadout, Flare,<br/>7wire, Oak HC/FT,<br/>Cade, Hustle Fund]
        CT[Climate Tech v23<br/>Khosla, Congruent,<br/>Prelude, Lowercarbon]
        SJ[Social Justice v25<br/>Kapor, Backstage,<br/>Harlem, Collab]
        ENT[Enterprise v26<br/>Unusual, First Round,<br/>Essence, K9, Precursor,<br/>M25, GoAhead]
        MICRO[Micro-VC v14<br/>Pear, Floodgate, Afore,<br/>Unshackled, 2048,<br/>Y Combinator]
    end

    subgraph Methods["Scraping Methods"]
        SITEMAP[Sitemap XML]
        BROWSER[Browserless<br/>Headless]
        STATIC[Static Lists]
        INFINITE[Infinite Scroll<br/>2048, YC /function]
    end

    subgraph Pipeline["Shared Subworkflow"]
        ENRICH[Enrich & Evaluate<br/>Pipeline v4]
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
