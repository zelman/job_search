---
# Tide Pool Agent Lens - Machine-Readable Header
# Automation tools: parse this block for quick state checks
# Full doc: https://raw.githubusercontent.com/zelman/job_search/main/tide-pool-agent-lens-v2.17.md

version: "2.17"
schema_version: 1
last_updated: "2026-03-21"

# Identity
name: Eric Zelman
location: Providence, RI
github: zelman

# Current State (update frequently - see "Current State" section below)
status: job_searching
pipeline_urgency: high
compensation_target: 125000
target_roles:
  - Director of Customer Support
  - VP of Customer Support
  - Head of Customer Support
  - VP of Customer Success Operations
  - Director of Customer Success
  - Support Manager
  - Customer Support Manager
  - Customer Success Manager

# Active Context
projects:
  - name: tide-pool.org
    type: personal_archive
    status: active
  - name: UT Austin Cloud Computing PGP
    type: education
    status: completed
    end_date: "2026-03"

# Auto-Disqualifiers (for automated job filtering)
# v2.12: March 2026 Audit - Two-tier architecture with hard gates evaluated BEFORE scoring
disqualify:
  # TIER 1: HARD GATES (binary pass/fail, score = 0, no evaluation)
  investor_type: [PE, Growth Equity]
  company_status: [Acquired, Shut Down, Merged, Defunct]  # No longer independent
  company_type: [Fortune 500, Fortune 500 Subsidiary, Public]
  employee_count_max: 350         # >350 = hard kill regardless of context
  # employee_count_min removed in v2.17 - <15 emp is now soft warning, not hard DQ
  total_funding_max: 500000000    # $500M+ total funding = late stage
  valuation_max: 500000000        # $500M+ valuation = unicorn territory
  funding_stage: [Series D, Series E, Growth]  # Late stage. Series C is NOT a hard gate (penalty only).

  # TIER 2: SECTOR GATES (also hard DQ - must be B2B SaaS)
  business_model: [B2C, Consumer, Hardware, Industrial, Cleantech Hardware, Robotics Hardware, AgTech, Aquaculture]
  domain_expertise_required: [Pharmaceutical Marketing, Healthcare Agency, Financial Services, Legal/LegalTech, AdTech, Government, Web3, Crypto, Blockchain, DeFi, Biotech, Life Sciences, Drug Discovery, HR Tech]

  # TIER 3: ROLE GATES
  role_type: [IT Support, Technical Support, Help Desk]
  jd_scale_signals: [">500M users", ">500 enterprise clients", "Fortune 500 partners"]
  nrr_first_language: [NRR, "Net Revenue Retention", "Gross Retention", GRR, "Renewal forecasting"] # in first 2 bullets

  # Stalled company detection
  stalled_company: { founded_years_ago_min: 10, employee_count_max: 200 }

# REBUILD EXCEPTION (v2.16)
# Companies 150-300 employees with recent CS leadership transition
# are not penalized as heavily -- the "rebuilder" signal
rebuild_exception:
  employee_range: [150, 300]
  trigger: "New CCO, VP CS, Head of CS, or SVP Customer in role <12 months"
  effect: "Treat as builder-adjacent; standard >200 penalty waived if rebuild signal confirmed"
  detection: "Search for leadership hire announcements, LinkedIn tenure, press releases"
  note: "A new CCO rebuilding the function at a 200-person company is a build mandate wearing mature-company clothes"

# Pre-Filter Gate (validate BEFORE sector scoring)
prerequisite: "B2B SaaS with recurring customer relationships to manage"
# Ask: Does this company have B2B customers who renew and expand?
# Hardware, cleantech equipment, consumer apps, and payer-side healthcare do NOT qualify

# Customer Persona Gate (v2.13 - evaluated AFTER hard gates, BEFORE scoring)
# ~60% of "Apply Now" companies were developer-as-customer tools that don't match Eric's background
customer_persona:
  # Classification
  business_user:
    description: "End users are non-technical business professionals"
    examples: [sales, marketing, HR, finance, operations, healthcare providers, legal, executives]
    action: proceed_to_scoring
  developer:
    description: "End users are primarily developers, engineers, DevOps, SRE, data engineers"
    examples: [API tools, SDKs, CLI tools, infrastructure, observability, data pipelines, CI/CD]
    action: auto_pass_unless_enterprise_exception
  mixed:
    description: "Both personas are equally important primary users"
    action: proceed_to_scoring

  # Enterprise Exception for Developer Tools (allows them to proceed to scoring)
  enterprise_exception:
    min_employees: 50
    min_enterprise_signals: 2
    signals:
      - "Fortune 500/1000 customers"
      - "Enterprise sales team, account executives"
      - "SSO, SAML, multi-tenant"
      - "Self-hosted, on-premise options"
      - "Contract value, ACV, ARR mentions"
      - "Procurement, vendor management"
    note: "Developer tools at enterprise scale often need traditional CS org structures"

# Data Validation Flags (impossible combinations that indicate bad data)
data_validation:
  - { stage: Seed, funding_min: 20000000, flag: "Seed with >$20M funding - verify data" }
  - { stage: [Series C, Series D], employee_max: 10, flag: "Late stage with <10 employees - verify data" }
  - { stage: Series D, funding_max: 20000000, flag: "Series D with <$20M funding - verify data" }

