# CONTEXT-cross-project.md — Sibling Projects Overview

*Last updated: April 13, 2026*

This file exists in multiple Claude Projects so each one knows what the others are doing. It's a shared awareness layer, not a substitute for each project's own CONTEXT file. The canonical version lives in git (`zelman/tidepool`). Update across all projects when something significant changes.

---

## Active Projects

### Lens Project (Claude Project: "Lens Project")

**What it is:** A bidirectional identity marketplace for hiring. Candidates and companies each create structured identity documents (lenses) through AI-coached discovery. A matching engine scores compatibility, flags tensions, and produces briefings instead of job alerts. Core principle: signal matching over keyword matching.

**Company:** Zelman Labs LLC (Rhode Island). EIN obtained. SAM.gov registration in progress.

**IP:** Provisional patent filed March 24, 2026 — App #64/015,187, micro entity. Nonprovisional conversion deadline: March 24, 2027. Microsoft patent US20250378320A1 flagged as prior art.

**What's built:**
- `LensIntake.jsx` — ~2200-line React intake form with live Claude API integration (Sonnet), 8 discovery sections, session persistence, guardrails
- Serverless proxy architecture on Vercel (`/api/discover`, `/api/synthesize`, `/api/score` — all live)
- `SYNTHESIS-PROMPT.md` for third-person narrative output; `lens-report-renderer.jsx` for International Style PDF
- Scoring schema: 6 weighted dimensions (Mission 25%, Role 20%, Culture 18%, Skill 17%, Work Style 12%, Energy 8%)
- Feedback form (International Style, Airtable-backed, Vercel-deployable)
- Media intake spec (audio/video, AssemblyAI for diarization — spec complete, not yet implemented)
- Competitive landscape doc (`specs/lens-competitive-landscape.md`, 18+ entries; Airtable as record-level source of truth)
- Strategic brief v1.3 — comprehensive analytical stress-test document
- Stress test synthesis v1 — 8 strategic pivots from 4 independent AI model adversarial tests
- Positioning docs: Lens for Hiring Leaders v2.1 (corporate audience), Lens for Executive Recruiting v1.2 (Beth Stewart audience), Core Narrative v1.2

**Dedicated repo:** `github.com/zelman/lens` (`components/`, `schemas/`, `docs/`, `scoring-config.yaml`, `review-profiles/`)

**Current state (April 2026):** In active tester validation. Serverless proxy live on Vercel. Post-guardrails version deployed. Tester cohort includes Jared Hibbs (completed full flow), Brendan McCarthy, Niels Godfredsen, Graham Jerabek, Luis Sampaio, Ravi Katam. Three tester-driven fixes shipped: prompt bias, redundant questioning, missing privacy disclosure.

**Strategic pivot (April 7–12, 2026):** Deep discovery only justified at $300K+/board-level hires (Edie Hunt, 4/7). Executive recruiters (not HR, not coaches) are the likely buyer. Consulting firms as additional channel (Anne Birdsong, 4/8). Role lens leads — stakeholder alignment is the primary pain. 8 strategic pivots confirmed via adversarial stress test with 4 independent AI models (4/12). Language shift: "prevent expensive misalignment" over "deeper identity matching." Oh/Wang/Mount reframed as "inspired by," not "foundation."

**Active validation pipeline:** Beth Stewart/Trewstar (no response, P1), Jenn Monkiewicz follow-up (4/15), Chris Lyon intro via Anne Birdsong. Rob Birdsong deprioritized (avoidant).

**Funding pathways:** Bootstrap ($2-5K), contractor-assisted ($30-50K), full team pre-seed ($750K), NSF SBIR Phase I ($275K non-dilutive — pitch drafted v0.3, RI Innovate Fund identified as matching source).

