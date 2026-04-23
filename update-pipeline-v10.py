#!/usr/bin/env python3
"""
Update Enrich & Evaluate Pipeline from v9.18 to v10.0
Implements all threshold changes from SCORING-THRESHOLDS.md
"""

import json
import re

def update_parse_enrichment_code(code):
    """Update Parse Enrichment node with v10 thresholds and logic"""

    # Update version comment
    new_version_comment = '''// v10.0: MAJOR APERTURE WIDENING (Apr 2026)
// - Title gate now context-dependent by company size
// - Employee hard cap 150→1000, soft cap 100→200, heavy penalty zone 300-1000
// - Funding hard cap $75M→$200M, soft zone $200M-$500M
// - Series C no longer auto-DQ if <300 employees (manual review path)
// - Incomplete data scores WATCH (40-45) instead of DQ
// - Function widening: Implementation, Professional Services, Solutions Consulting, etc.
// - Builder phrase override: +15 pts and title penalty waiver
//
// Previous versions:
// v9.16: Threshold alignment + stage gate fix
// v9.15: Stage Gate + Mature Company Detection
// v9.14: Gate tightening (now reversed in v10)
'''
    code = re.sub(
        r'// v9\.16: Threshold Alignment.*?(?=\nconst braveResponse)',
        new_version_comment,
        code,
        flags=re.DOTALL
    )

    # Update threshold constants - one by one for safety
    code = code.replace(
        "const HARD_FUNDING_CAP = 75000000;     // v9.16: Aligned to SCORING-THRESHOLDS.md ($75M)    // v9.14: Was 500M. Companies over $150M total funding are too mature.",
        "const HARD_FUNDING_CAP = 200000000;    // v10: Was $75M. Above $200M = auto-DQ"
    )
    code = code.replace(
        "const SOFT_FUNDING_CAP = 50000000;     // v9.16: Aligned to SCORING-THRESHOLDS.md ($50M)",
        "const SOFT_FUNDING_CAP = 200000000;    // v10: $200M-$500M gets -10 pts\nconst HEAVY_FUNDING_CAP = 500000000;   // v10 NEW: Above $500M = major penalty"
    )
    code = code.replace(
        "const HARD_EMPLOYEE_CAP = 150;         // v9.16: Aligned to SCORING-THRESHOLDS.md        // v9.14: Was 350. Over 200 employees = auto-DQ.",
        "const HARD_EMPLOYEE_CAP = 1000;        // v10: Was 150. Above 1000 = auto-DQ\nconst HEAVY_PENALTY_EMPLOYEE = 300;    // v10 NEW: 300-1000 gets -10 pts"
    )
    code = code.replace(
        "const SOFT_EMPLOYEE_CAP = 100;         // v9.16: Aligned to SCORING-THRESHOLDS.md        // v9.14: Was 200. 150-200 employees = warning + score penalty.",
        "const SOFT_EMPLOYEE_CAP = 200;         // v10: Was 100. 200-300 gets -5 pts"
    )

    # Add builder phrase detection after the existing signal patterns
    builder_phrase_code = '''
// v10 NEW: Builder phrase detection for role mandate override
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

const hasBuilderPhrase = BUILDER_PHRASES.some(p => p.test(allText) || p.test(companyData.description || ''));
let builderPhraseBonus = hasBuilderPhrase ? 15 : 0;

// v10 NEW: Valid CS functions (widened)
const VALID_CS_FUNCTIONS = [
  /customer\\s*(success|support|experience|service|care)/i,
  /\\b(implementation|onboarding)\\b/i,
  /professional\\s*services/i,
  /solutions?\\s*(consulting|engineer)/i,
  /client\\s*(services?|experience)/i,
  /customer\\s*operations/i
];

const hasValidCSFunction = VALID_CS_FUNCTIONS.some(p => p.test(allText) || p.test(companyData.description || ''));

// v10 NEW: Title tier detection
const TITLE_PATTERNS = {
  executive: /\\b(VP|Vice President|Head of|Director)\\b/i,
  seniorManager: /\\b(Senior Manager|Lead|Principal)\\b/i,
  manager: /\\b(Manager|CSM|Customer Success Manager)\\b/i,
  ic: /\\b(Specialist|Associate|Coordinator|Representative|Agent|Analyst)\\b/i
};

let detectedTitleTier = 'unknown';
if (TITLE_PATTERNS.executive.test(allText)) detectedTitleTier = 'executive';
else if (TITLE_PATTERNS.seniorManager.test(allText)) detectedTitleTier = 'seniorManager';
else if (TITLE_PATTERNS.manager.test(allText)) detectedTitleTier = 'manager';
else if (TITLE_PATTERNS.ic.test(allText)) detectedTitleTier = 'ic';

// v10 NEW: Title penalty calculation based on company size
let titlePenalty = 0;
if (!hasBuilderPhrase) {  // Builder phrases override title penalties
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
      // IC at 300+ = auto-DQ (handled separately)
    } else if (emp >= 150) titlePenalty = -15;
    else if (emp >= 50) titlePenalty = -10;
    else titlePenalty = -5;
  }
}

'''

    # Insert builder phrase code before the autoDisqualifiers section
    code = code.replace(
        "// === BUILD DISQUALIFICATION LIST ===",
        builder_phrase_code + "\n// === BUILD DISQUALIFICATION LIST ==="
    )

    # Update the employee cap DQ logic (add IC at 300+ auto-DQ)
    old_emp_dq = "if (employeeCount && employeeCount > HARD_EMPLOYEE_CAP) autoDisqualifiers.push(`Too large (>${HARD_EMPLOYEE_CAP} employees: ${employeeCount})`);"
    new_emp_dq = """// v10: IC at 300+ company = auto-DQ
if (employeeCount && employeeCount >= 300 && detectedTitleTier === 'ic') {
  autoDisqualifiers.push('IC title at large company (auto-DQ)');
}
if (employeeCount && employeeCount > HARD_EMPLOYEE_CAP) autoDisqualifiers.push(`Too large (>${HARD_EMPLOYEE_CAP} employees: ${employeeCount})`);"""
    code = code.replace(old_emp_dq, new_emp_dq)

    # Update Series C handling - no longer auto-DQ if <300 employees
    old_series_c = """// v9.15: Stage Gate - Series C or later
if (isLateStageByPattern) autoDisqualifiers.push(`Past target stage (${fundingStage || 'late stage detected'})`);
else if (['Series D', 'Series E'].includes(fundingStage)) autoDisqualifiers.push(`Late stage (${fundingStage})`);"""

    new_series_c = """// v10: Series C manual review path (no longer auto-DQ if <300 employees)
if (isLateStageByPattern) {
  if (fundingStage && /series\\s*c/i.test(fundingStage) && employeeCount && employeeCount < 300) {
    warnings.push('Series C but small (' + employeeCount + ' emp) — manual review');
  } else if (['Series D', 'Series E', 'Series F'].some(s => (fundingStage || '').includes(s))) {
    autoDisqualifiers.push('Late stage (' + fundingStage + ')');
  } else if (employeeCount && employeeCount >= 300) {
    autoDisqualifiers.push('Series C at scale (' + employeeCount + ' employees)');
  } else {
    autoDisqualifiers.push('Past target stage (' + (fundingStage || 'late stage detected') + ')');
  }
} else if (['Series D', 'Series E'].includes(fundingStage)) {
  autoDisqualifiers.push('Late stage (' + fundingStage + ')');
}"""
    code = code.replace(old_series_c, new_series_c)

    # Update data insufficiency handling - WATCH instead of DQ
    old_data_gate = """// v9.14: DATA SUFFICIENCY GATE
let dataPointCount = 0;
if (employeeCount) dataPointCount++;
if (fundingStage) dataPointCount++;
if (totalFunding) dataPointCount++;
if (foundedYear || ycBatchYear) dataPointCount++;
if (companyData.description && companyData.description.length > 50) dataPointCount++;
const isDataInsufficient = dataPointCount < 2;
if (isDataInsufficient && autoDisqualifiers.length === 0) {
  autoDisqualifiers.push('Insufficient enrichment data (' + dataPointCount + '/5 data points)');
}"""

    new_data_gate = """// v10: DATA SUFFICIENCY - WATCH instead of DQ
let dataPointCount = 0;
if (employeeCount) dataPointCount++;
if (fundingStage) dataPointCount++;
if (totalFunding) dataPointCount++;
if (foundedYear || ycBatchYear) dataPointCount++;
if (companyData.description && companyData.description.length > 50) dataPointCount++;
const isDataInsufficient = dataPointCount < 2;

// v10: Check for data conflicts (e.g., 16 employees + $475M funding)
const hasDataConflict = (employeeCount && employeeCount < 50 && totalFunding && totalFunding > 100000000) ||
                        (employeeCount && employeeCount < 20 && totalFunding && totalFunding > 50000000);

// v10: Don't DQ for insufficient data - flag for manual review instead
if (isDataInsufficient) {
  warnings.push('NEEDS MANUAL REVIEW: Insufficient enrichment data (' + dataPointCount + '/5 data points)');
}
if (hasDataConflict) {
  warnings.push('DATA CONFLICT - VERIFY: Employee/funding mismatch (' + employeeCount + ' emp, ' + totalFundingRaw + ')');
}"""
    code = code.replace(old_data_gate, new_data_gate)

    # Update soft cap warnings for v10 thresholds
    old_emp_warning = """if (employeeCount && employeeCount >= SOFT_EMPLOYEE_CAP && employeeCount <= HARD_EMPLOYEE_CAP) {
  warnings.push(`Employee count ${employeeCount} in penalty zone (${SOFT_EMPLOYEE_CAP}-${HARD_EMPLOYEE_CAP})`);
}"""

    new_emp_warning = """// v10: Tiered employee penalties
if (employeeCount && employeeCount >= HEAVY_PENALTY_EMPLOYEE && employeeCount <= HARD_EMPLOYEE_CAP) {
  warnings.push('Employee count ' + employeeCount + ' in heavy penalty zone (' + HEAVY_PENALTY_EMPLOYEE + '-' + HARD_EMPLOYEE_CAP + '): -10 pts');
} else if (employeeCount && employeeCount >= SOFT_EMPLOYEE_CAP && employeeCount < HEAVY_PENALTY_EMPLOYEE) {
  warnings.push('Employee count ' + employeeCount + ' in soft penalty zone (' + SOFT_EMPLOYEE_CAP + '-' + HEAVY_PENALTY_EMPLOYEE + '): -5 pts');
}"""
    code = code.replace(old_emp_warning, new_emp_warning)

    old_funding_warning = """if (totalFunding && totalFunding > SOFT_FUNDING_CAP && totalFunding <= HARD_FUNDING_CAP) {
  warnings.push(`Funding ${totalFundingRaw} exceeds ${formatFunding(SOFT_FUNDING_CAP)} soft cap`);
}"""

    new_funding_warning = """// v10: Funding soft cap warnings
if (totalFunding && totalFunding > HEAVY_FUNDING_CAP) {
  warnings.push('Funding ' + totalFundingRaw + ' exceeds ' + formatFunding(HEAVY_FUNDING_CAP) + ' heavy cap: major penalty');
} else if (totalFunding && totalFunding > SOFT_FUNDING_CAP && totalFunding <= HARD_FUNDING_CAP) {
  warnings.push('Funding ' + totalFundingRaw + ' exceeds ' + formatFunding(SOFT_FUNDING_CAP) + ' soft cap: -10 pts');
}"""
    code = code.replace(old_funding_warning, new_funding_warning)

    # Add new output fields for v10
    old_output = "is_data_insufficient: isDataInsufficient,"
    new_output = """is_data_insufficient: isDataInsufficient,
    has_data_conflict: hasDataConflict,
    // v10 fields
    has_builder_phrase: hasBuilderPhrase,
    builder_phrase_bonus: builderPhraseBonus,
    detected_title_tier: detectedTitleTier,
    title_penalty: titlePenalty,
    has_valid_cs_function: hasValidCSFunction,"""
    code = code.replace(old_output, new_output)

    return code


