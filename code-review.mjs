#!/usr/bin/env node

/**
 * code-review.mjs (v2)
 * 
 * Sends code to Opus 4.6 (or Sonnet) for structured review with
 * automatic project context injection via review profiles.
 *
 * Usage:
 *   node code-review.mjs <file> [options]
 *   node code-review.mjs <file1> <file2> [options]    # multi-file
 *   cat file.js | node code-review.mjs --stdin [options]
 *
 * Options:
 *   --model opus|sonnet    Model to use (default: sonnet)
 *   --profile <name>       Context profile: pipeline, scraper, rescore, dedup, job-eval, general
 *   --focus "a,b,c"        Comma-separated focus areas
 *   --context "..."        Manual context (overrides profile)
 *   --log                  Save review to ./review-logs/
 *   --diff                 Include git diff for the file alongside full content
 *   --stdin                Read code from stdin
 *
 * Examples:
 *   node code-review.mjs ./pipeline.json --model opus --profile pipeline --log
 *   node code-review.mjs ./scraper.json ./pipeline.json --profile scraper --focus "dedup,data handoff"
 *   git diff --staged | node code-review.mjs --stdin --profile pipeline
 *
 * Requires: ANTHROPIC_API_KEY environment variable
 */

import { readFileSync, writeFileSync, mkdirSync, existsSync, readdirSync } from 'fs';
import { basename, join, resolve } from 'path';
import { execSync } from 'child_process';

// --- Configuration ---

const MODELS = {
  opus:   'claude-opus-4-6',
  sonnet: 'claude-sonnet-4-6',
};

const DEFAULT_MODEL = 'sonnet';
const MAX_CODE_CHARS = 80_000;
const API_TIMEOUT_MS = 180_000;  // 3 minutes
const PROFILE_DIR = './review-profiles';
const LOG_DIR = './review-logs';

// --- Profile Auto-Detection ---

const PROFILE_PATTERNS = {
  pipeline:  /enrich.*evaluate|pipeline\s*v9|v9\.\d+|pre-brave|phase\s*[0-5]/i,
  scraper:   /vc\s*scraper|scraper.*v\d|browserless|portfolio/i,
  rescore:   /rescore|v4\.\d+|config.*fetcher|config.*driven/i,
  dedup:     /dedup|seen.*opportunities|duplicate/i,
  'job-eval': /job.*eval|job.*pipeline|v6\.\d+|job.*alert|job.*listing/i,
};

function detectProfile(filename, codePreview) {
  const combined = `${filename} ${codePreview}`;
  for (const [profile, pattern] of Object.entries(PROFILE_PATTERNS)) {
    if (pattern.test(combined)) return profile;
  }
  return 'general';
}

function loadProfile(profileName) {
  const profilePath = join(PROFILE_DIR, `${profileName}.md`);
  if (!existsSync(profilePath)) {
    console.error(`Warning: Profile '${profileName}' not found at ${profilePath}. Using no profile.`);
    console.error(`  Run: node generate-review-profiles.mjs`);
    return null;
  }
  const content = readFileSync(profilePath, 'utf-8');
  const tokens = Math.ceil(content.length / 4);
  if (tokens > 4000) {
    console.error(`Warning: Profile '${profileName}' is ~${tokens} tokens. Consider trimming.`);
  }
  return { content, tokens, name: profileName };
}

// --- Parse Args ---

function parseArgs() {
  const args = process.argv.slice(2);
  const opts = {
    files: [],
    stdin: false,
    model: DEFAULT_MODEL,
    focus: [],
    context: '',
    profile: null,    // explicit profile name or null for auto-detect
    log: false,
    diff: false,
  };

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg === '--stdin') {
      opts.stdin = true;
    } else if (arg === '--model' && args[i + 1]) {
      opts.model = args[++i].toLowerCase();
    } else if (arg === '--focus' && args[i + 1]) {
      opts.focus = args[++i].split(',').map(s => s.trim());
    } else if (arg === '--context' && args[i + 1]) {
      opts.context = args[++i];
    } else if (arg === '--profile' && args[i + 1]) {
      opts.profile = args[++i].toLowerCase();
    } else if (arg === '--log') {
      opts.log = true;
    } else if (arg === '--diff') {
      opts.diff = true;
    } else if (!arg.startsWith('--')) {
      opts.files.push(arg);
    }
  }

  return opts;
}

// --- Read Input ---