**Key concepts:**
- Coach personas (coaches contribute methodology to power custom AI coaching; James Pratt is first)
- Bidirectional lens (candidate lens scores companies C→R; role lens scores candidates R→C)
- Freemium as distribution (free lens intake → paid scored briefings or enterprise use)
- Oh/Wang/Mount 2011: observer ratings outperform self-reports for job performance prediction — **inspiration for** coached discovery depth, **not validation** that our approach achieves observer-grade validity
- International Style design language (white, black type, #D93025 red, zero border radius)

**How it relates to other projects:**
- Productizes the approach Eric built for himself in the Job Search project
- The Agent Lens (v2.15) is a hand-built lens document; the Lens Project automates creating one for anyone
- Shares "append, don't overwrite" and metadata-as-meaning philosophy with the Archive
- Shares coaching frameworks (James Pratt's Be-Have-Do, Essence/Pathway, IAM Model) across all projects
- The Job Search project's key learning — that desirable roles are filled through networks before reaching job boards — is the same distribution problem the Lens Project needs to solve

---

### Job Search (Claude Project: "Job Search 2")

**What it is:** Eric's personal AI-powered job search automation — scrapers, enrichment, scoring, and delivery pipelines running on n8n. Also the workspace for resume/cover letter generation, role evaluation, outreach drafting, and interview prep.

**What's built:**
- Enrich & Evaluate Pipeline v9.8 (company scoring, six-phase with hard gates in code)
- Job Evaluation Pipeline v6.4 (job posting scoring, with v6.5 alignment queued)
- Job alert parser pipeline (Brave Search enrichment + full Claude scoring)
- VC portfolio scraper pipelines (5 groups covering healthcare, climate, social justice, enterprise, micro-VC)
- Airtable base (`appFEzXvPWvRtXgRY`) for company tracking, job tracking, LinkedIn connections, applications
- Agent Lens (v2.15) consumed at runtime by n8n workflows via raw GitHub URL
- Resume template (docx skill with F-pattern layout, Calibri font, strict formatting rules)
- Portfolio artifacts: Yakima County APS rollout plan (v2 and v3) and CPS expansion video pitch

**Agent Lens v2.15 scoring thresholds:** STRONG FIT 80+, GOOD FIT 60–79, MARGINAL 40–59, SKIP <40. Gates loosened March 20: employee max 200→350, min 15→10; quota-carrying CSM removed from role gates; DEI/Workforce Analytics removed from domain DQ; penalties flattened (−5 to −10); v6.5 bonuses restored.

**Current state (April 2026):**
- Pipelines operational. Cold outreach continues to yield low results — warm intros remain the only channel producing real conversations.
- LinkedIn profile updated March 18 to fix title perception gap
- Fractional CS positioning explored in February — paused but available as parallel path
- **Note:** The Job Search 2 project's own CONTEXT file is the authoritative source for current pipeline status, active opportunities, and outreach state. This section captures structural context only.

**Target profile (refined):**
- Founding or first CS/support leadership role at early-stage B2B SaaS
- Series A/B, 20-100 employees, under ~$75M total funding, VC-backed (not PE)
- Genuine 0-to-1 build mandate where founder-led customer relationships are breaking down
- Title secondary to substance — Senior/Lead with real build mandate equals VP/Head with same
- Preferred sectors: healthcare SaaS (provider-side), regulated industries, developer tools with enterprise sales motion
- Location: Remote preferred, open to relocation to SF or NYC

**Key learnings (relevant to all projects):**
- **Cold outreach doesn't work for these roles.** Filled through founder/investor networks before reaching job boards. Network positioning problem, not a tooling problem.
- **The title gap is real and costly.** "VP of Customer Support" causes hiring managers to miss CS/renewal/revenue accountability. The exact problem the Lens Project aims to solve.
- **Pipeline false positive rate was high (~74% in early batches).** Root cause: pre-scoring gates in prompt language, not code. Fix: hard gates in code. Relevant to Lens scoring architecture.
- **CS hire readiness is the highest-signal scoring factor.** "Does this company need this hire right now" matters more than company fit.
- **Warm intros are the only channel producing real conversations.** Network broad but shallow outside former Bigtincan colleagues.

**Technical stack:** n8n cloud (zelman.app.n8n.cloud), Brave Search API, Claude Haiku 4.5 (scoring), Claude Code (implementation), Browserless.io, Airtable, GitHub (`zelman/job_search`)

**How it relates to other projects:**
- The working proof of concept for the Lens Project's product thesis
- The Agent Lens doc bridges both — Eric's personal lens, and the template for what the Lens Project produces for others
- Resume and career materials live in `zelman/work` repo
- Coaching frameworks from James Pratt inform lens signals that drive scoring
- Portfolio artifacts demonstrate what a "lens-matched" candidate looks like in practice

---

### Tide Pool Archive (within Claude Project: "Lens Project")

**What it is:** A personal digital archive (tide-pool.org) for cataloging records, books, recipes, and ephemera. Curation as authorship, metadata as voice, objects as markers of time and self.

**What's built:**
- Last.fm → Airtable automation (weekly top 3 albums, Sunday 9pm, with deduplication)
- Airtable base (`appFO5zLT7ZehXaBo`) with running schema
- Richer metadata schema designed but not yet implemented (temporal, stance, function, tide fields)
- Domain registered: tide-pool.org

**Current state (April 2026):** Last.fm automation running. Static site not started (planned: Eleventy + flat-file markdown architecture). Weekend cataloging practice designed but activity level unclear.

**How it relates to other projects:**
- Shares the `zelman/tidepool` GitHub repo with the Agent Lens
- "Append, don't overwrite" philosophy originated here and carries into the Lens Project
- The tide pool metaphor is the connective tissue across all projects (from coaching with James Pratt)
- tide-pool.org is Archive only — do NOT embed in Lens product materials
- Design language: Archive design TBD. Lens Project uses International Style (white background, red/orange accent). These are separate.

---

## Shared Infrastructure

| Resource | Used By |
|---|---|
| n8n cloud (zelman.app.n8n.cloud) | Job Search, Archive |
| Vercel | Lens Project (serverless proxy, frontend hosting) |
| Airtable | Job Search (`appFEzXvPWvRtXgRY`), Lens + Archive (`appFO5zLT7ZehXaBo`) |
| GitHub `zelman/tidepool` | Archive, Agent Lens, this cross-project file |
| GitHub `zelman/lens` | Lens Project product repo |
| GitHub `zelman/job_search` | Job Search pipelines |
| GitHub `zelman/work` | Resume, career materials |
| Claude.ai Projects | Strategic thinking, document creation, integrations (Job Search 2, Lens Project) |
| Claude Code | n8n engineering (Job Search), local file ops (all), lens repo commits |
| Claude Haiku 4.5 | Pipeline scoring (Job Search) |
| Claude Sonnet | Lens discovery conversations, synthesis |
| Brave Search API | Job Search enrichment |
| Browserless.io | Job Search scraping |
| Last.fm API | Archive automation |
| Figma/FigJam MCP | Workflow diagrams (Lens Project) |

---

## Key People (across projects)

### Coaching & Lens Project — Core
- **James Pratt** — Career coach (Nov-Dec 2025). First contributing coach persona. Methodology encoded: Be-Have-Do, Essence/Pathway, IAM Model. Challenged enterprise precision assumption (3/30/26). NDA pending.
- **Nathan Fierley** — Potential co-builder. Tested James Pratt persona. Reframed product toward enterprise hiring and bidirectional matching. No formal commitment. No NDA needed.
- **Todd Gerspach** — Previous career coach, extensive C-level network. Freemium GTM advocate. NDA pending.

### Lens Project — Validation Contacts
- **Edie Hunt** — Retired Goldman Sachs partner, COO HCM, Chief Diversity Officer. Produced the most significant strategic reframe (4/7/26): exec recruiters as buyer, $300K+ hires only for deep discovery. NDA pending review.
- **Anne Birdsong** — 20+ yrs CPG sales leadership. Call completed 4/8. Key signals: consulting firm channel (Accenture-type), validated cost-of-bad-hire from K-C experience, flagged IP protection unprompted, Chris Lyon intro pending, volunteered to test intake form.
- **Rob Birdsong** — VP Google Cloud Consulting North America, ~1,200 reports. Appears avoidant, deprioritized.
- **Jenn Monkiewicz** — Fractional CPO, built custom AI HR system with SCX.ai. Met week of 4/7. Follow-up Wednesday 4/15.
- **Edith McCarthy** — Demoed product, recruited testers Brendan and Graham. Separate from Edie Hunt. NDA pending.
- **Bob Slaby** — CCO at Bigtincan (Vector Capital hire), now at Showpad. Outreach sent 4/8 for exec recruiter intros; no response.
- **Jordan Frank** — Runs Traction Software 23+ years, inventor, board member. 10-slide intro deck built for 4/13 meeting.

### Lens Project — Testers
- **Jared Hibbs** — Completed full flow, submitted structured feedback
- **Brendan McCarthy** — ~2 hours, flagged repetitive questioning
- **Niels Godfredsen** — Engineer at Remedy, committed to test (also personal contact who facilitated LeanData intro)
- **Graham Jerabek** — Strongest positioning feedback: simplify pitch, use J&J as anchor
- **Luis Sampaio** — Challenged "only works for people who know what they want" assumption
- **Ravi Katam** — Longtime CS colleague from Bigtincan, early tester. Completed discovery flow; flagged resume/LinkedIn integration gaps.
- **Steve Hendrix** — Former Bigtincan colleague. Agreed to test (4/10). NDA pending.

### Job Search — References & Advocates
- **Patrick Welch** — Former President/COO, Bigtincan. Top reference. Vouches for Eric as VP of Customer Success (not just Support).
- **Matt MacInnis** — COO, Rippling. Recommendation relationship.
- **David Keane** — Bigtincan founder. Skeptical of AI SaaS; received moat-focused deck. Connected Jenn Monkiewicz intro.

### Other
- **Howard** — Eric's father-in-law. Introduced Edie Hunt.
- **Don Whalen** — Bigtincan colleague. NDA pending.
- **Beth Stewart** — CEO Trewstar; places women on corporate boards. Intro email sent by Edie Hunt. No response as of 4/13. P1 validation target.
- **Chris Lyon** — CRO at League, ex-Workday/Model N. Intro pending via Anne Birdsong.

---

## The Thread Between Projects

These aren't three unrelated things. They share a common thesis:

**Identity is relational and evolving, not fixed.** The Archive captures this through objects and meaning over time. The Job Search operationalizes it through signal-based scoring instead of keyword matching. The Lens Project productizes it so others can do the same.

The tide pool metaphor (from coaching with James Pratt) is the connective tissue: creating conditions for life to flourish, cyclically filled and emptied, depth over breadth.

**Established pattern (April 2026):** The Job Search project proved the Lens Project thesis in real time. The market reads Eric as "Support expert" from surface signals; the lens reveals a CS leader with renewal accountability and 0-to-1 build experience. The gap between how the market reads a profile and what the person actually brings is exactly the problem the Lens Project solves. This lived experience is now the product's origin story and strongest positioning asset. Adversarial stress testing with 4 independent AI models (April 12) confirmed the thesis holds but produced 8 pivots that sharpen the positioning: role lens leads, "prevent expensive misalignment" language, first customer = 10-20 person retained boutique, Oh/Wang/Mount as inspiration not validation.

---

## Toolchain Notes

- **Claude.ai Projects** handle integrations, research, document creation, and strategic thinking
- **Claude Code** handles git operations, local file changes, n8n workflow engineering, and lens repo commits
- Shell alias: `tidepool` launches Claude Code in `Side Projects/tidepool`
- GitHub MCP configured in Claude Code via Docker + personal access token (expires July 2026)
- Presentation work uses `pptxgenjs` via Node.js; LibreOffice for PDF conversion
- Claude Opus 4.6 model string: `claude-opus-4-6` (no date suffix); Sonnet 4 for routine code review
- **Claude Code Sessions tables** sync context between Claude Code (CLI) and Claude AI (web):
  - **Lens:** `tblLgWUHElcbKABKF` in base `appFO5zLT7ZehXaBo` ([view](https://airtable.com/appFO5zLT7ZehXaBo/tblLgWUHElcbKABKF/viwm16G91N1PhRL0V))
  - **Job Search:** `tblHhzGpsgNJUIqy0` in base `appFEzXvPWvRtXgRY` ([view](https://airtable.com/appFEzXvPWvRtXgRY/tblHhzGpsgNJUIqy0/viwQhRbvnMi7cqzBN))
  - Claude Code should write a row to the appropriate table when completing code changes, so Claude AI has visibility into recent work. This is part of the **session-wrapup skill** — include Sessions table updates in the cleanup/handoff checklist.
  - Claude AI should check these tables when picking up work after a gap or when Claude Code activity is uncertain.

---

*This file is a bridge, not a source of truth. Each project's own CONTEXT file has the detailed state. Canonical version lives in `zelman/tidepool` repo. Update across all projects when a major milestone, new person, or structural change occurs.*