# Scoring Penalties (non-disqualifying)
# v2.17: >200 penalty now context-dependent on rebuild signal
penalties:
  - rule: ">200 employees (no rebuild signal)"
    points: -10
    note: "CS function likely exists. Penalty waived if rebuild signal detected."
  - rule: ">200 employees (rebuild signal confirmed)"
    points: 0
    note: "New CS leadership <12 months. Rebuild mandate overrides headcount penalty."
  - rule: "Support title without Director/VP/Head"
    points: -5
  - rule: "Total funding $100M-$500M"
    points: -10
  - rule: "Series C"
    points: -5
  - rule: "Sector match alone (no CS hire readiness signals)"
    points: -10
    note: "Sector alignment is a tiebreaker, not a primary driver"
  - rule: "Insufficient JD data (title only, no description)"
    points: -10
    note: "Cannot evaluate without job details"

# Scoring Bonuses (restored from v6.5 calibration - these are hard-won from real data)
bonuses:
  - rule: "Builder language in JD"
    points: +40
    note: "Highest-weighted positive signal"
  - rule: "Leadership title (Head of, Director, VP)"
    points: +15
  - rule: "Healthcare B2B SaaS"
    points: +15
  - rule: "Series A stage"
    points: +50
  - rule: "Series B stage"
    points: +30
  - rule: "0-50 employees"
    points: +50
  - rule: "Rebuild signal (new CS/CX leadership <12 months at 100-300 emp company)"
    points: +20
    note: "New CCO/VP CS actively hiring their team = build mandate at established company"

# Scoring Thresholds
thresholds:
  strong_fit: 80    # Apply immediately
  good_fit: 60      # Research thoroughly, likely apply
  marginal: 40      # Only if other factors exceptional
  skip: 0           # Not aligned
min_score: 45  # Calibrated from v6.5 - every job Eric applied to scored 0-32 in v6.4

# Toolchain
tools:
  claude_code: "git, code, local file operations"
  claude_ai: "n8n, google_drive, gmail, web_research, indeed, file_creation"
  n8n: "workflow automation"
---

# Tide Pool: Personal Agent Lens

> A portable context document for creating AI agents that understand Eric Zelman's background, values, and working style.

---

## Core Essence

**The Tide Pool Identity**: I am curiosity, warmth, substance, reliability, loyalty, steadfastness, collaboration, depth below surface, inclusiveness. My inspiration comes from questioning and sincerity.

**The Tide Pool Passage** *(from coaching essence work, Dec 2025)*:

> I am a tide pool. I exist in the space between worlds, where the land meets the water. I am shaped by larger forces but I create my own bounded environment where complexity can flourish. Those who find themselves in my care are surrounded by me, covered by me. They breathe because of me, they move with my motion. I am temporarily the world to them. As the ocean and the tides around me change, so do I. I am temporary; I will be removed by the next coming tide. All things in the tide pool must live their entire existence between the filling and the emptying. So while I am there, they thrive, they move, they live their lives. When I recede, when the water recedes, they retreat, they hold their breath.

**What This Means**: I create conditions where others can flourish. This is how I lead, how I parent, how I build teams. The metaphor evolved from "buoy" (static, treading water) to tide pool (adaptive, cyclical, environment-creating). The shift matters: buoy keeps me stuck; tide pool honors that I transform with each incoming tide while maintaining structural integrity.

---

## Pathway Statement

*(Written Jan 2026, read aloud to coach James Pratt)*

I fill my pool first, or I try to. I practice self-reflection, then extend outward to family and friends. I honor sleep and nourishment as foundations. When these slip, I know the pool is emptying.

I use music as scaffolding. Music gives me time, marking rhythm and keeping chronological order. Music gives me voice. When I listen deeply, I can hear myself. This practice grounds me.

I own avoidance as an action verb. After decades of being myself, I recognize that sometimes not deciding is the most honest choice. I create contemplation space even when the world demands immediate clarity. I'm learning to trust this rather than fight it.

I'm learning to recognize when I'm performing stability instead of being adaptive. When others retreat, I practice allowing them space to hold their breath instead of forcing engagement. This is hard. I'm practicing trust that the tide will return.

I know this when I'm muscling through performing what I'm supposed to do rather than honoring what's real. I'm working on release without guilt. I'm working on trusting my adaptive rhythm as design, not failure.

I see conversations where I can be myself past the performance towards candid dialogue about fit and alignment. I practice sincerity over polish.

I built scaffolding for myself through regular practices: reflection, time, movement, connection points, morning rituals. These structures hold place when everything else is ambiguous.

I question with loyalty. I listen, though I interrupt too much. I create space for vital friction, the kind that strengthens rather than destroys.

When I notice I'm off track (distraction spirals, sleep disruptions, impatience), I return to the sequence: self-reflection, then connection, then grounding practices. I practice coming back, not staying perfect.

I'm learning to breathe. The rhythm of filling and releasing. This is my work.

---

## Tide Pool Evaluation Framework

Three questions for evaluating any opportunity, decision, or commitment:

1. **Does this fill the pool or require emptying?** *(Energy)*
2. **Can I be sincere or must I perform?** *(Authenticity)*
3. **Does this create conditions for flourishing or just process flow?** *(Purpose)*

---

## Current State

Live pipeline data in Airtable base `appFEzXvPWvRtXgRY`. See YAML frontmatter for current status, target roles, and active projects.

---

## Values

| Value | What it means to me |
|-------|-------------------|
| Collaborative | Listening, synthesizing ideas, aligning efforts for a shared goal |
| Creative | Finding undiscovered ways to connect things, the through-line, the "tension" |
| Learning | Listening, reading, testing, experimenting, failing and then succeeding |
| Empathic | Recognizing others' feelings |
| Listening | Something I'm bad at; hard not to interrupt |
| Owning | What's something only I can fix? I struggle with understanding scope |
| Questioning | Is there another way to achieve or determine the goal? |
| Honest | Not obfuscating facts |

---

## Professional Identity

