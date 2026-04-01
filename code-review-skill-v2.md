# Skill: Code Review via External Model (v2)

## Purpose

This skill enables Claude Code to request independent code review from a different Claude model (Opus 4.6 or Sonnet 4) by shelling out to a local script. Use it to catch bugs, edge cases, scoring logic errors, and architectural issues that a single-model pass can miss.

**v2 additions:** Auto-context injection from project files, context profiles for different review types, multi-file support, and review logging.

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
2. **Auto-select the context profile** based on the file type (see Context Profiles below)
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

## Context Profiles (v2 NEW)

### The Problem This Solves

The reviewing model has zero project context. A one-line `--context` flag can't convey scoring thresholds, known bugs, architecture decisions, or the dedup pattern the code should follow. This is why reviews are sometimes generic or miss project-specific issues.

### How It Works

The `--profile` flag tells the script to read specific sections from project files and prepend them to the review prompt. The reviewer gets the same architectural understanding that Claude Code gets from CLAUDE.md, without the user manually copying context.

### Available Profiles

| Profile | Flag | Auto-detected when | What gets injected |
|---------|------|--------------------|--------------------|
| `pipeline` | `--profile pipeline` | File contains "Enrich & Evaluate" or "v9" or "v6" | Scoring architecture, gate tiers, domain distance table, known bugs, current thresholds from SCORING-THRESHOLDS.md |
| `scraper` | `--profile scraper` | File contains "VC Scraper" or "Scraper" | Scraper inventory (dedup status per scraper), dual-source dedup pattern, dedup register bug, pipeline integration points |
| `rescore` | `--profile rescore` | File contains "Rescore" or "v4" | Config-driven architecture, Airtable Config table schema, isRescore bug history, threshold alignment rules |
| `dedup` | `--profile dedup` | File contains "Dedup" | Dedup key format, Seen Opportunities schema, dedup register bug, dual-source workaround |
| `job-eval` | `--profile job-eval` | File contains "Job Evaluation" or "Job Alert" | Job scoring dimensions, JD fetch architecture, pre-scoring gates, NRR detection |
| `general` | `--profile general` | Default fallback | Project summary, Airtable schema, workflow ID table, candidate profile |

### Auto-Detection

When `--profile` is not specified, the script reads the filename and first 500 characters of the file to auto-select the most relevant profile. Claude Code can also explicitly specify the profile when the auto-detection might be wrong.

### Profile File Structure

Profiles are defined in `./review-profiles/` directory. Each profile is a markdown file containing the context sections to inject.

```
review-profiles/
  pipeline.md      # Scoring architecture, gates, thresholds, known bugs
  scraper.md       # Scraper inventory, dedup status, dedup pattern
  rescore.md       # Config-driven architecture, Airtable config schema
  dedup.md         # Key format, Seen Opportunities, known bugs
  job-eval.md      # Job scoring, JD fetch, pre-scoring
  general.md       # Project overview, Airtable schema, workflow IDs
```

These files are assembled from CLAUDE.md and SCORING-THRESHOLDS.md sections. They're static extracts, not dynamic reads, so they need to be regenerated when CLAUDE.md changes significantly. A helper script handles this:

```bash
# Regenerate all profiles from current CLAUDE.md and SCORING-THRESHOLDS.md
node generate-review-profiles.mjs
```

### Token Budget

Each profile is capped at ~3,000 tokens of context to keep review costs reasonable. Profiles should contain architectural facts and known bugs, not changelog history. The script warns if a profile exceeds 4,000 tokens.

---

## Script Reference: code-review.mjs

### Location
`./code-review.mjs` (project root)

### Usage

```bash
# Review a file with auto-detected profile (NEW)
node code-review.mjs ./path/to/file.js

# Review with explicit profile
node code-review.mjs ./path/to/file.js --profile pipeline

# Review with Opus + profile + focus
node code-review.mjs "./Enrich & Evaluate Pipeline v9.17.json" \
  --model opus \
  --profile pipeline \
  --focus "pre-brave gate logic,null handling"

# Review with manual context (overrides profile)
node code-review.mjs ./path/to/file.js --context "custom context here"

# Review multiple files together (NEW)
node code-review.mjs ./scoring.js ./enrichment.js --profile pipeline --focus "data flow between files"

# Review staged git changes via stdin
git diff --staged | node code-review.mjs --stdin --profile pipeline --context "staged changes to enrichment pipeline"

# Review with logging (NEW)
node code-review.mjs ./pipeline.json --model opus --profile pipeline --log
```

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `<file>` | (required unless --stdin) | Path to the file(s) to review. Accepts multiple paths. |
| `--stdin` | false | Read code from stdin instead of a file |
| `--model` | `sonnet` | Model to use: `sonnet` (default) or `opus` |
| `--profile` | (auto-detect) | Context profile to inject: `pipeline`, `scraper`, `rescore`, `dedup`, `job-eval`, `general` |
| `--focus` | (none) | Comma-separated focus areas for the reviewer |
| `--context` | (none) | Manual context string. Overrides profile if both specified. |
| `--log` | false | Save review results to `./review-logs/` with timestamp |
| `--diff` | false | When reviewing a file, also include the git diff for that file (shows what changed, not just current state) |

