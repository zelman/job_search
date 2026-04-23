#!/usr/bin/env python3
"""
Update Funding Alerts Rescore from v4.15 to v5.0
Implements all threshold changes from SCORING-THRESHOLDS.md
"""

import json
import re

def update_parse_enrich_code(code):
    """Update Parse Enrich node with v10/v5 thresholds and logic"""

    # Add version comment
    version_comment = """// v5.0: MAJOR APERTURE WIDENING - synced with Pipeline v10.0
// - Employee hard cap 150→1000, soft cap 100→200, heavy penalty 300
// - Funding hard cap $75M→$200M, soft cap $200M-$500M
// - Series C no longer auto-DQ if <300 employees
// - Incomplete data scores WATCH instead of DQ
// - Title gate context-dependent by company size
// - Builder phrase override: +15 pts
//
"""

    # Insert version comment at the beginning
    if "// v5.0:" not in code:
        code = version_comment + code

    # Add builder phrase detection if not already present
    if "BUILDER_PHRASES" not in code:
        builder_phrase_code = """
// v5.0 NEW: Builder phrase detection
const BUILDER_PHRASES = [
  /build\\s+from\\s+(scratch|the\\s+ground\\s+up)/i,
  /first\\s+(hire|cs|customer\\s+success|support)/i,
  /\\bfounding\\b/i,
  /\\bgreenfield\\b/i,
  /\\b(0|zero)\\s*(-|to)\\s*(1|one)\\b/i,
  /stand\\s+up\\s+(the\\s+)?(function|team|org)/i,
  /establish\\s+(the\\s+)?(team|function|org)/i,
  /no\\s+existing\\s+(cs\\s+)?team/i,
  /first\\s+customer[- ]facing\\s+hire/i,
  /define\\s+(the\\s+)?playbook/i,
  /create\\s+(the\\s+)?process/i
];

const allSearchText = (enrichData.description || '') + ' ' + (enrichData.company_name || '');
const hasBuilderPhrase = BUILDER_PHRASES.some(p => p.test(allSearchText));
const builderPhraseBonus = hasBuilderPhrase ? 15 : 0;

// v5.0 NEW: Title tier detection
const TITLE_PATTERNS = {
  executive: /\\b(VP|Vice President|Head of|Director)\\b/i,
  seniorManager: /\\b(Senior Manager|Lead|Principal)\\b/i,
  manager: /\\b(Manager|CSM|Customer Success Manager)\\b/i,
  ic: /\\b(Specialist|Associate|Coordinator|Representative|Agent|Analyst)\\b/i
};

let detectedTitleTier = 'unknown';
if (TITLE_PATTERNS.executive.test(allSearchText)) detectedTitleTier = 'executive';
else if (TITLE_PATTERNS.seniorManager.test(allSearchText)) detectedTitleTier = 'seniorManager';
else if (TITLE_PATTERNS.manager.test(allSearchText)) detectedTitleTier = 'manager';
else if (TITLE_PATTERNS.ic.test(allSearchText)) detectedTitleTier = 'ic';

// v5.0 NEW: Title penalty calculation
let titlePenalty = 0;
if (!hasBuilderPhrase) {
  const emp = employeeCount || 0;
  if (detectedTitleTier === 'seniorManager') {
    if (emp >= 300) titlePenalty = -10;
    else if (emp >= 150) titlePenalty = -5;
  } else if (detectedTitleTier === 'manager') {
    if (emp >= 300) titlePenalty = -15;
    else if (emp >= 150) titlePenalty = -10;
    else if (emp >= 50) titlePenalty = -5;
  } else if (detectedTitleTier === 'ic') {
    if (emp >= 300) {
      // IC at 300+ = auto-DQ
      dqReasons.push('IC title at large company (auto-DQ)');
    } else if (emp >= 150) titlePenalty = -15;
    else if (emp >= 50) titlePenalty = -10;
    else titlePenalty = -5;
  }
}

"""
        # Insert after config parsing section
        if "const config = configData.config" in code:
            code = code.replace(
                "const config = configData.config",
                "const config = configData.config\n" + builder_phrase_code
            )

    # Update employee cap check - from hardcoded 150 to config-driven 1000
    code = re.sub(
        r"employeeCount\s*>\s*150",
        "employeeCount > (config.HARD_EMPLOYEE_CAP || 1000)",
        code
    )

    # Update funding cap check - from $75M to $200M
    code = re.sub(
        r"totalFunding\s*>\s*75000000",
        "totalFunding > (config.HARD_FUNDING_CAP || 200000000)",
        code
    )

    # Update Series C handling - add manual review path
    old_series_c = "if (/series\\s*c/i.test(stage)) dqReasons.push('Series C');"
    new_series_c = """// v5.0: Series C manual review path
if (/series\\s*c/i.test(stage)) {
  if (employeeCount && employeeCount < 300) {
    // Don't DQ - flag for manual review
    console.log('Series C but small (' + employeeCount + ' emp) — manual review');
  } else {
    dqReasons.push('Series C at scale (' + (employeeCount || '?') + ' employees)');
  }
}"""
    code = code.replace(old_series_c, new_series_c)

    # Add v5.0 output fields
    if "has_builder_phrase" not in code:
        old_return = "return {"
        new_return = """// v5.0 fields
const v5Fields = {
  has_builder_phrase: hasBuilderPhrase,
  builder_phrase_bonus: builderPhraseBonus,
  detected_title_tier: detectedTitleTier,
  title_penalty: titlePenalty
};

return {"""
        code = code.replace(old_return, new_return, 1)

        # Add v5 fields to output
        if "...enrichData" in code:
            code = code.replace(
                "...enrichData",
                "...enrichData,\n    ...v5Fields"
            )

    return code


