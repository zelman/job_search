# Claude Code Project Instructions

## Repository Overview

This is the Tide Pool repo. It contains three things:

1. **Eric's personal agent lens** (`tide-pool-agent-lens.md` at root) — consumed at runtime by n8n job search pipelines via raw GitHub URL. This is the monolith (39KB). Still the canonical source for n8n. Do not break backward compatibility.
2. **The Lens Project product** (`lens/`) — Next.js intake app, scoring schemas, scorers, deliverables. This is the product being built for other users.
3. **User files** (`users/`) — per-user lens, scoring config, and sources. The product architecture. Eric is the first user; Ravi Katam is an example.

## Architecture: Three User Files

The product uses three files per user, all in `users/{name}/`:

- **`lens.md`** — Identity + preferences. What the intake form produces. ~7KB. Contains YAML frontmatter (disqualifiers, sector preferences, scoring weights) and markdown body (essence, values, professional identity, work style, energy).
- **`scoring.yaml`** — User's scoring configuration. Slider weights (must sum to 100), personal gates, sector signals, thresholds. This is what changes when a user drags a weight slider.
- **`sources.yaml`** — Which job boards, VC portfolios, alert keywords, and enrichment sources to monitor. Assembled from sector preferences during intake.

These are separate from the monolith. The monolith stays at root for n8n backward compatibility until n8n is updated to read the split files.

## Scoring: Dual-Mode Architecture

`scoring-config.yaml` at repo root defines a **signal library** that supports two scoring modes:

- **Pipeline mode** (n8n): Additive scoring. Signals trigger fixed point bonuses (+50 Series A, +40 builder language). Scores can exceed 100. Backward-compatible.
- **Product mode** (JSX scorer, sliders): Weighted composite. Each dimension scored 0-100, multiplied by user weight. Composite always 0-100. Signals raise/lower dimension scores instead of adding flat bonuses.

Same signals, same gates, same investor lookup. Different math. User's `scoring.yaml` declares which mode via `mode: pipeline | product`.

## Claude API Integration Pattern

JSX scorer and intake components call the Claude API directly (client-side, no proxy):