def update_build_evaluation_prompt(code):
    """Update Build Evaluation Prompt with v10 scoring guidance"""

    # Update the scoring guidance for Stage & Size Fit
    old_stage_guide = """2. STAGE & SIZE FIT (25 points max)
   - 25 = Seed/Series A, 10-50 employees (sweet spot)
   - 20 = Series B, 30-80 employees
   - 15 = Pre-seed or Series C, appropriate size
   - 10 = Growth stage but still building
   - 5 = Later stage or larger company
   - 0 = Too early (<10 emp) or too late (150+ emp)"""

    new_stage_guide = """2. STAGE & SIZE FIT (25 points max)
   - 25 = Seed/Series A, 10-100 employees (sweet spot)
   - 20 = Series B, 50-150 employees
   - 15 = Early Series C, 100-200 employees (v10: no longer auto-DQ)
   - 10 = Series C/growth, 200-300 employees (rebuild/transform opportunity)
   - 5 = Later stage or 300-500 employees
   - 0 = Too early (<10 emp) or too late (500+ emp)

   v10 NOTE: Companies 150-300 employees are now scored, not filtered.
   These often need CS rebuild/transformation - strong build opportunities."""
    code = code.replace(old_stage_guide, new_stage_guide)

    # Add builder phrase bonus guidance before ROLE MANDATE
    old_role_mandate = "3. ROLE MANDATE (20 points max)"
    new_role_mandate = """3. ROLE MANDATE (20 points max)

   v10 BUILDER PHRASE OVERRIDE: If job description contains ANY of these phrases,
   add +15 pts and waive any title penalties:
   - "build from scratch" / "build from the ground up"
   - "first hire" / "founding" / "greenfield" / "0 to 1"
   - "stand up the function" / "establish the team"
   - "no existing team" / "first customer-facing hire"
   - "define the playbook" / "create the process"

   This is the single strongest positive signal.
"""
    code = code.replace(old_role_mandate, new_role_mandate)

    # Update function widening guidance - add before CALIBRATION EXAMPLES
    old_calibration = "CALIBRATION EXAMPLES (correct scoring for reference):"
    new_calibration = """v10 FUNCTION WIDENING: The following functions are equally valid targets:
- Customer Success / Support / Experience / Service / Care
- Implementation / Onboarding
- Professional Services
- Solutions Consulting / Solutions Engineering (post-sales, not pre-sales)
- Client Services / Client Experience
- Customer Operations

Apply same scoring logic to these functions.

CALIBRATION EXAMPLES (correct scoring for reference):"""
    code = code.replace(old_calibration, new_calibration)

    return code