### Output

Structured JSON to stdout. Logs status messages to stderr (so stdout stays parseable).

```json
{
  "filename": "pipeline.json",
  "profile_used": "pipeline",
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
    "positive_observations": ["what's solid about the code"],
    "known_bug_check": ["checked against known bugs in profile: dedup register, isRescore, etc."]
  },
  "stats": {
    "total_issues": 4,
    "critical": 1,
    "major": 1,
    "minor": 1,
    "suggestions": 1
  },
  "model": "claude-sonnet-4-20250514",
  "context_tokens": 2847,
  "reviewed_at": "2026-04-01T14:30:00.000Z"
}
```

**v2 additions in output:**
- `profile_used` -- which context profile was injected
- `known_bug_check` -- reviewer explicitly checks against known bugs listed in the profile
- `context_tokens` -- how many tokens of profile context were injected (for cost tracking)

---

## Review Logging (v2 NEW)

When `--log` is passed, the script saves the full review JSON to `./review-logs/{timestamp}-{filename}.json`.

This serves two purposes:
1. **Session wrap-ups** -- Claude Code can read the log directory to summarize what was reviewed and what was found
2. **Review history** -- Track whether the same issues keep recurring (pattern detection)

The log directory is gitignored by default. Add `review-logs/` to `.gitignore`.

---

## When to Request Review

### Always Review These (Non-Negotiable)

Request review before considering work complete on any of the following:

- **Scoring and evaluation pipeline files** -- enrichment logic, weighted scoring, pre-scoring gates, disqualification tiers, sector detection. **Use `--profile pipeline`.**
- **VC scraper files** after modifications that change scraping targets, dedup logic, or merge chains. **Use `--profile scraper`.**
- **n8n workflow JSON files** after modifications that change data flow, add/remove nodes, or alter scoring calculations
- **Regex-heavy code** -- sector detection patterns, keyword matching, negative lookahead logic, pattern-based gates
- **Airtable batch operations** -- field mapping, record creation/update logic, batch processing loops
- **Dedup-related code** -- any changes to dedup check, dedup register, or scraper-level filtering. **Use `--profile dedup`.**
- **Any file where a subtle bug could silently produce wrong results** (false positives in pipeline, wrong disqualification, lost data)

### Use Opus (--model opus) When

- Changing scoring logic (weighted scores, gate thresholds, tier definitions)
- Architectural changes (new nodes, restructured data flow, changed pipeline shape)
- Touching 100+ lines in a single change
- Multi-file changes that affect how components interact
- The code involves complex conditional logic with many branches
- **Changes that interact with known bugs** (dedup register, isRescore, Airtable batch node)

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

4. **Let the profile handle context.** The `--profile` flag (or auto-detection) injects the right project context. Only use `--context` for additional information the profile doesn't cover (e.g., "this is a new pattern we haven't used before" or "the user specifically asked for X approach").

5. **Add focus areas from the current session.** If you just fixed a dedup bug, add `--focus "dedup key generation,null company names,duplicate detection"`. The focus should reflect what you actually changed, not generic concerns.

6. **Run the script.** Use the bash tool:
   ```bash
   node code-review.mjs ./path/to/changed-file.js \
     --model sonnet \
     --profile pipeline \
     --focus "relevant concerns from this session" \
     --log
   ```

7. **Parse the output.** Read the JSON from stdout.

8. **Check `known_bug_check`.** The reviewer explicitly verifies against known bugs in the profile. If it flags a known bug interaction, treat it as critical.

9. **Act on findings:**
   - **Critical or major issues:** Fix them. Then tell the user what was found and what you fixed.
   - **Minor issues or suggestions:** Report them to the user. Ask if they want them addressed.
   - **Approval with no issues:** Note that the review passed and move on.
   - **"needs_discussion" status:** Present the reviewer's concerns to the user for a decision.

10. **Optional follow-up review.** If you fixed critical/major issues, one follow-up review is fine to confirm the fix. Do not loop more than once.

---

## How to Report Review Results to the User

When reporting review findings, be direct:

**If issues were found and fixed:**
> Ran code review on `pipeline.json` using Opus 4.6 (pipeline profile, 2.8K tokens of context). Found 1 critical issue (null reference in employee count gate) and 2 minor suggestions. Fixed the critical issue -- changed the guard from `!employeeCount` to `employeeCount === null` to handle the `0` case. The minor suggestions are [describe]. Want me to address those too?

**If the review passed clean:**
> Ran code review on `scoring.js` using Sonnet (pipeline profile). No issues found -- approved.

**If the review flagged a known bug interaction:**
> Code review on `scraper.js` flagged that this code writes to the Dedup Register subworkflow, which has a known bug (not writing to Seen Opportunities). The reviewer recommends adding the dual-source dedup pattern at the scraper level as a workaround. Want me to implement that?

**If the review flagged things worth discussing:**
> Code review on `enrichment.js` flagged a potential edge case: if the company description is an empty string (not null), all sector detection patterns fail silently and the company gets scored as "no sector detected" rather than erroring. The reviewer suggests adding an empty-string guard. Want me to add that?

