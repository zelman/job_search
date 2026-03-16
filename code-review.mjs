#!/usr/bin/env node

/**
 * code-review.mjs
 * 
 * Sends code to Opus 4.6 (or Sonnet) for structured review.
 * Designed to be called by Claude Code via shell command.
 *
 * Usage:
 *   node code-review.mjs <file> [--model opus|sonnet] [--focus areas] [--context "..."]
 *   cat file.js | node code-review.mjs --stdin [--model opus|sonnet]
 *
 * Examples:
 *   node code-review.mjs ./pipeline.json --model opus --focus "scoring logic,edge cases"
 *   node code-review.mjs ./enrichment.js --context "n8n Code node for company enrichment"
 *   git diff --staged | node code-review.mjs --stdin --context "staged changes"
 *
 * Requires: ANTHROPIC_API_KEY environment variable
 */

import { readFileSync } from 'fs';
import { basename } from 'path';

// --- Configuration ---

const MODELS = {
  opus:   'claude-opus-4-6',
  sonnet: 'claude-sonnet-4-20250514',
};

const DEFAULT_MODEL = 'sonnet'; // Sonnet for routine reviews, pass --model opus for heavy lifts
const MAX_CODE_CHARS = 80_000;  // Guard against token blowout on large files
const API_TIMEOUT_MS = 180_000; // 3 minutes for Opus on large reviews

// --- Parse Args ---

function parseArgs() {
  const args = process.argv.slice(2);
  const opts = {
    file: null,
    stdin: false,
    model: DEFAULT_MODEL,
    focus: [],
    context: '',
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
    } else if (!arg.startsWith('--')) {
      opts.file = arg;
    }
  }

  return opts;
}

// --- Read Input ---

function readCode(opts) {
  let code, filename;

  if (opts.stdin) {
    code = readFileSync('/dev/stdin', 'utf-8');
    filename = 'stdin';
  } else if (opts.file) {
    code = readFileSync(opts.file, 'utf-8');
    filename = basename(opts.file);
  } else {
    console.error('Error: Provide a file path or --stdin');
    process.exit(1);
  }

  if (code.length > MAX_CODE_CHARS) {
    const truncated = code.length - MAX_CODE_CHARS;
    code = code.substring(0, MAX_CODE_CHARS);
    console.error(`Warning: Code truncated (${truncated} chars removed). Consider reviewing in sections.`);
  }

  return { code, filename };
}

// --- Build Prompt ---

function buildPrompt(code, filename, context, focusAreas) {
  const system = `You are a senior code reviewer. Review the provided code and return ONLY valid JSON with no other text.

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
- suggestion: Optional style or optimization idea.

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
  "positive_observations": ["what's solid"]
}`;

  const focusBlock = focusAreas.length > 0
    ? `\n\nPRIORITY FOCUS AREAS:\n- ${focusAreas.join('\n- ')}`
    : '';

  const contextBlock = context
    ? `\nCONTEXT: ${context}`
    : '';

  const user = `Review this code:

FILENAME: ${filename}${contextBlock}${focusBlock}

\`\`\`
${code}
\`\`\`

Return your review as JSON only.`;

  return { system, user };
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

function formatOutput(review, filename, model) {
  const usage = {
    model: MODELS[model] || model,
  };

  // Count by severity
  const counts = { critical: 0, major: 0, minor: 0, suggestion: 0 };
  for (const issue of review.issues || []) {
    if (counts[issue.severity] !== undefined) counts[issue.severity]++;
  }

  return JSON.stringify({
    filename,
    review,
    stats: {
      total_issues: (review.issues || []).length,
      ...counts,
    },
    ...usage,
    reviewed_at: new Date().toISOString(),
  }, null, 2);
}

// --- Main ---

async function main() {
  const opts = parseArgs();
  const { code, filename } = readCode(opts);
  const { system, user } = buildPrompt(code, filename, opts.context, opts.focus);

  // Log to stderr so stdout stays clean JSON for Claude Code to parse
  console.error(`Reviewing ${filename} with ${opts.model}...`);

  const apiResponse = await callAPI(system, user, opts.model);
  const review = parseReview(apiResponse);
  const output = formatOutput(review, filename, opts.model);

  // Structured JSON to stdout
  console.log(output);
}

main();