function readCode(opts) {
  const entries = [];

  if (opts.stdin) {
    let code = readFileSync('/dev/stdin', 'utf-8');
    if (code.length > MAX_CODE_CHARS) {
      console.error(`Warning: stdin truncated (${code.length - MAX_CODE_CHARS} chars removed).`);
      code = code.substring(0, MAX_CODE_CHARS);
    }
    entries.push({ code, filename: 'stdin', diff: null });
  } else if (opts.files.length > 0) {
    let totalChars = 0;
    for (const file of opts.files) {
      let code = readFileSync(file, 'utf-8');
      totalChars += code.length;

      if (totalChars > MAX_CODE_CHARS) {
        const allowed = MAX_CODE_CHARS - (totalChars - code.length);
        if (allowed <= 0) {
          console.error(`Warning: Skipping ${file} (total code exceeds ${MAX_CODE_CHARS} chars).`);
          continue;
        }
        code = code.substring(0, allowed);
        console.error(`Warning: ${file} truncated to fit within char limit.`);
      }

      let diff = null;
      if (opts.diff) {
        try {
          diff = execSync(`git diff HEAD -- "${resolve(file)}"`, { encoding: 'utf-8', timeout: 5000 });
          if (!diff.trim()) diff = null;
        } catch {
          // Not in a git repo or file not tracked -- skip diff silently
        }
      }

      entries.push({ code, filename: basename(file), diff });
    }
  } else {
    console.error('Error: Provide file path(s) or --stdin');
    process.exit(1);
  }

  if (entries.length === 0) {
    console.error('Error: No code to review.');
    process.exit(1);
  }

  return entries;
}

// --- Build Prompt ---

function buildPrompt(entries, context, focusAreas, profile) {
  let systemParts = [`You are a senior code reviewer. Review the provided code and return ONLY valid JSON with no other text.

REVIEW PRIORITIES:
1. Bugs & Logic Errors - null/undefined handling, off-by-one, incorrect regex, type coercion
2. Edge Cases - boundary conditions, empty inputs, unexpected data shapes
3. Data Loss Risks - silent failures, swallowed errors, missing fallbacks
4. Performance - unnecessary iteration, regex backtracking, unbounded operations
5. Maintainability - magic numbers, unclear naming, repeated patterns

SEVERITY:
- critical: Will cause failures or data loss. Must fix.
- major: Significant bug or flaw. Fix before shipping.
- minor: Small improvement. Fix when convenient.
- suggestion: Optional style or optimization idea.`];

  // Inject profile context
  if (profile) {
    systemParts.push(`\nPROJECT CONTEXT (from review profile: ${profile.name}):\n${profile.content}`);
    systemParts.push(`\nIMPORTANT: Check this code against the known bugs listed above. If this code interacts with any known bug, flag it as critical.`);
  }

  systemParts.push(`
JSON RESPONSE FORMAT:
{
  "approval_status": "approved" | "changes_requested" | "needs_discussion",
  "summary": "2-3 sentence assessment",
  "issues": [
    {
      "severity": "critical|major|minor|suggestion",
      "location": "function name, line description, or code reference",
      "description": "What's wrong",
      "fix": "How to fix it",
      "code_snippet": "suggested replacement (optional)"
    }
  ],
  "missed_edge_cases": ["edge case 1"],
  "positive_observations": ["what's solid"]${profile ? ',\n  "known_bug_check": ["for each known bug in the profile, state whether this code is affected"]' : ''}
}`);

  const system = systemParts.join('\n');

  // Build user message
  const userParts = ['Review this code:'];

  const focusBlock = focusAreas.length > 0
    ? `\nPRIORITY FOCUS AREAS:\n- ${focusAreas.join('\n- ')}`
    : '';

  const contextBlock = context
    ? `\nADDITIONAL CONTEXT: ${context}`
    : '';

  userParts.push(contextBlock);
  userParts.push(focusBlock);

  for (const entry of entries) {
    userParts.push(`\nFILENAME: ${entry.filename}`);
    userParts.push(`\n\`\`\`\n${entry.code}\n\`\`\``);

    if (entry.diff) {
      userParts.push(`\nGIT DIFF (what changed):\n\`\`\`diff\n${entry.diff}\n\`\`\``);
    }
  }

  userParts.push('\nReturn your review as JSON only.');

  return { system, user: userParts.join('\n') };
}

// --- Call Anthropic API ---

