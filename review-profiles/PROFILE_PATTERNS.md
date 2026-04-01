# PROFILE_PATTERNS for `zelman/lens`

Drop this into `code-review.mjs` replacing the existing PROFILE_PATTERNS object.

```javascript
const PROFILE_PATTERNS = {
  // Intake form, discovery sections, file upload, session persistence
  form:     /lens-form|lens-intake|intake|discovery|section.*component|phase|upload.*context|status.*select/i,

  // Scoring logic, dimensions, weights, YAML output, lens document evaluation
  scoring:  /lens-scorer|role-lens|scoring|dimension|weight|yaml.*output|score.*break|threshold|disqualif|domain.*distance|builder.*maintainer/i,

  // Coach persona files, James Pratt integration, persona framework
  coach:    /coach|persona|james.*pratt|pratt|be-have-do|essence.*statement|iam.*model|authentic.*presence/i,

  // Configuration, guardrails, scoring-config, YAML schemas, Vercel config, deployment
  config:   /scoring-config|guardrails|vercel\.json|\.yaml$|\.yml$|config\/|api\/submit|serverless/i,
};
```

## Auto-Detection Logic

The script reads filename + first 500 characters of content. Pattern priority (first match wins):

1. `coach` — most specific, unlikely false positives
2. `scoring` — catches scorer components and scoring config
3. `form` — catches intake/discovery components
4. `config` — catches YAML files and deployment config
5. `general` — fallback when no pattern matches

## Override Examples

```bash
# Auto-detect (should pick "scoring")
node code-review.mjs ./lens/src/lens-scorer.jsx --model sonnet --log

# Auto-detect (should pick "form")
node code-review.mjs ./lens/src/lens-intake.jsx --model sonnet --log

# Manual override when auto-detect is wrong
node code-review.mjs ./lens/schemas/LENS-SPEC.md --profile general --model sonnet --log

# Force Opus for complex scoring logic changes
node code-review.mjs ./lens/src/lens-scorer.jsx --model opus --log
```

## "Always Review These" (for skill doc)

These files should trigger code review on any change:
- `lens/src/lens-scorer.jsx` — core scoring logic with hardcoded system prompt
- `lens/src/lens-intake.jsx` — primary user-facing surface (when wired)
- `lens/src/lens-form.jsx` — reference discovery implementation
- `scoring-config.yaml` — shared signal library, dual-mode scoring config
- `users/*/scoring.yaml` — user scoring parameters
- `tide-pool-agent-lens.md` — monolith (n8n backward compat)

## "Use Opus When"

- Changes to system prompts (scoring criteria, coaching instructions, gate parameters)
- Changes to the lens document output schema (YAML frontmatter structure)
- Changes touching both intake and scoring in the same PR
- Any change to auto-disqualifier logic
- Coach persona integration changes (new persona, persona loading, prompt modification)