- **Endpoint:** `https://api.anthropic.com/v1/messages`
- **Model:** `claude-sonnet-4-20250514`
- **Auth:** API key in client-side fetch (no server proxy in current architecture)
- **System prompt:** Hardcoded as `SYSTEM_PROMPT` const at top of component file
- **Response parsing:** Filter `content` blocks for `type: "text"`, strip ```json fences, `JSON.parse`
- **Streaming:** Used in lens-form.jsx discovery flow (typewriter effect). NOT used in lens-scorer.jsx (single completion).
- **Error handling:** try/catch with user-facing error string

**Planned change:** System prompts will move from hardcoded consts to runtime-fetched config (guardrails.yaml). Until then, the const IS the source of truth.

## Key Files

| File | Purpose | Who Edits |
|---|---|---|
| `tide-pool-agent-lens.md` | Monolith lens v2.15. n8n reads this. | Eric via Claude Code |
| `scoring-config.yaml` | Shared signal library, dual-mode scoring | Platform (not users) |
| `users/eric-zelman/lens.md` | Eric's identity in product format | Intake form / Eric |
| `users/eric-zelman/scoring.yaml` | Eric's weights and gates | Sliders / Eric |
| `users/eric-zelman/sources.yaml` | Eric's feeds, VCs, boards | Eric |
| `lens/src/lens-scorer.jsx` | Swiss Style scorer, fetches lens at runtime | Claude AI / Claude Code |
| `lens/src/lens-scorer-compare.jsx` | Dual-schema comparison with weight sliders | Claude AI / Claude Code |
| `lens/schemas/LENS-SPEC.md` | Formal schema spec (the real product spec) | Claude Code |
| `lens/schemas/candidate-lens-v1.md` | Product lens format with 6-dim schema | Claude Code |
| `lens/schemas/sources-template.yaml` | Template for source config generation | Claude Code |
| `lens/docs/enhancements.md` | Enhancement tracking (check before starting work) | Both |
| `lens/docs/SCORING-ENGINE.md` | Pipeline architecture and evolution | Claude Code |
| `lens/app/` | Next.js intake application | Claude Code |
| `review-profiles/` | Code review context files (5 profiles) | Claude Code |
| `CONTEXT-cross-project.md` | Sibling project awareness | Both |

## Versioning Rules

When editing `tide-pool-agent-lens.md`:
1. Update `last_updated` in YAML frontmatter (format: "YYYY-MM-DD")
2. Increment version (e.g., 2.15 -> 2.16)
3. Update footer version and date
4. Add changelog entry
5. Keep YAML and body text consistent (employee counts, penalty values, thresholds)

When editing `scoring-config.yaml`:
1. Increment version
2. Update `last_updated`
3. Ensure both pipeline and product mode entries stay in sync for shared signals

## Design Language: Swiss Style

All product-facing artifacts use:
- Background: White (#FFFFFF)
- Typography: Helvetica Neue / Helvetica / Arial
- Primary accent: Red (#D93025)
- Secondary accent: Orange (#E8590C)
- Border radius: Zero everywhere
- Rules: 2px black for major boundaries, 1px #EEEEEE for subdivisions

The old dark theme (#0a0a0a, #a08060 gold) is retired for product materials. All remaining dark-theme components (lens-scorer.jsx, lens-form.jsx) are tech debt pending Swiss migration. Do not extend dark-theme patterns.

## Naming Conventions

- **Discovery sections:** 0-indexed in code arrays, 1-indexed in user-facing display (sections 0-7 internally = sections 1-8 in UI)
- **Scoring dimension keys:** snake_case (`cs_hire_readiness`, `stage_size_fit`, `role_mandate`, `sector_mission`, `outreach_feasibility`)
- **User directories:** kebab-case (`users/eric-zelman/`, `users/ravi-katam/`)
- **Coach persona IDs:** kebab-case (`james-pratt`)
- **JSX files:** kebab-case (`lens-scorer.jsx`, `lens-intake.jsx`)
- **YAML keys:** snake_case for machine fields, sentence-case for human-readable descriptions
- **Design tokens:** Raw hex codes (not CSS variables): #D93025 red, #E8590C orange, #1A1A1A text, #EEEEEE rules, #2D6A2D positive signals

## What Lives Where (Repo Boundaries)

- **tidepool** (this repo): Lens documents, scoring config, product code, schemas, user files
- **job_search** (separate repo): n8n workflow JSON, pipeline execution code, PE detection modules, Airtable integration
- **work** (separate repo): Resume, cover letters, career materials

Do NOT put n8n execution code (JavaScript modules, workflow JSON) in this repo. Scoring *configuration* (what signals to look for, how to weight them) belongs here. Scoring *execution* (the n8n nodes that run the evaluation) belongs in job_search.

## Local Development & File Handoff

### Local Clone

The canonical local copy of this repo is:
```
/Users/zelman/Desktop/Quarantine/Side Projects/tidepool
```

Shell alias: `tidepool` (launches Claude Code in this directory)

### File Handoff from Claude AI

Claude AI (claude.ai) creates JSX components, scoring configs, markdown docs, and other artifacts. These are downloaded to the user's machine and should be placed in the correct repo location before committing.

**Where files go:**

| File type | Repo path |
|---|---|
| JSX scorers, components | `lens/src/` |
| Next.js app components | `lens/app/components/` |
| Next.js API routes | `lens/app/api/` |
| Schema specs, templates | `lens/schemas/` |
| Documentation | `lens/docs/` |
| Pitch decks, reports | `lens/deliverables/` |
| Static/public assets | `lens/public/` |
| User lens files | `users/{name}/lens.md` |
| User scoring configs | `users/{name}/scoring.yaml` |
| User source configs | `users/{name}/sources.yaml` |
| Review profiles | `review-profiles/` |
| n8n workflow JSON | **DO NOT PUT HERE** — goes in `zelman/job_search` |

### Vercel Deployment

The Next.js app in `lens/` deploys to Vercel. When Claude Code receives a JSX component to add:
1. Place it in the correct path per the table above
2. If it's a page component, wire it into `lens/app/page.js` or create a new route
3. If it has API dependencies (Claude API calls), add the route in `lens/app/api/`
4. Commit, push, and Vercel auto-deploys from the `main` branch

### Ideal Workflow

1. Eric works with Claude AI (claude.ai Lens Project) to design/iterate on components
2. Claude AI produces files (JSX, YAML, MD) — these download to `~/Downloads`
3. Eric tells Claude Code: "Move ~/Downloads/[filename] to [repo path] and commit"
4. Claude Code moves file into repo, commits, pushes — Vercel auto-deploys

**Example:**
```
Move ~/Downloads/lens-scorer.jsx to lens/src/lens-scorer.jsx and commit with message "Swiss Style scorer with runtime lens fetch"
```

Claude Code should use the file placement table above to suggest the correct destination if Eric doesn't specify one.

## Current State (April 2026)

- Agent lens at v2.15 (gates loosened, bonuses restored, thresholds renamed)
- Next.js intake app in `lens/app/`
- Dual-mode scoring config committed
- User architecture (`users/`) committed with Eric + Ravi example
- Enhancement backlog in `lens/docs/enhancements.md`
- n8n still reads the monolith; split file migration is on the backlog
- Provisional patent filed 3/24/26 (App #64/015,187). Convert to nonprovisional by 3/24/27.
- 5 warm testers in pipeline (Ravi, Nathan, Edith, Brendan, Graham)
- Dark theme → Swiss Style migration: decided April 1, 2026. All components will migrate.
- Guardrails extraction (system prompts → guardrails.yaml): schema designed, deferred until testers complete current sessions
- Review profiles system added (`review-profiles/`) for code review context injection

## Known Bugs & Active Issues

### Coach Persona State Persistence (OPEN)
**Symptom:** Coach persona selection resets when navigating between discovery sections in lens-form.jsx.
**Root cause:** Persona ID stored in component-level state, not lifted or persisted to session storage.
**Impact:** Users must re-select their coach persona on each section transition.
**Workaround:** None.

### Flat Bonuses Override Weight Sliders (ARCHITECTURAL)
**Symptom:** In pipeline mode, fixed bonuses (+50 Series A, +40 builder) dominate the score, making dimension weight sliders functionally cosmetic.
**Root cause:** Additive bonuses bypass the weighted composite math. This is by design in pipeline mode but creates a UX mismatch when sliders are shown.
**Impact:** Users think they can tune results by adjusting sliders; actual effect is minimal.
**Status:** Signal library architecture (signals raise dimension scores instead of flat bonuses) is the planned fix. Product mode in scoring-config.yaml is the implementation path.

### Config Drift Between scoring-config.yaml and JSX System Prompts (ACTIVE)
**Symptom:** Threshold values, gate parameters, or dimension weights may differ between the YAML config file and the hardcoded system prompts in lens-scorer.jsx.
**Root cause:** JSX system prompts haven't been wired to read scoring-config.yaml at runtime. Both are edited independently.
**Impact:** Reviewer can't trust either source as canonical without checking both.
**Workaround:** Check both files when reviewing scoring changes. scoring-config.yaml is intended to become the single source of truth.

## Previously Fixed (do not re-flag)

- **Infinite re-render on section change** — Fixed by memoizing prompt construction in lens-form.jsx. The memoization may look unnecessary to a reviewer; it's load-bearing.
- **Beam false-negative (March 2026)** — Company called Beam was incorrectly filtered before v2.15 gate loosening. The looser parameters (employee max 350, min 10) are the fix, not a regression.
- **Dark theme in lens-scorer.jsx** — Uses #0a0a0a background, #a08060 accent. This is tech debt pending Swiss Style migration (decided April 1, 2026), not a design choice. Don't fix dark-theme styling bugs — the whole visual layer will be replaced. DO flag any new code that introduces dark-theme patterns.

---

## Session Hygiene

At the end of any substantive session, generate a wrap-up before the user disconnects. This prevents knowledge from dying in the terminal.

### End-of-Session Checklist

1. **Artifacts:** List every file created or modified this session with version numbers (before → after). New files need an Artifact Registry entry in Airtable (base appFO5zLT7ZehXaBo, table tblcE723hIH692lSy).

2. **Decisions:** Bullet any architectural, strategic, or design decisions made. One sentence each: what was decided and why.

3. **CONTEXT update:** Draft the specific text to add or replace in CONTEXT-lens-project.md. Write the actual paragraph, not a vague reminder.

4. **Commit:** Stage and commit with a descriptive message. Group related changes. Don't bundle unrelated work.

5. **Memory flag:** If anything changed that should persist in Claude.ai memory (stable facts, tool configs, project structure), note it explicitly so the user can add it in their next Claude.ai session.

### Versioning

All artifacts use semantic versioning (v1.0, v1.1, v2.0). Track in filenames or internal version constants. Bump on every meaningful change.

### Legal Files

Signed NDAs, patent application drafts, and attorney correspondence are local only — never committed to git. Strategy reasoning (IP-STRATEGY.md, competitive-landscape.md) is committed normally.

### What Goes Where

- **Git (this repo):** Product code, specs, schemas, scorers, deliverables, strategy docs
- **Airtable Artifact Registry:** Row for every versioned artifact with location and git status
- **Claude.ai CONTEXT files:** Living state summaries, updated via session wrap-up
- **Claude.ai memory:** Stable personal facts, tool configs, project structure (slow-changing)
- **Local only (gitignored):** Signed legal documents, credentials, API keys
