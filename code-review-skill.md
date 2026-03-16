# Skill: Code Review via External Model

## Purpose

This skill enables Claude Code to request independent code review from a different Claude model (Opus 4.6 or Sonnet 4) by shelling out to a local script. Use it to catch bugs, edge cases, scoring logic errors, and architectural issues that a single-model pass can miss.

---

## Trigger Phrases

When the user says any of these, run a code review using this skill:

| User says | Action |
|-----------|--------|
| "review this with Opus" | Review the file(s) just modified with `--model opus` |
| "run Opus review" | Same as above |
| "Opus review on [file]" | Review the specified file with `--model opus` |
| "get a second opinion" | Review recent changes with default model (Sonnet) |
| "review this" | Review the file(s) just modified with default model |
| "external review" | Review recent changes with default model |
| "review [file] with Sonnet" | Review specified file with `--model sonnet` |

When triggered, Claude Code should:
1. Identify the file(s) to review (most recently modified, or specified by user)
2. Construct appropriate `--context` based on what the code does
3. Add `--focus` areas if the recent work had specific concerns
4. Run the script and report findings to the user

---

## Setup

### Requirements
- `code-review.mjs` in the project root (or adjust path below)
- `ANTHROPIC_API_KEY` environment variable set in your shell
- Node.js (already available in Claude Code environments)

### Installation
1. Place `code-review.mjs` in your project root
2. Add these instructions to your project's `CLAUDE.md` or load as a skill
3. No other dependencies required

---

## Script Reference: code-review.mjs

### Location
`./code-review.mjs` (project root)

### Usage

```bash
# Review a file (defaults to Sonnet - fast, cheap, good for most reviews)
node code-review.mjs ./path/to/file.js

# Review with Opus for complex or high-stakes changes
node code-review.mjs ./path/to/file.js --model opus

# Add context so the reviewer understands what the code does
node code-review.mjs ./path/to/file.js --context "n8n Code node that scores companies for job search fit"

# Focus the review on specific concerns
node code-review.mjs ./path/to/file.js --focus "scoring logic,edge cases,null handling"

# Combine flags
node code-review.mjs ./pipeline.json --model opus --focus "disqualification gates,regex patterns" --context "Tide Pool enrichment and scoring pipeline"

# Review staged git changes via stdin
git diff --staged | node code-review.mjs --stdin --context "staged changes to enrichment pipeline"

# Review a specific function or section via stdin
cat ./src/scoring.js | node code-review.mjs --stdin --focus "boundary conditions"
```

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `<file>` | (required unless --stdin) | Path to the file to review |
| `--stdin` | false | Read code from stdin instead of a file |
| `--model` | `sonnet` | Model to use: `sonnet` (default) or `opus` |
| `--focus` | (none) | Comma-separated focus areas for the reviewer |
| `--context` | (none) | Brief description of what the code does and why it matters |

### Output

Structured JSON to stdout. Logs status messages to stderr (so stdout stays parseable).

```json
{
  "filename": "pipeline.json",
  "review": {
    "approval_status": "approved | changes_requested | needs_discussion",
    "summary": "2-3 sentence assessment",
    "issues": [
      {
        "severity": "critical | major | minor | suggestion",
        "location": "function name or code reference",
        "description": "What's wrong",
        "fix": "How to fix it",
        "code_snippet": "suggested replacement code (optional)"
      }
    ],
    "missed_edge_cases": ["description of unhandled condition"],
    "positive_observations": ["what's solid about the code"]
  },
  "stats": {
    "total_issues": 4,
    "critical": 1,
    "major": 1,
    "minor": 1,
    "suggestions": 1
  },
  "model": "claude-sonnet-4-20250514",
  "reviewed_at": "2026-03-15T14:30:00.000Z"
}
```

---

## When to Request Review

### Always Review These (Non-Negotiable)

Request review before considering work complete on any of the following:

- **Scoring and evaluation pipeline files** — enrichment logic, weighted scoring, pre-scoring gates, disqualification tiers, sector detection
- **n8n workflow JSON files** after modifications that change data flow, add/remove nodes, or alter scoring calculations
- **Regex-heavy code** — sector detection patterns, keyword matching, negative lookahead logic, pattern-based gates
- **Airtable batch operations** — field mapping, record creation/update logic, batch processing loops
- **Any file where a subtle bug could silently produce wrong results** (false positives in pipeline, wrong disqualification, lost data)

### Use Opus (--model opus) When

- Changing scoring logic (weighted scores, gate thresholds, tier definitions)
- Architectural changes (new nodes, restructured data flow, changed pipeline shape)
- Touching 100+ lines in a single change
- Multi-file changes that affect how components interact
- The code involves complex conditional logic with many branches