def update_build_eval_code(code):
    """Update Build Eval node with v5 scoring guidance"""

    # Add v5 stage guidance
    old_stage = "- 25 = Seed/Series A, 10-50 employees (sweet spot)"
    new_stage = """- 25 = Seed/Series A, 10-100 employees (sweet spot)
   - 20 = Series B, 50-150 employees
   - 15 = Early Series C, 100-200 employees (v5: no longer auto-DQ)
   - 10 = Series C/growth, 200-300 employees (rebuild opportunity)"""
    code = code.replace(old_stage, new_stage)

    # Add builder phrase guidance
    if "BUILDER PHRASE OVERRIDE" not in code:
        old_role = "3. ROLE MANDATE"
        new_role = """3. ROLE MANDATE

   v5 BUILDER PHRASE OVERRIDE: +15 pts and title penalty waiver for:
   "first hire", "founding", "greenfield", "0 to 1", "build from scratch",
   "stand up the function", "define the playbook", "no existing team"
"""
        code = code.replace(old_role, new_role)

    return code


def update_parse_eval_code(code):
    """Update Parse Eval to apply v5 modifiers"""

    # Add v5 modifier applications
    if "builderPhraseBonus" not in code:
        old_score = "let finalScore = evaluation.total_score"
        new_score = """let finalScore = evaluation.total_score || 0;

// v5.0: Apply builder phrase bonus
const builderPhraseBonus = enrichData.builder_phrase_bonus || 0;
if (builderPhraseBonus > 0) {
  finalScore += builderPhraseBonus;
}

// v5.0: Apply title penalty
const titlePenalty = enrichData.title_penalty || 0;
if (titlePenalty < 0) {
  finalScore = Math.max(0, finalScore + titlePenalty);
}

// v5.0: Apply headcount penalties
const emp = enrichData.employee_count || 0;
if (emp >= 300 && emp <= 1000 && !enrichData.has_builder_phrase) {
  finalScore = Math.max(0, finalScore - 10);
} else if (emp >= 200 && emp < 300 && !enrichData.has_builder_phrase) {
  finalScore = Math.max(0, finalScore - 5);
}

// Original score tracking
let finalScore = evaluation.total_score"""
        code = code.replace(old_score, new_score)

    return code


def main():
    # Load the v4.15 rescore workflow
    with open('Funding Alerts Rescore v4.15-standalone.json', 'r') as f:
        workflow = json.load(f)

    # Update workflow name
    workflow['name'] = 'Funding Alerts Rescore v5.0 (Standalone)'

    # Update the version filter in Fetch 1 Record
    for node in workflow['nodes']:
        if node.get('name') == 'Fetch 1 Record':
            old_filter = node['parameters'].get('filterByFormula', '')
            if 'v4.15' in old_filter:
                node['parameters']['filterByFormula'] = old_filter.replace('v4.15', 'v5.0')
                print(f"Updated version filter: {old_filter} -> {node['parameters']['filterByFormula']}")

        elif node.get('name') == 'Parse Enrich':
            print('Updating Parse Enrich node...')
            original_len = len(node['parameters']['jsCode'])
            node['parameters']['jsCode'] = update_parse_enrich_code(node['parameters']['jsCode'])
            print(f"  Updated. Code length: {original_len} -> {len(node['parameters']['jsCode'])} characters")

        elif node.get('name') == 'Build Eval':
            print('Updating Build Eval node...')
            original_len = len(node['parameters']['jsCode'])
            node['parameters']['jsCode'] = update_build_eval_code(node['parameters']['jsCode'])
            print(f"  Updated. Code length: {original_len} -> {len(node['parameters']['jsCode'])} characters")

        elif node.get('name') == 'Parse Eval':
            print('Updating Parse Eval node...')
            original_len = len(node['parameters']['jsCode'])
            node['parameters']['jsCode'] = update_parse_eval_code(node['parameters']['jsCode'])
            print(f"  Updated. Code length: {original_len} -> {len(node['parameters']['jsCode'])} characters")

    # Save as v5.0
    output_file = 'Funding Alerts Rescore v5.0-standalone.json'
    with open(output_file, 'w') as f:
        json.dump(workflow, f, indent=2)

    print(f'\nSaved updated workflow to: {output_file}')

    # Generate Airtable Config update instructions
    print('\n' + '='*60)
    print('AIRTABLE CONFIG TABLE UPDATE REQUIRED')
    print('='*60)
    print('''
Update the Config table (tblofzQpzGEN8igVS) with these v5.0 values:

| Key | Old Value | New Value |
|-----|-----------|-----------|
| HARD_EMPLOYEE_CAP | 150 | 1000 |
| SOFT_EMPLOYEE_CAP | 100 | 200 |
| HEAVY_PENALTY_EMPLOYEE | (new) | 300 |
| HARD_FUNDING_CAP | 75000000 | 200000000 |
| SOFT_FUNDING_CAP | 50000000 | 200000000 |
| HEAVY_FUNDING_CAP | (new) | 500000000 |
| VERSION | 4.15 | 5.0 |

Note: The Config Fetcher workflow pulls these values at runtime.
''')


if __name__ == '__main__':
    main()
