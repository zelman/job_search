# Review Context: General

## What This Code Does
The Lens Project is an AI-powered career identity discovery and job-fit platform. Users complete a guided discovery process (8 sections, AI-facilitated or coach-facilitated) that produces a "lens document" — a portable markdown file with YAML frontmatter. This document governs automated job opportunity scoring via signal matching (not keyword matching). The product has a free tier (lens generation), paid tier ($50/mo briefings), coach channel (B2B2C), and planned enterprise tier (bidirectional matching).

## Architecture
- **Repo:** `github.com/zelman/tidepool` — contains agent lens monolith (root), product code (`lens/`), user files (`users/`), scoring config (root)
- **Product directory:** `lens/` — `src/` (JSX scorers), `app/` (Next.js intake), `schemas/` (LENS-SPEC, templates), `docs/` (enhancements, scoring engine), `deliverables/` (decks, reports), `public/` (static assets)
- **User files:** `users/{name}/` — `lens.md`, `scoring.yaml`, `sources.yaml` per user
- **Related repos:** `zelman/job_search` (n8n pipeline execution code), `zelman/work` (resume/career materials)
- **Deployment:** Vercel auto-deploys from `main` branch. Active URLs: `lens-red-two.vercel.app`, `lens-feedback.vercel.app`
- **Data:** Airtable base `appFO5zLT7ZehXaBo` — Artifact Registry, Testers (13 records), Lens Feedback, Lens Plan tables
- **Pipeline:** n8n cloud (`zelman.app.n8n.cloud`) reads monolith (`tide-pool-agent-lens.md`) via raw GitHub URL

## Key Patterns and Conventions
- **Design language (Swiss Style):** White (#FFFFFF) background, black (#1A1A1A) type, red (#D93025) primary accent, orange (#E8590C) secondary, zero border-radius, hairline rules (1-2px). Helvetica Neue / DM Sans for product. All-caps spaced section labels in red. Green (#2D6A2D) for positive signals. Monospace for scores. DO NOT use wide character spacing on headers.
- **Versioning:** Semantic versioning on filenames or internal version constants. Versions iterate with every build.
- **Artifact registry:** Every artifact gets an Airtable row immediately (table `tblcE723hIH692lSy`). Workflow defined in `ARTIFACT-WORKFLOW.md`.
- **Legal:** IP docs, NDAs are local-only (gitignored). Provisional patent filed 3/24/26, App #64/015,187. Convert to nonprovisional by 3/24/27.
- **Principle:** "Deliver manual first" — build infrastructure only after validating demand.

## Current State
- **Phase:** Active validation. 5 warm testers (Ravi, Nathan, Edith, Brendan, Graham). Tester walkthrough deck built (10 slides, Swiss Style).
- **Patent:** Provisional filed. IP Summary v1.1 and Mutual NDA v1.0 ready. NDAs pending with James, Nathan, Todd, Ravi.
- **Competitive:** Jack & Jill AI is primary reference ($20M seed, ~50K users). Conclusion: J&J ceiling is recruiter-level intelligence; Lens Project floor is coaching-level depth.
- **Open items:** Guardrails.yaml extraction, Vercel deployment of updated components, signal library to replace flat bonus architecture, multi-tenant deferred.

## Known Bugs to Check Against
- See form, scoring, coach, and config profiles for specific bugs.
- **General pattern:** System prompts are hardcoded in JSX files. Any edit to scoring logic, coaching prompts, or gate parameters must be manually synced across files until guardrails extraction is complete.

## Previously Fixed (do not re-flag)
- The dark theme aesthetic (warm neutrals, #a08060) is **tech debt, not a design choice** — Swiss Style migration is planned for all components including lens-scorer.jsx and lens-form.jsx. Flag any new code introducing dark-theme patterns.
- The sample briefing page at `lens-red-two.vercel.app/weekly-inflection-briefing-sample.html` may use old styling. This is expected.

## Integration Points
- **Claude API:** Sonnet for discovery and scoring. No proxy — client-side fetch.
- **Airtable:** Feedback form writes via serverless proxy. Tester tracking and artifact registry via MCP.
- **n8n:** Pipeline reads agent lens from GitHub raw URL. Scoring runs on Haiku 4.5.
- **Vercel:** Static deployment. Serverless functions for Airtable proxy.
- **GitHub:** 4 active repos. Cross-project context via `CONTEXT-cross-project.md` in `zelman/tidepool`.
