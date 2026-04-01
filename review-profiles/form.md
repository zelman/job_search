# Review Context: Form (Intake & Discovery)

## What This Code Does
The intake form is the product's primary user-facing surface. It guides users through context upload (resume, LinkedIn, assessments), status selection, and an 8-section AI-powered discovery conversation that produces a lens document (markdown + YAML frontmatter). Two versions exist: `lens/src/lens-intake.jsx` (~680 lines, newer, Swiss Style, 4-phase flow with persistence) and `lens/src/lens-form.jsx` (~800 lines, original, dark theme, 6-phase flow with live Claude API).

## Architecture
- **lens-intake.jsx:** Intro → Context Upload → Status → Discovery (placeholder). Session persistence via localStorage (phase + status + file metadata). Files need re-upload on return (binary can't serialize). Swiss Style design.
- **lens-form.jsx:** Status → Resume → Intro → Discovery → Synthesis → Done. Live Claude API integration (Sonnet). 8 discovery sections with per-section `systemContext`, `workflowHint`, and optional `scoreDimension` mapping. Typewriter streaming effect. YAML + markdown output with visual scoring tab.
- **Discovery sections (0-7 in code, 1-8 in UI):** Essence, Skills & Experience, Values, Mission & Sector, Work Style, What Fills You, Disqualifiers, Situation & Timeline.
- **Claude API pattern:** fetch to `api.anthropic.com/v1/messages`, model `claude-sonnet-4-20250514`, system prompt as const, response parsed by filtering `type: "text"` blocks.

## Key Patterns and Conventions
- Section numbering: 0-indexed in arrays, 1-indexed in display
- File upload accepts 5 categories: resume (single), LinkedIn PDF (single), writing samples (multiple), assessments (multiple), anything else (multiple)
- Status options: Employed / Actively Searching / In Transition — shapes AI tone
- Coach persona selection modifies system prompt per section
- YAML output uses 6 weighted dimensions: Mission 25%, Role 20%, Culture 18%, Skill 17%, Work Style 12%, Energy 8%

## Current State
- `lens-intake.jsx` is the current build (Swiss Style, persistence, no live API yet in Phase 4)
- `lens-form.jsx` is the reference implementation for the discovery conversation (has working Claude API integration)
- Phase 4 of intake needs to integrate the discovery flow from lens-form.jsx — this is an open wiring task
- Guardrails extraction planned: system prompts may move from hardcoded consts to runtime-fetched `guardrails.yaml`
- **Existing tester URLs must not change** during guardrails refactor

## Known Bugs to Check Against
- **Coach persona state doesn't persist across section transitions** — persona selection resets when moving between discovery sections in lens-form.jsx. Root cause: component-level state, not lifted or persisted.
- **File re-upload required on return** — binary data can't serialize to localStorage. User gets a warm notice listing previously uploaded file names, but must re-upload. This is by design, not a bug — don't flag it.

## Previously Fixed (do not re-flag)
- Infinite re-render on section change was fixed by memoizing the prompt construction
- The dark theme (#0a0a0a) in lens-form.jsx is **tech debt, not a design choice** — Swiss Style migration is planned. If reviewing lens-form.jsx, don't spend time on dark-theme styling bugs — the whole visual layer will be replaced. DO flag any new code that introduces dark-theme patterns.

## Integration Points
- **Input:** User-uploaded files (PDF text extraction for resume), user text responses to discovery prompts
- **Output:** Lens document (markdown body + YAML frontmatter with scoring dimensions and weights)
- **Downstream:** Lens document consumed by n8n scoring pipeline (Job Search project) and lens-scorer.jsx
- **External:** Claude API (Sonnet) for discovery conversation; Airtable for feedback collection (via serverless proxy)
