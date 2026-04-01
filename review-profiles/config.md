# Review Context: Configuration & Infrastructure

## What This Code Does
Configuration files define scoring parameters, deployment routing, guardrails for AI behavior, and YAML schemas for lens documents. This area is in active transition — most config is currently hardcoded in JSX component files and being extracted to standalone YAML files for runtime loading.

## Architecture
- **scoring-config.yaml** (repo root): Dual-mode config defining signal library for both pipeline mode (n8n, additive) and product mode (JSX, weighted composite). Shared signals, gates, investor lookup. User's `scoring.yaml` declares mode.
- **guardrails.yaml** (planned, `lens/config/` or similar): Will externalize hardcoded system prompts from JSX components. Schema designed but file not yet created. Pre-work steps safe to execute; JSX refactor deferred until current testers complete sessions.
- **vercel.json**: Routing config for Vercel deployments. Root set to `/lens-project`.
- **Lens document schema:** YAML frontmatter + markdown body. 6 scoring dimensions with weights. Instant disqualifiers as array. Score thresholds defined.
- **Three-file user architecture** (in `zelman/tidepool`): `users/` directory with `lens.md`, `scoring.yaml`, `sources.yaml` per user.

## Key Patterns and Conventions
- **YAML style:** snake_case keys for machine fields, sentence-case for human-readable descriptions
- **Scoring dimensions:** Mission (25%), Role (20%), Culture (18%), Skill (17%), Work Style (12%), Energy (8%) — these weights are authoritative
- **Score thresholds (product):** Defined in scoring-config.yaml, should match what's in system prompts
- **Score thresholds (Agent Lens v2.15):** STRONG FIT 80+, GOOD FIT 60-79, MARGINAL 40-59, SKIP <40
- **Score thresholds (lens-scorer.jsx):** APPLY 60+, WATCH 40-59, PASS <40 — note the label difference
- **Vercel deployment:** Two active deployments: `lens-red-two.vercel.app` (intake form), `lens-feedback.vercel.app` (feedback form)
- **Airtable integration:** Feedback form uses serverless API route (`api/submit.js`) to proxy writes. Token is server-side only.

## Current State
- Guardrails extraction is in planning. Schema drafted. Branch and fetch utility not yet created.
- **Critical constraint:** Existing tester URLs must not break during any config refactor. lens-red-two.vercel.app and lens-feedback.vercel.app are in active use.
- scoring-config.yaml exists but is disconnected from runtime — the JSX system prompts are the actual source of truth
- The plan is: `guardrails.yaml` → fetch utility → JSX reads config at mount → system prompts built from config instead of hardcoded strings
- Multi-tenant infrastructure is deferred until demand is validated. Manual pipeline runs first.

## Known Bugs to Check Against
- **Config drift between scoring-config.yaml and system prompts:** The YAML file and the hardcoded system prompts may have different threshold values, dimension weights, or gate parameters. Until runtime loading is wired, any edit to one must be manually synced to the other.
- **Threshold label mismatch:** lens-scorer.jsx uses APPLY/WATCH/PASS. Agent Lens v2.15 uses STRONG FIT/GOOD FIT/MARGINAL/SKIP. These are different systems with different scales — don't try to unify them unless explicitly asked.

## Previously Fixed (do not re-flag)
- None — this area is new enough that there's no fix history.

## Integration Points
- **Input:** Human-authored YAML defining scoring rules, gates, dimensions, weights
- **Output:** Config consumed by JSX components (planned: at mount via fetch), by n8n pipeline (at runtime via raw GitHub URL)
- **External:** Vercel (deployment), Airtable (data storage), GitHub raw URLs (n8n fetches agent lens at runtime)
- **Sensitive:** Legal docs (IP summary, NDA) are in `legal/` directory and gitignored. Never include in config files or commit.