### Use Sonnet (default) When

- Bug fixes, small refactors, single-function changes
- Adding new entries to existing pattern lists (PE firm names, sector keywords, job title patterns)
- Routine code cleanup, renaming, comment updates that touch logic
- Changes under 100 lines in a single file

### Skip Review When

- README, documentation, or comment-only changes
- Config changes that don't affect logic (display names, labels, descriptions)
- Whitespace, formatting, or linting fixes
- Files you've already reviewed in this session and haven't changed since

---

## How to Run a Review

### Step-by-step process for Claude Code:

1. **Finish the code change.** Don't review mid-edit. Complete the logical unit of work first.

2. **Determine review scope.** Which files changed? Do any hit the "always review" list above?

3. **Pick the model.** Opus for complex/high-stakes, Sonnet for routine. When in doubt, Sonnet is fine.

4. **Provide context.** Always pass `--context` with a brief description. The reviewer model has zero context about the project. A single sentence like "n8n Code node that enriches company data from web scraping and scores it against a 100-point job search fit model" makes the review dramatically better.

5. **Run the script.** Use the bash tool:
   ```bash
   node code-review.mjs ./path/to/changed-file.js --model sonnet --context "brief description" --focus "relevant concerns"
   ```

6. **Parse the output.** Read the JSON from stdout.

7. **Act on findings:**
   - **Critical or major issues:** Fix them. Then tell the user what was found and what you fixed.
   - **Minor issues or suggestions:** Report them to the user. Ask if they want them addressed.
   - **Approval with no issues:** Note that the review passed and move on.
   - **"needs_discussion" status:** Present the reviewer's concerns to the user for a decision.

8. **Optional follow-up review.** If you fixed critical/major issues, one follow-up review is fine to confirm the fix. Do not loop more than once.

---

## How to Report Review Results to the User

When reporting review findings, be direct:

**If issues were found and fixed:**
> Ran code review on `pipeline.json` using Opus 4.6. Found 1 critical issue (null reference in employee count gate) and 2 minor suggestions. Fixed the critical issue — changed the guard from `!employeeCount` to `employeeCount === null` to handle the `0` case. The minor suggestions are [describe]. Want me to address those too?

**If the review passed clean:**
> Ran code review on `scoring.js` using Sonnet. No issues found — approved.

**If the review flagged things worth discussing:**
> Code review on `enrichment.js` flagged a potential edge case: if the company description is an empty string (not null), all sector detection patterns fail silently and the company gets scored as "no sector detected" rather than erroring. The reviewer suggests adding an empty-string guard. Want me to add that?

Do NOT:
- Silently fix things without telling the user what the review found
- Skip reporting because the issues seem minor
- Rerun the review more than once after fixes (one follow-up max)
- Run review on files that didn't change

---

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `Error: ANTHROPIC_API_KEY not set` | Missing env var | Set `export ANTHROPIC_API_KEY=sk-ant-...` in your shell |
| `API error 429` | Rate limited | Wait 30 seconds and retry once |
| `API error 529` | API overloaded | Wait 60 seconds and retry once |
| `Error: API call timed out` | Large file or slow response | Try with `--model sonnet` or review a smaller section |
| `Parse error` in output | Model didn't return clean JSON | The `raw_response` field will contain what it said; read that for useful feedback even if structured parsing failed |
| Review seems shallow or generic | Missing context | Always pass `--context` with what the code does and why it matters |

---

## Cost Awareness

| Model | Input (1M tokens) | Output (1M tokens) | Typical review cost |
|-------|-------------------|---------------------|-------------------|
| Sonnet 4 | $3 | $15 | ~$0.02-0.05 |
| Opus 4.6 | $5 | $25 | ~$0.03-0.10 |

A typical file review (500-2000 lines) costs a few cents with Sonnet and under $0.10 with Opus. Default to Sonnet. The cost difference is ~2x and Sonnet catches the majority of bugs. Save Opus for the files where subtle logic errors have real consequences.

---

## Example: Reviewing a Tide Pool Pipeline Change

```bash
# After modifying the enrichment and scoring pipeline
node code-review.mjs "./Enrich & Evaluate Pipeline v9.7.json" \
  --model opus \
  --focus "scoring logic,disqualification gates,null handling,regex patterns" \
  --context "n8n workflow JSON for Tide Pool job search pipeline. Enriches companies from VC portfolio scraping, scores them on a 100-point weighted system with binary pre-scoring gates (funding cap, employee count, PE flag, customer persona, business model). Changes in this version: added developer-as-customer persona gate and adjusted sector detection regex."
```

This gives the reviewer enough context to understand what correct behavior looks like, which is the difference between a useful review and a generic one.