def update_parse_evaluation_code(code):
    """Update Parse Evaluation to apply v10 modifiers"""

    # Add builder phrase bonus application before the funding staleness section
    old_funding_stale = "// v9.9: Apply funding staleness modifier from enrichment"
    new_modifiers = """// v10: Apply builder phrase bonus
const builderPhraseBonus = companyData.builder_phrase_bonus || 0;
if (builderPhraseBonus > 0) {
  finalScore += builderPhraseBonus;
  scoreCapReason = scoreCapReason ? scoreCapReason + ' | ' : '';
  scoreCapReason += 'Builder phrase bonus: +' + builderPhraseBonus;
}

// v10: Apply title penalty
const titlePenalty = companyData.title_penalty || 0;
if (titlePenalty < 0) {
  finalScore = Math.max(0, finalScore + titlePenalty);
  scoreCapReason = scoreCapReason ? scoreCapReason + ' | ' : '';
  scoreCapReason += 'Title penalty: ' + titlePenalty + ' (tier: ' + (companyData.detected_title_tier || 'unknown') + ', emp: ' + (companyData.employee_count || '?') + ')';
}

// v10: Apply headcount penalties
const emp = companyData.employee_count || 0;
if (emp >= 300 && emp <= 1000 && !companyData.has_builder_phrase) {
  finalScore = Math.max(0, finalScore - 10);
  scoreCapReason = scoreCapReason ? scoreCapReason + ' | ' : '';
  scoreCapReason += 'Heavy headcount penalty: -10 (' + emp + ' employees)';
} else if (emp >= 200 && emp < 300 && !companyData.has_builder_phrase) {
  finalScore = Math.max(0, finalScore - 5);
  scoreCapReason = scoreCapReason ? scoreCapReason + ' | ' : '';
  scoreCapReason += 'Soft headcount penalty: -5 (' + emp + ' employees)';
}

// v9.9: Apply funding staleness modifier from enrichment"""
    code = code.replace(old_funding_stale, new_modifiers)

    # Add v10 output fields
    old_output = "funding_staleness_modifier: fundingStalenessModifier,"
    new_output = """funding_staleness_modifier: fundingStalenessModifier,
    // v10 fields
    builder_phrase_bonus: builderPhraseBonus,
    title_penalty: titlePenalty,
    has_builder_phrase: companyData.has_builder_phrase || false,
    detected_title_tier: companyData.detected_title_tier || 'unknown',"""
    code = code.replace(old_output, new_output)

    return code