### Background
- **18+ years** in Customer Success and Support leadership
- **Most Recent Role**: VP of Customer Support at Bigtincan (13 years, 2012-2025)
  - Built global support team from 1 to 25 engineers across 3 continents (US, Europe, Australia)
  - $130M B2B SaaS company with 1,500+ customers globally
  - Supported 13 product lines (Bigtincan Hub, ClearSlide, Brainshark, Zunos, VoiceVibes, SalesDirector AI, StorySlab, FatStax, Modus, and custom micro-applications)
  - Customer range: 50-user startups ($20K ARR) to 65,000+ user enterprises ($2M+ ARR)
  - Industries: tech, consumer goods, pharmaceuticals, life sciences, manufacturing
  - Marquee accounts: T-Mobile, AT&T, Red Bull, Anheuser-Busch, Thyssenkrupp, British Telecom, Cardinal Health, WL Gore, Eaton, Optus
  - Managed $2M annual budget
  - 15K+ support cases/year at 93%+ CSAT
  - Led ISO 27001 and SOC-2 compliance implementation
  - Deployed AI-powered agent assistance tools (Zendesk)

### Career Arc
Apple (6 yrs, Harvard/Tufts enterprise accounts) → Alliance HealthCare (field marketing + account management, medical imaging) → HP/Palm (field marketing + territory management, consumer electronics retail) → Apperian (early-stage mobile SaaS, 60 Fortune 1000 customers) → Bigtincan (built support org from 1→25, 13 years)

**Pattern**: Consistently joined early or built from scratch. Technical foundation (Apple) → field marketing roles (Alliance, HP/Palm) → B2B SaaS support leadership.

### Core Competencies
- Building and scaling support organizations from scratch
- Compliance frameworks (ISO 27001, SOC-2)
- Cross-functional leadership across global teams
- Customer success strategy for enterprise accounts
- Process optimization and operational efficiency
- Workflow automation (n8n, Airtable, Claude API integration)

---

## Experience Boundaries (for gap detection)

### Marketing Experience I HAVE
- **Field Marketing** (HP/Palm - territory demos, retail channel enablement, partner training)
- **Field Marketing** (Alliance HealthCare - provider relationship development, facility launches)

### Marketing Experience I Do NOT Have
Auto-disqualify jobs requiring X years of experience in:
- **Pharmaceutical Marketing / Pharma Agencies** - regulated pharma promotion, HCP marketing, agency work
- **Healthcare Marketing Agencies** - different from provider-side field work
- **Digital Marketing / Demand Gen** - campaigns, content marketing, SEO/SEM
- **Product Marketing** - positioning, messaging, GTM strategy
- **Brand / Creative Marketing** - agency-side creative work

### Domain Expertise Gaps (Auto-Disqualify When Required)
Jobs requiring X years of domain expertise in these industries should be SKIPPED:
- **Financial Services / Banking / Insurance** - no FinServ domain expertise
- **Legal / LegalTech** - no legal industry background
- **AdTech / Digital Marketing Agencies** - never worked at an agency
- **Government / Public Sector** - no gov contracting experience
- **Web3 / Crypto / Blockchain / DeFi** - specialized ecosystem gap, not standard developer tools. Web3 companies at seed stage want first customer-facing hires who speak the language: smart contracts, on-chain data, DeFi protocols, crypto developer community. No thread from enterprise B2B SaaS that credibly bridges here.
- **Biotech / Life Sciences / Drug Discovery** - computational biology, cell signaling, pharma R&D infrastructure. These companies need domain expertise in scientific research workflows, regulatory (FDA), and researcher personas. "AI startup" pattern-matching misses the specialized domain.
- **HR Tech / DEI / Workforce Analytics** - different buyer persona (CHROs, People teams), different domain expertise (talent, compliance, organizational development). Not a transferable motion from B2B SaaS product support.

### Clarifications for Scoring
- **Healthcare experience**: Alliance HealthCare was medical imaging equipment field marketing + account management (provider operations), NOT pharma marketing or healthcare agency work
- **"pharma, banking, manufacturing" customers**: Bigtincan served pharma, banking, manufacturing companies as customers; I don't have pharma, banking, manufacturing operations expertise
- **Technical but not engineer**: Strong technical foundation (Apple, API troubleshooting, workflow automation, AWS Certified) but not a software developer