async function callAPI(system, user, model) {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    console.error('Error: ANTHROPIC_API_KEY not set');
    process.exit(1);
  }

  const modelId = MODELS[model] || MODELS[DEFAULT_MODEL];

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), API_TIMEOUT_MS);

  try {
    const res = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
        'content-type': 'application/json',
      },
      body: JSON.stringify({
        model: modelId,
        max_tokens: 4096,
        system,
        messages: [{ role: 'user', content: user }],
      }),
      signal: controller.signal,
    });

    clearTimeout(timeout);

    if (!res.ok) {
      const errBody = await res.text();
      console.error(`API error ${res.status}: ${errBody}`);
      process.exit(1);
    }

    return await res.json();
  } catch (e) {
    clearTimeout(timeout);
    if (e.name === 'AbortError') {
      console.error('Error: API call timed out');
    } else {
      console.error(`Error: ${e.message}`);
    }
    process.exit(1);
  }
}

// --- Parse Response ---

function parseReview(apiResponse) {
  const content = apiResponse.content?.[0]?.text || '';

  let jsonStr = content;

  // Strip markdown code blocks if present
  const codeBlock = content.match(/```(?:json)?\s*([\s\S]*?)```/);
  if (codeBlock) {
    jsonStr = codeBlock[1];
  } else {
    const jsonMatch = content.match(/\{[\s\S]*\}/);
    if (jsonMatch) jsonStr = jsonMatch[0];
  }

  // Clean trailing commas
  jsonStr = jsonStr
    .replace(/,\s*}/g, '}')
    .replace(/,\s*]/g, ']')
    .trim();

  try {
    return JSON.parse(jsonStr);
  } catch (e) {
    return {
      approval_status: 'error',
      summary: `Failed to parse review JSON: ${e.message}`,
      raw_response: content.substring(0, 3000),
      issues: [],
      missed_edge_cases: [],
      positive_observations: [],
    };
  }
}

// --- Format Output ---

function formatOutput(review, filenames, model, profile) {
  const counts = { critical: 0, major: 0, minor: 0, suggestion: 0 };
  for (const issue of review.issues || []) {
    if (counts[issue.severity] !== undefined) counts[issue.severity]++;
  }

  return {
    filename: filenames.length === 1 ? filenames[0] : filenames,
    profile_used: profile ? profile.name : null,
    review,
    stats: {
      total_issues: (review.issues || []).length,
      ...counts,
    },
    model: MODELS[model] || model,
    context_tokens: profile ? profile.tokens : 0,
    reviewed_at: new Date().toISOString(),
  };
}

// --- Logging ---

function saveLog(output) {
  if (!existsSync(LOG_DIR)) {
    mkdirSync(LOG_DIR, { recursive: true });
  }

  const ts = new Date().toISOString().replace(/[:.]/g, '-');
  const name = Array.isArray(output.filename)
    ? output.filename[0]
    : output.filename;
  const safeName = name.replace(/[^a-zA-Z0-9_.-]/g, '_');
  const logPath = join(LOG_DIR, `${ts}-${safeName}.json`);

  writeFileSync(logPath, JSON.stringify(output, null, 2), 'utf-8');
  console.error(`Review logged to ${logPath}`);
}

// --- Main ---

async function main() {
  const opts = parseArgs();
  const entries = readCode(opts);

  // Resolve profile: explicit > auto-detect > none
  let profile = null;
  if (!opts.context) {
    // Only use profiles when no manual --context override
    const profileName = opts.profile
      || detectProfile(
          entries.map(e => e.filename).join(' '),
          entries[0].code.substring(0, 500)
        );

    if (existsSync(PROFILE_DIR)) {
      profile = loadProfile(profileName);
    } else if (opts.profile) {
      console.error(`Warning: Profile directory ${PROFILE_DIR} not found.`);
      console.error(`  Run: node generate-review-profiles.mjs`);
    }
    // If no profile dir exists and no explicit --profile, just proceed without context (v1 behavior)
  }

  const filenames = entries.map(e => e.filename);
  const { system, user } = buildPrompt(entries, opts.context, opts.focus, profile);

  // Log to stderr so stdout stays clean JSON
  const profileNote = profile ? ` (${profile.name} profile, ~${profile.tokens} tokens)` : '';
  console.error(`Reviewing ${filenames.join(', ')} with ${opts.model}${profileNote}...`);

  const apiResponse = await callAPI(system, user, opts.model);
  const review = parseReview(apiResponse);
  const output = formatOutput(review, filenames, opts.model, profile);

  // Save log if requested
  if (opts.log) {
    saveLog(output);
  }

  // Structured JSON to stdout
  console.log(JSON.stringify(output, null, 2));
}

main();