def main():
    # Load the v9.18 pipeline
    with open('Enrich & Evaluate Pipeline v9.18.json', 'r') as f:
        pipeline = json.load(f)

    # Update pipeline name
    pipeline['name'] = 'Enrich & Evaluate Pipeline v10.0'

    # Find and update nodes
    for node in pipeline['nodes']:
        if node.get('name') == 'Parse Enrichment':
            print('Updating Parse Enrichment node...')
            original_len = len(node['parameters']['jsCode'])
            node['parameters']['jsCode'] = update_parse_enrichment_code(node['parameters']['jsCode'])
            print(f"  Updated. Code length: {original_len} -> {len(node['parameters']['jsCode'])} characters")

        elif node.get('name') == 'Build Evaluation Prompt':
            print('Updating Build Evaluation Prompt node...')
            original_len = len(node['parameters']['jsCode'])
            node['parameters']['jsCode'] = update_build_evaluation_prompt(node['parameters']['jsCode'])
            print(f"  Updated. Code length: {original_len} -> {len(node['parameters']['jsCode'])} characters")

        elif node.get('name') == 'Parse Evaluation':
            print('Updating Parse Evaluation node...')
            original_len = len(node['parameters']['jsCode'])
            node['parameters']['jsCode'] = update_parse_evaluation_code(node['parameters']['jsCode'])
            print(f"  Updated. Code length: {original_len} -> {len(node['parameters']['jsCode'])} characters")

    # Save as v10.0
    output_file = 'Enrich & Evaluate Pipeline v10.0.json'
    with open(output_file, 'w') as f:
        json.dump(pipeline, f, indent=2)

    print(f'\nSaved updated pipeline to: {output_file}')

    # Verify the updates
    print('\nVerifying threshold updates...')
    with open(output_file, 'r') as f:
        content = f.read()

    checks = [
        ('HARD_EMPLOYEE_CAP = 1000', 'Employee hard cap 1000'),
        ('HEAVY_PENALTY_EMPLOYEE = 300', 'Employee heavy penalty 300'),
        ('SOFT_EMPLOYEE_CAP = 200', 'Employee soft cap 200'),
        ('HARD_FUNDING_CAP = 200000000', 'Funding hard cap $200M'),
        ('HEAVY_FUNDING_CAP = 500000000', 'Funding heavy cap $500M'),
        ('has_builder_phrase', 'Builder phrase detection'),
        ('title_penalty', 'Title penalty'),
        ('BUILDER_PHRASES', 'Builder phrase patterns'),
        ('VALID_CS_FUNCTIONS', 'Valid CS functions'),
        ('detectedTitleTier', 'Title tier detection'),
        ('has_data_conflict', 'Data conflict detection'),
        ('Series C but small', 'Series C manual review path'),
    ]

    all_passed = True
    for pattern, desc in checks:
        if pattern in content:
            print(f'  ✓ {desc}')
        else:
            print(f'  ✗ {desc}: MISSING')
            all_passed = False

    if all_passed:
        print('\n✓ All v10 features verified successfully!')
    else:
        print('\n⚠ Some features may need manual verification')


if __name__ == '__main__':
    main()
