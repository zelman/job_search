# Review Context: Coach Personas

## What This Code Does
Coach personas are AI coaching characters trained on a real coach's methodology. They modify the system prompts used during the intake form's 8-section discovery flow, changing tone, questioning style, and frameworks applied. The output is always a functional lens document — the persona shapes the journey, not the destination. James Pratt is the first (and currently only) contributing persona.

## Architecture
- **Persona definition:** `James_Pratt_Skill.md` in Claude.ai project knowledge. Contains coaching methodology (Be-Have-Do framework, Authentic Presence, Essence Statement, IAM Model), session style, and behavioral patterns.
- **Persona integration point:** Each discovery section has a `systemContext` field in the section config array. The coach persona modifies or replaces this system context to inject the coach's methodology into the AI conversation.
- **Runtime flow:** User selects coach persona → persona ID stored in component state → per-section system prompts modified → Claude API calls use persona-inflected prompts → lens document output is persona-agnostic (same YAML schema regardless of coach)
- **Coach onboarding pipeline (documented in FigJam):** Recruitment → persona encoding → testing → live deployment → growth flywheel

## Key Patterns and Conventions
- **Persona IDs:** kebab-case (`james-pratt`)
- **Persona files:** Markdown format, stored in project knowledge (not in code repo currently)
- **Section configs:** Array of objects with `systemContext` (string), `workflowHint` (string), `scoreDimension` (optional string)
- **Persona-agnostic output:** The lens document schema doesn't change based on which coach was used. The YAML frontmatter and dimension weights are the same.
- **James Pratt's frameworks:**
  - Be-Have-Do: identity → behavior → action (not the reverse)
  - Authentic Presence: Essence (who you are) + Pathway (where you're going)
  - IAM Model: structured self-assessment framework
  - Coaching style: metaphor-heavy, challenges assumptions, "buoy identity" concept

## Current State
- James Pratt is the only implemented persona
- Persona selection UI exists in lens-form.jsx but state doesn't persist across section transitions (known bug)
- No runtime persona loading — the methodology is baked into system prompt strings
- Multi-coach roster framing exists in pitch decks (v3) but not in code
- Revenue sharing model and coach terms are conceptual, not implemented
- NDA with James Pratt is pending

## Known Bugs to Check Against
- **Persona state doesn't persist across section transitions:** When user moves from one discovery section to the next, the selected coach persona resets. This is the same bug documented in the form profile. Any code touching persona selection or section navigation should be checked against this.
- **No persona validation:** There's no check that a persona ID maps to a valid persona config. If someone passes an invalid persona ID, behavior is undefined.

## Previously Fixed (do not re-flag)
- None documented yet for this area.

## Integration Points
- **Input:** Coach methodology documents (currently markdown in project knowledge); coaching session transcripts/recordings (James Pratt has a library — not yet encoded)
- **Output:** Modified system prompts per discovery section
- **Upstream:** Persona selection UI in intake form
- **Downstream:** Claude API calls during discovery; lens document output (persona-agnostic)
- **External:** James Pratt's coaching materials, session recordings, IAM Model PDF — all in Claude.ai project knowledge, not in code repo