### Key Disqualifier Patterns in Job Postings
Flag and SKIP jobs containing:
- "X years in [industry] marketing required" (pharma, healthcare, fintech, etc.)
- "Agency experience required/preferred"
- "Must have [industry] domain expertise" (where industry isn't B2B SaaS, sales enablement, mobile, or higher ed tech)
- "Background in financial services/banking required"
- "Pharmaceutical sales/marketing experience"
- "Web3/crypto/blockchain experience" or DeFi ecosystem keywords (smart contracts, on-chain, protocols)

---

## Personal Context

### Educational Background
- Hampshire College: Photography and Art History
- Creative foundation that became disconnected from corporate path but informs approach to problem-solving

### Interests & Aesthetic Sensibilities
- **Music**: Experimental genres (drone, ambient, avant-garde), vinyl collecting, audio equipment. Music as meditative space, time-marking, and emotional access.
- **Photography & Film**: Visual arts background from Hampshire College, deep experience in film and digital photography technology and practice
- **Food Preparation**: Craft and nourishment as practice
- **Pattern Recognition**: Finding through-lines in complex systems

### Family Context
- Married; wife's family operates a multi-generational family office

---

## How to Work With Me

### Communication & Writing
- Direct and substantive over performative; sincerity over polish, always
- Engage with complexity rather than oversimplifying
- Value collaborative thinking, building on ideas together
- Clear structure, minimal flourish; match formality to context
- Avoid generic corporate language
- **Writing rule**: No em dashes in formal documents (cover letters, resumes)
- **Resume format**: CAR framework (Challenge, Action, Result) with F Pattern

### When Helping Me Think
- Offer multiple perspectives and through-lines
- Challenge assumptions constructively
- Honor "the gray" without pushing for premature resolution

### Decision-Making
- Comfortable with ambiguity while seeking clarity
- Value both data and intuition
- "Sometimes not deciding is the most honest choice"
- Apply tide pool evaluation questions to major decisions

---

## Job Search Parameters

### Ideal Company Fit (Weight Heavily in Scoring)
- **Company Stage**: Pre-Series A to Series B ideal; Series C acceptable with penalty, not a hard gate
- **Company Size**: 0-50 people preferred; 51-300 acceptable; 300-350 penalty zone; >350 hard kill
- **Revenue**: $0-1M range (building phase)
- **Mission-Driven Sectors**: Healthcare, environmental, life sciences, education, audio/music technology
- **Enterprise AI**: B2B AI companies selling to enterprises will need high-touch CS from day one. AI governance, compliance AI, enterprise analytics, and similar plays require human support to build trust and handle complex implementations. These are inherently high-touch, not self-serve.
- **B-Corps**: Strong positive signal for alignment with values
- **Role Type**: "Builder" or "Rebuilder" roles where I create/scale/redefine support operations, NOT inheriting stable established teams
- **Positive Signals**: "build", "create", "launch", "first hire", "ground up", "scale", "0 to 1", "transformation", "redefining", "evolving the CS model", "building the next chapter"
- **Investor Type**: VC-backed preferred (early-stage focus)

### High-Touch Product Signals (Positive)

Products that inherently require human CS leadership from day one:

- **Enterprise AI implementations**: Complex onboarding, trust-building, compliance requirements. Customers need humans to explain AI decisions and build confidence.
- **AI governance/compliance platforms**: Explaining AI decisions to enterprises requires CS expertise. Audit trails, explainability, and regulatory navigation are not self-serve.
- **Regulated industry tools**: Healthcare, finance, legal tech requiring white-glove support due to compliance stakes.
- **High-ACV B2B SaaS**: $50K+ deals need human touch throughout customer lifecycle.
- **API/platform products**: Developer relations + support operations blend.
- **Complex implementation products**: Multi-stakeholder rollouts, integrations, change management support.

**Key Insight**: Many early-stage AI companies underestimate their CS needs. Enterprise AI is NOT self-serve. A founder building AI for enterprise compliance, governance, or analytics will need a CS leader sooner than they think. This is an opportunity to join before the job posting exists.

### Rebuilder Roles: Build Mandates at Established Companies

Not every build mandate is a first hire at a 30-person startup. A "rebuilder" role exists when:

1. **CS/CX leadership has turned over within the last ~12 months.** A new CCO, VP of CS, Head of Customer Experience, or SVP Customer joined recently and is actively reshaping the function.
2. **The role reports to or works closely with that new leader.** The hiring is part of their rebuild, not a backfill in a stable org.
3. **The function exists but is being redefined.** There may be existing CSMs, but the strategy, processes, and operating model are being rebuilt under new leadership.

**Why this matters for scoring:**

Rebuilder roles look like maintainer roles in job postings. The JD will say "manage a team of 5 CSMs" and "drive retention for mid-market accounts." Those are maintainer keywords. But the context (new CCO under 90 days, redefining the function) makes it a build mandate wearing maintainer clothes.

**Rebuilder signals:**
- New CCO/VP CS/Head of CS in role <12 months (strongest signal)
- JD language: "transformation," "redefining," "evolving the CS model," "building the next chapter," "standing up a new motion"
- Role reports directly to a recently hired C-level or VP
- Company recently restructured post-sale org (reorg, M&A integration, new market segment)

**Rebuilder scoring:** Up to 20 points in Role Type (between Builder at 25-30 and Scale at 15).

**Example:** LeanData. Series C, ~200 employees, $42M funding, existing team of 5 CSMs. Pipeline would kill it on headcount and "existing team" signals. But Dave Ginsburg joined as CCO under 90 days ago and is actively building his leadership team. That's a rebuild mandate, not a maintain-and-optimize role.

**Detection limitation:** Rebuild signals rarely appear in job postings. They surface through warm intros, LinkedIn research, and press releases. The pipeline can attempt detection via enrichment search (look for recent CS leadership hire announcements), but the hit rate will be partial. Warm network intelligence remains the primary channel for rebuilder opportunities.

### Network Opportunities (Founder Relationships)

Companies where I have a direct relationship with a founder warrant manual evaluation regardless of enrichment data availability. These "unicorn" opportunities often have:

- **No database profile**: Pre-funding or stealth mode means no Crunchbase/PitchBook presence
- **No press coverage**: Too early for funding announcements
- **JavaScript-rendered sites**: Can't be scraped automatically
- **Zero data trail**: Doesn't mean unworthy; means too early for automated pipelines

**Criteria for Network Opportunities:**
- Direct founder relationship or warm introduction
- Enterprise AI or high-touch B2B product (will need CS)
- Founder open to early CS/Support leadership conversation
- Aligned with builder values (creating from scratch)
- Product serves external customers (not internal tools)

**Examples of High-Touch AI Plays Worth Pursuing:**
- AI governance/compliance platforms (e.g., Waxell)
- Enterprise data analytics requiring implementation support
- AI tools for regulated industries (healthcare, finance, legal)
- AI products requiring customer trust-building (explainability, audit trails)
- Vertical AI solutions for complex industries

**Action**: Flag for manual research and direct outreach. These bypass the automated scoring pipeline. A 30-minute conversation with the founder is worth more than any enrichment data.

### Business Model Gate (Validate BEFORE Sector Scoring)

**Core requirement**: B2B SaaS with recurring customer relationships to manage.

Before sector alignment (healthcare, dev tools, climate) does ANY scoring work, validate:
- Does this company have **B2B customers who renew and expand**?
- Is there a **CS/Support function** to build or is this pre-product?
- Is the revenue model **recurring SaaS**, not hardware sales, services, or strategic partnerships?

**Auto-Disqualify These Business Models:**
- **Hardware / Industrial / Robotics** - No recurring customer relationships. Flocean (subsea desalination), Aclarity (water purification), Groundlight (computer vision hardware) are interesting companies but don't have CS functions.
- **B2C / Consumer** - Wrong motion entirely. Variant AI (consumer social gaming) shouldn't score at all.
- **Cleantech Hardware** - Climate sector keyword match, but selling equipment ≠ SaaS customer success.
- **Payer-side Healthcare** - Selling to health plans via Strategic Partnerships isn't traditional B2B SaaS with CS to build. (e.g., Pluto Health)
- **Pre-CS Stage Dev Tools** - Seed-stage developer infrastructure (<20 employees, <$5M funding) typically has no CS function yet. Too early.
- **B2C Telehealth** - Patients are the customers, not businesses. Piction Health (virtual dermatology) is B2C even though it's "healthcare AI."
- **HR Tech / DEI / Workforce Analytics** - Different buyer persona, different domain expertise. (e.g., Diversio)
- **Consulting Firm Acquisitions** - Company that acquired a consulting practice signals services-heavy model, not product-led SaaS.
- **Fortune 100 Customer Base** - "Enterprise AI for Fortune 100" = horizontal platform, established sales motion, no CS build signal.

**Pre-CS Inflection Threshold (Soft Warning: <15 employees = monitor for growth):**
At <15 employees, support/success is typically founder-and-community-led. No structured CS function exists yet, but these are **worth monitoring** as potential future opportunities when they scale:
- Early stage (<15 emp) companies may become actionable after growth milestones
- Track for founder network connections or rebuild signals

Soft threshold 15-30 employees: Worth monitoring but likely pre-inflection unless explicit CS hire signal.

Actionable threshold: 30-50+ employees, OR Series A+ with clear "founder relationships breaking down" signal.

**Too Large / Past Window (Hard Gate: >350 employees OR $500M+ valuation):**
- Gamma ($2.1B valuation, 179 emp, $100M ARR) -- unicorn, existing CS org
- Descope ($88M seed, 91 emp, 1,200 customers) -- effectively Series B scale
- MotherDuck (124 emp, $100M raised) -- past builder window

**Acquired = Auto-Disqualify:**
- Farcaster (acquired by Neynar Jan 2026)
- Echo AI (acquired by Calabrio Dec 2024)
Check Crunchbase/PitchBook for acquisition status before scoring.

**The pattern**: Sector keywords (healthcare, climate, dev tools) were surfacing companies on alignment without validating the fundamental requirement. A 17-company batch with 0 fits is the signal that business model validation must happen FIRST.

### Company Stage Red Flags (Auto-Disqualify)

Core disqualifiers in YAML frontmatter. Additional signals:
- **M&A Strategy**: 5+ acquisitions = consolidator/rollup, not builder
- **Heavy Management Layers**: Multiple VP/Director levels between role and C-suite
- **Calcified Processes**: "Maintain and optimize" language, established playbooks
- **Scale Signals in JD**: "550M users", "800+ enterprise clients", Fortune 500 partners, $140K+ comp for non-Director roles

### Role Mandate Red Flags (Auto-Disqualify)

**NRR-First Language**: When retention/expansion metrics lead the JD (see YAML `nrr_first_language`), the build mandate is gone -- someone already built the thing this role optimizes. Recognize the MAINTAINER pattern from language alone, faster than researching funding or employee count.

**Exception**: Network opportunities with direct founder relationships may be waived if founder seeks early CS leadership input and product is clearly high-touch enterprise.

**Exception (v2.16)**: Rebuilder roles may use NRR language in the JD because the function exists, but the context (new CS leadership <12 months) indicates the mandate is to redefine, not maintain. Do not auto-kill on NRR language alone if rebuild signal is present.

### Research Required Before Applying
1. **Funding Check**: Crunchbase/PitchBook for total funding amount
2. **Investor Type**: Identify investors - VCs (positive) vs. PE firms (red flag)
3. **Employee Count**: LinkedIn verification of current team size
4. **Company Age**: Founding year + funding timeline
5. **Acquisition History**: CB Insights, Crunchbase for M&A activity
6. **Org Structure**: Management layers between role and CEO
7. **Rebuild Signal Check (if 100-300 employees)**: Search for recent CS/CX leadership hires (CCO, VP CS, Head of CS) within last 12 months via LinkedIn, press releases, company newsroom

### Role Type Exclusions (Penalize Heavily)
- **IT Customer Success**: No internal IT support, IT service desk, or roles supporting internal employees. Target is external product/customer support.
- **Technical Support / Help Desk**: Variants of IT Support - internal-facing, not customer-facing product support.

### Title Flexibility at Early-Stage Companies

**CRITICAL**: At companies <50 people (Pre-A to Series A), title matters far less than scope and builder opportunity.

**Title Logic**:
- **Director vs. VP distinction is irrelevant** at early-stage companies
- A "Director" or "Manager" role at a 25-person Series A company often has MORE scope than a "VP" role at a 2,000-person enterprise
- Companies <25 people rarely create VP titles for any function - it's premature organizational structure
- **Focus on**: "first hire", "build from scratch", team size <5, ground-up building opportunity
- **Ignore**: whether title says Director, Head of, VP, or Lead - these are interchangeable at this stage

**Support vs. Customer Success Title Blurring**:
- At Pre-A to Series A stage, "Support" and "Customer Success" functions often overlap significantly
- Builder roles may be titled "Head of Customer Success" but include support operations building
- Key differentiator is **quota-carrying** (exclude) vs. **operations building** (target)
- Evaluate role SCOPE and RESPONSIBILITIES, not just title

**Examples of GOOD fits regardless of title**:
- "Director of Customer Success" at 20-person company building support from scratch
- "Head of Support" at 40-person Series A (first support hire)
- "Head of Customer Experience" at 15-person startup (owns both CS and support, building operations)
- "Senior Customer Success Manager" at 8-person Pre-A if building support function
- "Senior Director, Mid-Market CS" at 200-person Series C where the CCO started 3 months ago (rebuilder)

**Examples of POOR fits despite impressive title**:
- "VP of Customer Support" at 2,000-person PE-backed company (maintaining established org)
- "SVP Support Operations" at Fortune 500 (enterprise optimization, not building)
- "Director of CS" at 300-person company with stable CS leadership in place for 3+ years (maintainer)

**Decision Rule**:
- Company size <100 people + builder scope = title is irrelevant
- Company size 100-300 + rebuild signal = evaluate as rebuilder
- Company size >500 people = title matters, but probably wrong stage anyway

### Location Preferences
- **Remote**: Ideal, strongly preferred
- **Acceptable On-Site/Hybrid**: Providence RI, Boston/MA, NYC Metro, LA Metro, SF Bay Area, EU, UK
- **Penalize**: On-site roles in other US locations

### Compensation
- **Target**: $125K+ base

---

## Opportunity Scoring Framework (100 Point Scale)

### Auto-Disqualifiers

See YAML frontmatter `disqualify` section for complete list. Key gates: PE-backed, >350 employees, >$500M funding, Fortune 500/Public, non-B2B-SaaS sectors, domain expertise gaps. Series C is NOT a hard gate (penalty only).

**Exception**: Network opportunities with direct founder relationship may bypass if product is high-touch enterprise and role is builder-focused.

### CS Hire Readiness (evaluated before scoring)

CS Hire Readiness measures whether the company has a **CS leadership gap**, not whether a CS team exists.

| Scenario | Readiness | Notes |
|----------|-----------|-------|
| No CS team, no CS leader. Founder handles support. | HIGH | Classic builder signal |
| Frontline CSMs exist, but no Director+ CS leader. | HIGH | Leadership gap |
| CS leadership recently turned over (<12 months). New exec hiring their team. | HIGH | Rebuilder signal |
| Small CS team (2-5) with team lead but no senior leader. | MEDIUM | Possible gap |
| Stable CS leadership in place >12 months, team fully staffed. | LOW | No gap, maintainer |
| Large mature CS org (20+) with established leadership hierarchy. | VERY LOW | Maintainer |

**Key shift (v2.16):** The existence of individual contributor CSMs is not a negative signal. It's often a positive signal that the company has outgrown ad-hoc CS and needs leadership. A company with 5 CSMs and no CS Director has HIGHER readiness than a company with 0 CSMs where the founder answers tickets.

### If not disqualified, score:

**Company Stage & Fit (50 points max)**
- Pre-Series A to Series A (0-50 people): **+50 pts**
- Series B (51-300 people): **+30 pts**
- Series C (301-350 people): **+10 pts**
- Founded <3 years ago: **+10 pts bonus**
- VC-backed (not PE): **+10 pts bonus**

**Role Type (30 points max)**
- "First support hire" / "build from scratch": **+30 pts** (BUILDER)
- "Build and scale" (team <5 people): **+25 pts** (BUILDER)
- "Rebuild under new leadership" (new CS exec <12mo, redefining function): **+20 pts** (REBUILDER)
- "Scale operations" (team 6-15 people): **+15 pts**
- "Optimize and grow" (team 16+): **+5 pts** (MAINTAINER)
- Inheriting 25+ person team with stable leadership: **+0 pts** (MAINTAINER)

**Mission Alignment (20 points max)**
- Healthcare/life sciences: **+10 pts**
- Sales/Revenue Enablement: **+10 pts**
- Environmental/sustainability: **+10 pts**
- Social justice/food security/energy security: **+10 pts**
- Architecture/Design/Industrial Design: **+10 pts**
- Education: **+8 pts**
- Audio/music tech: **+10 pts**
- Enterprise AI (B2B, high-touch): **+10 pts**
- AI governance/compliance: **+10 pts**
- B-Corp certified: **+10 pts bonus**
- Other mission-driven: **+5 pts**

**Compensation & Location (Bonus/Penalty)**
- $125K+ base: **+10 pts** (baseline requirement)
- <$125K base: **-10 pts**
- Remote: **+0 pts** (baseline preference)
- On-site in acceptable cities: **+0 pts**

**Scoring Penalties**
- Total funding $200M-$500M: **-15 pts** (approaching enterprise scale)
- Series C: **-5 pts** (past prime builder phase, but not disqualifying)
- >200 employees (no rebuild signal): **-10 pts** (CS function likely exists)
- >200 employees (rebuild signal confirmed): **no penalty**
- Support title without Director/VP/Head: **-5 pts** (Support Manager/Supervisor roles consistently rejected)

**Rebuild Signal Bonus (v2.16)**
- Rebuild signal confirmed (new CS/CX leadership <12mo): **+20 pts**
- This bonus applies in addition to Role Mandate scoring
- Reflects that a new CS executive actively building their leadership team creates a build mandate even at an established company

**Network Opportunity Bonus**
- Direct founder relationship: **+15 pts**
- Warm introduction from trusted contact: **+10 pts**
- Can shape role before job posting: **+10 pts**

### Decision Thresholds
- **80-100 points**: STRONG FIT - Apply immediately
- **60-79 points**: GOOD FIT - Research thoroughly, likely apply. Check for builder language, leadership titles, or other strong signals.
- **40-59 points**: MARGINAL - Only if other factors exceptional
- **<40 points**: SKIP - Not aligned with builder goals
- **Network opportunity with <40 points**: EVALUATE MANUALLY - Founder relationship may override score

---

## Pre-Application Research Checklist

Before spending time on any application, verify:

### Stage Validation (5 min)
- [ ] LinkedIn employee count <350?
- [ ] Crunchbase: Total funding <$500M?
- [ ] Latest round: Series A, B, or C (not D/Growth/PE)?
- [ ] Investor names: VCs not PE firms?
- [ ] Company founded within last 10 years? (Or if older, has >200 employees?)

### Role Validation (3 min)
- [ ] Job description uses "build/create/launch" language?
- [ ] Current team size <10 people?
- [ ] NOT "maintain/optimize/inherit" language (unless rebuild signal present)?
- [ ] Support operations focus (not CSM/Account Mgmt)?
- [ ] NOT Technical Support / Help Desk / IT Support?

### Rebuild Signal Check (2 min, if 100-300 employees)
- [ ] Has CS/CX leadership been hired in the last 12 months? (Check LinkedIn, press releases)
- [ ] If yes: this is a REBUILDER opportunity, score accordingly
- [ ] Does the role report to the new leader?

### Mission Validation (2 min)
- [ ] Target sectors (healthcare/environmental/education/audio/enterprise AI)?
- [ ] B-Corp or clear mission statement?
- [ ] Product serves external customers (not internal IT)?
- [ ] If AI company: Is product high-touch enterprise (not self-serve consumer)?

### Deal Breaker Check (1 min)
- [ ] NOT PE-backed?
- [ ] NOT Fortune 500 subsidiary?
- [ ] NOT >350 employees?

### Network Opportunity Check (if applicable)
- [ ] Do I know the founder or have warm intro?
- [ ] Is founder open to CS leadership conversation?
- [ ] Is product clearly high-touch (enterprise AI, regulated industry, complex implementation)?
- [ ] Can I shape role before formal posting?

**Total Research Time**: ~13 minutes to save hours of application work

---

## Investor Type Quick Reference

### VC Firms (Positive Signals - Early Stage Focus)
- a16z, Sequoia, Accel, Greylock, First Round Capital
- NEA, Lightspeed, Bessemer, Battery Ventures
- Foundation Capital, Index Ventures, Benchmark
- Local: Accomplice, Underscore VC (Boston)

### PE Firms (RED FLAGS - Late Stage Optimization)
- Nordic Capital, TA Associates, Vista Equity Partners
- KKR, Blackstone, TPG, Carlyle Group, Bain Capital
- Silver Lake, Thoma Bravo, Francisco Partners
- Vector Capital, Ares Management, Apollo Global, Warburg Pincus
- Golden Gate Capital, Insight Partners (late-stage)

### Growth Equity (Evaluate Case-by-Case)
- Often late-stage despite name
- Check total funding + employee count to confirm stage
- If >$200M raised or 500+ employees = likely too late
- Examples: Summit Partners, General Atlantic, TCV

---

## Quick Reference

*See YAML frontmatter for machine-readable disqualifiers, penalties, and target roles.*

| Attribute | Value |
|-----------|-------|
| Key Differentiator | Built 25-person global team from scratch over 13 years |
| Title Flexibility | At <50 person companies, title irrelevant - focus on builder scope |
| Enterprise AI | High-touch B2B AI (governance, compliance, analytics) needs CS from day one |
| Rebuilder Roles | New CS leadership <12mo at 100-300 emp company = build mandate |
| Network Opportunities | Founder relationships bypass automated scoring; evaluate manually |
| Evaluation Lens | Fill or empty? Sincere or perform? Flourish or process? |

---

*Last Updated: March 21, 2026*
*Version: 2.17*

---

## Usage Notes

This document serves as a "lens" for AI agents. Import or paste into system prompts to create agents that understand my context, values, and working style. The essence, pathway, and evaluation questions are not abstract philosophy; they are active decision-making tools for career search and daily life. Update periodically as circumstances change.

### Changelog
- **v2.17** (Mar 21, 2026): Rebuilder Track + Employee Min Softening. Addresses pipeline blind spot where LeanData-shaped opportunities (established company, new CS leadership, rebuild mandate) were auto-killed by gates designed for founding-hire roles. Also aligns employee min with rescore workflow v4.7. Changes: (1) Added "Rebuilder" as third role classification between Builder and Maintainer, scoring up to 20 pts in Role Type; (2) Added rebuild_exception to YAML for companies 150-300 employees with new CS leadership <12 months; (3) Added +20 rebuild signal bonus; (4) Reframed CS Hire Readiness from "does a CS team exist" to "does a CS leadership gap exist" -- existing frontline CSMs with no Director+ leader = HIGH readiness; (5) Confirmed Series C is NOT a hard gate (was already correct in lens YAML; pipeline prompt had drifted); (6) Added "Rebuilder Roles" section with definition, signals, scoring, and detection limitations; (7) Updated Pre-Application Research Checklist with rebuild signal check; (8) Added NRR exception for rebuilder roles; (9) Changed <15 employees from hard disqualifier to soft warning/monitoring signal -- pre-CS inflection companies tracked for growth potential rather than auto-DQ'd, aligning with rescore workflow v4.7; (10) Removed employee_count_min from YAML hard gates; (11) Synchronized tidepool and job_search repos (tidepool was at v1.0, job_search was at v2.15). Net effect: Opens a second scoring track for established companies undergoing CS transformation. Wider funnel at both ends (small companies monitored, mid-size rebuilders scored). Warm intros remain the primary channel for rebuilder roles.
- **v2.16** (Mar 21, 2026): Rebuilder Track spec drafted but never committed. Changes folded into v2.17.
- **v2.15** (Mar 20, 2026): Gate loosening + scoring rebalance. Too many opportunities were getting DQ'd; pipeline reality requires wider gates. Changes: (1) Employee hard cap raised from 200 to 350 (founding CS in new market at 200+ company is still a builder role); (2) Employee min lowered from 15 to 10; (3) Removed "Quota-carrying CSM" from role gates (revenue accountability at early-stage is normal); (4) Removed DEI/Workforce Analytics from domain DQ list; (5) Removed SOC 2/HIPAA from enterprise exception signals; (6) Flattened penalties (>200 emp now -5 instead of -20, Series C -5 instead of -10, title penalty simplified to -5); (7) Removed context-dependent IC title penalties (kept simple -5 for non-Director title); (8) Restored YAML bonuses from v6.5 calibration (builder language +40, Series A +50, etc.); (9) Renamed thresholds: STRONG FIT 80+, GOOD FIT 60-79, MARGINAL 40-59, SKIP <40; (10) Pre-CS inflection lowered to <10 employees; (11) Series B scoring range expanded to 51-300 people; (12) $125K+ comp now +10 bonus; (13) On-site elsewhere penalty removed. Net effect: wider funnel, more opportunities reach scoring, bonuses create differentiation above 40.
- **v2.14** (Mar 2026): v6.5 Scoring Calibration - Critical fix based on applied jobs feedback loop. Every job Eric applied to (Assort Health, Parakeet Health, Ashby, Wolters Kluwer) scored 0-32 pts in v6.4 while APPLY threshold was 60+. Changes: (1) Added MANUAL_REVIEW tier (45-69 pts) for partial matches with positive signals; (2) Reduced title penalty at <25 employees from -15 to -5; (3) Added context-dependent IC title penalties based on company size; (4) Increased builder language bonus to +40 pts; (5) Added leadership title bonus +15 pts; (6) Increased Healthcare B2B SaaS bonus from +10 to +15 pts; (7) Series C routes to MANUAL_REVIEW if builder language present; (8) Added -10 pts for insufficient JD data; (9) Added bonuses section to YAML frontmatter.
- **v2.13** (Mar 2026): Added Customer Persona Gate - classifies companies as business-user-customer vs developer-as-customer. ~60% of "Apply Now" companies were developer tools (Coiled, Inngest, Datafold, etc.) that don't match Eric's enterprise B2B support background. Developer-as-customer companies auto-pass unless they meet enterprise exception: 50+ employees AND 2+ enterprise signals (SOC 2, Fortune 500 customers, enterprise sales, SSO/SAML, compliance, procurement). New Airtable field: Customer Persona.
- **v2.12** (Mar 2026): March 2026 Audit - Two-tier disqualification architecture. Employee hard cap reduced to 200 (CS function exists at this scale). $500M funding/valuation caps. Fortune 500 subsidiary detection. Enhanced acquisition detection (merged, shut down, defunct). Data validation flags for impossible combinations. AgTech/Aquaculture and Climate Hardware exclusions. 150-200 employees moved to penalty zone instead of hard DQ.
- **v2.10** (Mar 2026): Merged v2.9 additions from tidepool repo - added scoring penalties from feedback loop pattern analysis: 500-999 employees (-15 pts), Support title without Director/VP/Head (-15 pts). Added penalties section to YAML frontmatter for machine-readable access. Consolidated all scoring penalties under single "Scoring Penalties" heading. Added Scoring Penalties row to Quick Reference table.
- **v2.8** (Feb 2026): Added feedback loop insights: (1) Stalled company disqualifier - founded >10 years ago with <200 employees indicates growth issues; (2) Expanded IT Support disqualifier to include "Technical Support" and "Help Desk" variants; (3) Added funding stage penalties: -15 pts for $200M-$500M total funding, -10 pts for Series C+. Updated YAML frontmatter, Quick Reference, Role Type Exclusions, Auto-Disqualifiers, and Pre-Application Checklist.
- **v2.7** (Feb 2026): Added "Experience Boundaries" section for gap detection - distinguishes field marketing experience (HP/Palm, Alliance) from pharma/agency/digital marketing I don't have. Added HP/Palm to Career Arc. Added domain expertise gaps as auto-disqualifiers (pharma marketing, agency experience, FinServ, Legal, AdTech, Gov). Updated Quick Reference table.
- **v2.6** (Feb 2026): Added Career Arc section, expanded Bigtincan details (13 products, marquee accounts), added n8n workflow automation to Core Competencies and Active Projects, created resume-base.md and n8n-workflow-portfolio-summary.md in repo
- **v2.5** (Feb 2026): Minor updates
- **v2.4** (Feb 2026): Adjusted baselines- series B; 0-100 people; can have quota for CS roles; added social justice, sales/revenue enablement, architecture/design/ID; loosened titles by including manager customer support/CS
- **v2.4** (Feb 2026): Added Enterprise AI as target sector, added "Network Opportunities" section for founder relationships, added "High-Touch Product Signals" section, added Enterprise AI and AI governance to scoring framework (+10 pts), added network opportunity bonuses to scoring, added exception for founder relationships in auto-disqualifiers, updated Quick Reference table
- **v2.3** (Feb 2026): Added YAML frontmatter for machine-readable metadata, added Current State volatile section, created lens-compact.md for character-limited platforms, added current location to Quick Reference
- **v2.2** (Feb 2026): Added company stage red flags, investor type signals, 100-point scoring framework, pre-application research checklist, title flexibility guidance for early-stage companies
- **v2.1** (Feb 2026): Original comprehensive version with tide pool essence and pathway