Do NOT:
- Silently fix things without telling the user what the review found
- Skip reporting because the issues seem minor
- Rerun the review more than once after fixes (one follow-up max)
- Run review on files that didn't change
- Omit the profile used and context token count from the report

---

## Context Profile Generation

### Initial Setup

Run once to create the profile directory and generate profiles from your current CLAUDE.md:

```bash
mkdir -p review-profiles review-logs
echo "review-logs/" >> .gitignore
node generate-review-profiles.mjs
```

### Regeneration

Run after significant CLAUDE.md updates (new bugs discovered, architecture changes, threshold changes):

```bash
node generate-review-profiles.mjs
```

The generator reads CLAUDE.md and SCORING-THRESHOLDS.md, extracts the relevant sections for each profile, and writes them to `review-profiles/`. Each profile is a focused subset -- not the entire CLAUDE.md.

### What Goes in Each Profile

**pipeline.md** (~2,500 tokens target):
- v9 architecture overview (6-phase flow)
- Scoring dimensions and point allocations
- Domain distance table
- Pre-Brave gate summary (v9.17)
- Gate tier definitions (hard, sector, GTM, stale, soft)
- Current thresholds from SCORING-THRESHOLDS.md
- Known bugs: dedup register, Airtable batch node, isRescore
- Candidate profile (what "good fit" means)

**scraper.md** (~2,000 tokens target):
- VC scraper inventory table (IDs, dedup status, signal rates)
- Dual-source dedup pattern (template code)
- Dedup register bug description
- How scrapers connect to the E&E pipeline
- Pre-Brave gate (what gets filtered before Brave)

**rescore.md** (~1,500 tokens target):
- Config-driven architecture (Airtable Config table)
- Config key/value reference
- PE Firms table schema
- isRescore bug and fix (v4.15)
- HTTP Request bypass pattern for Airtable updates

**dedup.md** (~1,500 tokens target):
- Key generation format (company: and job: prefixes)
- Seen Opportunities table schema
- Dedup register bug (not writing to table)
- Dual-source workaround pattern
- Cross-source dedup flow

**job-eval.md** (~2,000 tokens target):
- Job scoring dimensions (rebalanced in v6.3)
- JD fetch architecture (Browserless fallback)
- Pre-scoring gates (NRR, IT support, scale signals)
- Developer-as-customer persona gate
- Sector detection patterns

**general.md** (~1,500 tokens target):
- One-paragraph project summary
- Airtable base and table IDs
- Workflow ID table
- Candidate profile summary
- Hard rules (never claim)

---

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `Error: ANTHROPIC_API_KEY not set` | Missing env var | Set `export ANTHROPIC_API_KEY=sk-ant-...` in your shell |
| `API error 429` | Rate limited | Wait 30 seconds and retry once |
| `API error 529` | API overloaded | Wait 60 seconds and retry once |
| `Error: API call timed out` | Large file or slow response | Try with `--model sonnet` or review a smaller section |
| `Parse error` in output | Model didn't return clean JSON | The `raw_response` field will contain what it said; read that for useful feedback even if structured parsing failed |
| Review seems shallow or generic | Missing context | Check that `--profile` is being used. If auto-detection picked `general`, try an explicit profile. |
| `Profile file not found` | Profiles not generated | Run `node generate-review-profiles.mjs` |
| `Warning: profile exceeds 4000 tokens` | Profile too long | Edit the profile in `review-profiles/` to trim changelog or history sections |
| Review misses project-specific issues | Profile is stale | Regenerate profiles: `node generate-review-profiles.mjs` |

---

## Cost Awareness

| Model | Input (1M tokens) | Output (1M tokens) | Typical review cost (with profile) |
|-------|-------------------|---------------------|-----------------------------------|
| Sonnet 4 | $3 | $15 | ~$0.03-0.06 |
| Opus 4.6 | $5 | $25 | ~$0.05-0.12 |

Profile injection adds ~2,000-3,000 tokens of input per review. At Sonnet rates, that's less than $0.01 additional cost. The improvement in review quality far exceeds the cost.

---

## Example: Reviewing a Tide Pool Pipeline Change (v2)

```bash
# After modifying the enrichment and scoring pipeline
# Profile auto-detects as "pipeline" from filename
node code-review.mjs "./Enrich & Evaluate Pipeline v9.17.json" \
  --model opus \
  --focus "pre-brave gate logic,null handling,dedup interaction" \
  --log

# After adding dedup to a scraper
node code-review.mjs "./VC Scraper - Healthcare v28.json" \
  --model sonnet \
  --profile scraper \
  --focus "dual-source dedup pattern,key normalization,merge chain integrity" \
  --log

# Multi-file review: scraper + pipeline interaction
node code-review.mjs "./VC Scraper - Healthcare v28.json" "./Enrich & Evaluate Pipeline v9.17.json" \
  --model opus \
  --profile scraper \
  --focus "data handoff between scraper and pipeline,field naming consistency" \
  --log
```

This gives the reviewer the scoring architecture, known bugs, current thresholds, and dedup status -- the same context this project has in Claude.ai -- without the user copying anything.
