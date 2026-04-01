# Review Context: Scoring

## What This Code Does
Scoring components evaluate job opportunities against a user's lens document. Two directions exist: **C→R** (candidate scores companies, `lens-scorer.jsx`) and **R→C** (company scores candidates, Role Lens Scorer). Both use Claude API to produce structured JSON scores across weighted dimensions. The scoring system is the product's core differentiator — signal matching, not keyword matching.

## Architecture
- **lens/src/lens-scorer.jsx:** Single-file React component. System prompt hardcoded as `SYSTEM_PROMPT` const (~96 lines). User pastes job listing text → Claude API call → JSON response parsed → visual score breakdown rendered.
- **Role Lens Scorer (R→C):** Built separately (lens/src/). Gate Tolerance + Analysis Depth sliders produce 9 named evaluation modes. Scores candidates against a company's role lens.
- **scoring-config.yaml** (repo root): Dual-mode signal library. Pipeline mode = additive bonuses, product mode = weighted composite. Same signals, different math. User's `scoring.yaml` declares mode.
- **Agent Lens v2.15** (`tide-pool-agent-lens.md` at repo root): Eric's personal lens document, the monolith. n8n reads this via raw GitHub URL. March 20 gate changes: employee max 200→350, min 15→10; quota-carrying CSM removed from role gates; penalties flattened (-5 to -10 range); bonuses restored (builder +40, Series A +50, healthcare +15). Thresholds: STRONG FIT 80+, GOOD FIT 60-79, MARGINAL 40-59, SKIP <40.

## Key Patterns and Conventions
- **Scoring dimension keys:** snake_case (`cs_hire_readiness`, `stage_size_fit`, `role_mandate`, `sector_mission`, `outreach_feasibility`)
- **Score output:** JSON with `scores` object (each key has `score`, `max`, `rationale`), `classification`, `total_score`, `adjusted_score`, `domain_distance`, `builder_or_maintainer`, signal arrays, `briefing`, `red_flags`, `strengths`
- **Thresholds (lens-scorer.jsx):** 60+ APPLY, 40-59 WATCH, <40 PASS
- **Thresholds (Agent Lens v2.15):** 80+ STRONG FIT, 60-79 GOOD FIT, 40-59 MARGINAL, <40 SKIP
- **Domain distance:** Additive modifier (+5 to -10) based on sector proximity
- **Auto-disqualifiers:** Hard gates checked before scoring (PE-backed, >200 employees, public company, etc.)
- **API pattern:** Single completion (no streaming), `claude-sonnet-4-20250514`, response stripped of ```json fences then JSON.parse'd

## Current State
- lens-scorer.jsx uses the **old dark theme** (#0a0a0a, #a08060 accent, DM Sans/DM Mono fonts) — this is **tech debt, pending Swiss Style migration**. Swiss Style target: white (#FFFFFF) background, #1A1A1A text, #D93025 red accent, #E8590C orange secondary, zero border-radius, Helvetica Neue / DM Sans. Flag any new code that deepens dark-theme dependency.
- System prompt is hardcoded with Eric's specific profile (name, target role, sectors, compensation) — not yet generalized for multi-user
- The flat bonus architecture (builder +40, Series A +50, healthcare +15) is known to be incompatible with weight sliders — bonuses dominate and make slider adjustments cosmetic. **Signal library architecture** is the planned fix (signals raise dimension scores instead).
- `scoring-config.yaml` exists but the scorer JSX doesn't read it at runtime — it's a reference doc, not a live config

## Known Bugs to Check Against
- **Flat bonuses override slider weights:** Fixed bonuses (+50, +40) in the Agent Lens make the 6-dimension weight sliders functionally cosmetic. This is a known architectural limitation, not a code bug per se. Don't flag bonus values as wrong — flag any new code that assumes sliders meaningfully affect outcomes.
- **Beam false-negative (March 2026):** A company called Beam was incorrectly filtered out before the v2.15 gate loosening. If reviewing gate logic, check that the loosened parameters (employee max 350, min 10) are applied.

## Previously Fixed (do not re-flag)
- The `>200 employees` hard gate in lens-scorer.jsx system prompt predates the v2.15 loosening to 350 in the Agent Lens. These are different systems (scorer JSX vs. n8n pipeline) — the discrepancy is known. Don't flag it unless someone is trying to synchronize them.

## Integration Points
- **Input:** Raw text (pasted job listing or company description)
- **Output:** Structured JSON score object
- **Upstream:** Lens document defines the scoring criteria (currently hardcoded in system prompt; eventually loaded from user's lens file)
- **Downstream:** Score results displayed in UI; in the n8n pipeline, scores feed into the daily briefing email
- **Config:** `scoring-config.yaml` is the intended source of truth for weights/thresholds but isn't wired to runtime yet
