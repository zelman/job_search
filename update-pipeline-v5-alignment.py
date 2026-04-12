#!/usr/bin/env python3
"""
Update Job Evaluation Pipeline v6.10 to align with Rescore v5.0 thresholds.

Changes:
1. Employee hard DQ: 350 → 1000
2. Employee penalty: 200-350 → graduated 200-1000
3. Series C: Add <300 employee exception (goes to penalty, not watch, but milder)
"""

import json

# Load the workflow
with open('Job Evaluation Pipeline v6.10.json', 'r') as f:
    workflow = json.load(f)

# Update workflow name
workflow['name'] = 'Job Evaluation Pipeline v6.11'

for node in workflow['nodes']:
    if node.get('name') == 'Parse Enrichment':
        code = node['parameters']['jsCode']

        # Update version comment at top
        old_version = "// v6.8: Fixed P0"
        new_version = "// v6.11: Aligned to Rescore v5.0 thresholds (employee 1000, graduated penalties)\n// v6.8: Fixed P0"
        if old_version in code:
            code = code.replace(old_version, new_version)
            print("Updated version comment")

        # Fix 1: Employee hard DQ 350 → 1000
        old_emp_dq = """// v6.4: Employee hard DQ at 350 (aligned to v9.8 company pipeline)
if (enrichment.employeeCount && enrichment.employeeCount > 350) {
  enrichment.autoDisqualifiers.push(`${enrichment.employeeCount} employees (>350 = CS function already exists)`);
}"""

        new_emp_dq = """// v6.11: Employee hard DQ at 1000 (aligned to Rescore v5.0)
if (enrichment.employeeCount && enrichment.employeeCount > 1000) {
  enrichment.autoDisqualifiers.push(\`\${enrichment.employeeCount} employees (>1000 = too large for builder role)\`);
}"""

        if old_emp_dq in code:
            code = code.replace(old_emp_dq, new_emp_dq)
            print("Fix 1: Updated employee hard DQ 350 → 1000")
        else:
            # Try alternate pattern
            if "employeeCount > 350" in code:
                code = code.replace("employeeCount > 350", "employeeCount > 1000")
                code = code.replace(">350 = CS function already exists", ">1000 = too large for builder role")
                print("Fix 1: Updated employee threshold (alternate pattern)")
            else:
                print("WARNING: Could not find employee DQ pattern")

        # Fix 2: Employee penalty zone 200-350 → graduated 200-1000
        old_emp_penalty = """// v6.4: 200-350 employees = -20 pts penalty zone (aligned to v9.8 company pipeline)
if (enrichment.employeeCount && enrichment.employeeCount >= 200 && enrichment.employeeCount <= 350) {
  enrichment.scoringPenalties.push(`${enrichment.employeeCount} employees (200-350 penalty zone): -20 pts`);
}"""

        new_emp_penalty = """// v6.11: Graduated employee penalties (aligned to Rescore v5.0)
if (enrichment.employeeCount) {
  const emp = enrichment.employeeCount;
  if (emp >= 500 && emp <= 1000) {
    enrichment.scoringPenalties.push(\`\${emp} employees (500-1000 heavy penalty zone): -20 pts\`);
  } else if (emp >= 300 && emp < 500) {
    enrichment.scoringPenalties.push(\`\${emp} employees (300-499 moderate penalty zone): -15 pts\`);
  } else if (emp >= 200 && emp < 300) {
    enrichment.scoringPenalties.push(\`\${emp} employees (200-299 light penalty zone): -5 pts\`);
  }
}"""

        if old_emp_penalty in code:
            code = code.replace(old_emp_penalty, new_emp_penalty)
            print("Fix 2: Updated employee penalty to graduated tiers")
        else:
            # Try simpler replacement
            if "200-350 penalty zone" in code:
                # Find the whole block and replace
                start = code.find("// v6.4: 200-350 employees")
                if start != -1:
                    # Find the end of the if block
                    end = code.find("}", start) + 1
                    old_block = code[start:end]
                    code = code.replace(old_block, new_emp_penalty)
                    print("Fix 2: Updated employee penalty (simpler pattern)")
                else:
                    print("WARNING: Could not find employee penalty block")
            else:
                print("WARNING: Could not find employee penalty pattern")

        # Fix 3: Series C - add <300 employee exception
        old_series_c = """// Series C penalty
if (enrichment.fundingStage === 'Series C') {
  enrichment.scoringPenalties.push('Series C: -10 pts');
}"""

        new_series_c = """// Series C penalty - v6.11: lighter penalty if <300 employees (aligned to Rescore v5.0)
if (enrichment.fundingStage === 'Series C') {
  const emp = enrichment.employeeCount || 0;
  if (emp < 300) {
    enrichment.scoringPenalties.push(\`Series C with \${emp} employees: -5 pts (builder opportunity)\`);
  } else {
    enrichment.scoringPenalties.push('Series C with 300+ employees: -15 pts');
  }
}"""

        if old_series_c in code:
            code = code.replace(old_series_c, new_series_c)
            print("Fix 3: Added Series C <300 employee exception")
        else:
            # Try simpler pattern
            simple_series_c = "if (enrichment.fundingStage === 'Series C') {\n  enrichment.scoringPenalties.push('Series C: -10 pts');\n}"
            if simple_series_c in code:
                code = code.replace(simple_series_c, new_series_c.replace("// Series C penalty - v6.11: lighter penalty if <300 employees (aligned to Rescore v5.0)\n", ""))
                print("Fix 3: Added Series C exception (simpler pattern)")
            else:
                print("WARNING: Could not find Series C penalty pattern")

        node['parameters']['jsCode'] = code

    # Also update the Build Prompt node system prompt thresholds
    elif node.get('name') == 'Build Prompt':
        code = node['parameters']['jsCode']

        # Update employee thresholds in system prompt
        code = code.replace(">350 employees (CS function already exists)", ">1000 employees")
        code = code.replace("200-350 employees: -20 pts", "200-299 employees: -5 pts, 300-499: -15 pts, 500-1000: -20 pts")
        code = code.replace("0 = Too early (<15 emp) or too late (>350 emp)", "0 = Too early (<15 emp) or too late (>1000 emp)")

        node['parameters']['jsCode'] = code
        print("Updated Build Prompt thresholds")

# Save as new version
output_file = 'Job Evaluation Pipeline v6.11.json'
with open(output_file, 'w') as f:
    json.dump(workflow, f, indent=2)

print(f"\nSaved updated workflow to: {output_file}")

# Verification
print("\n" + "=" * 60)
print("VERIFICATION")
print("=" * 60)

with open(output_file) as f:
    wf = json.load(f)

for node in wf['nodes']:
    if node.get('name') == 'Parse Enrichment':
        code = node['parameters']['jsCode']

        print("\n1. Employee hard DQ:")
        if "employeeCount > 1000" in code:
            print("   ✓ Updated to 1000")
        else:
            print("   ✗ NOT updated")

        print("\n2. Employee penalty zones:")
        if "500-1000 heavy penalty" in code:
            print("   ✓ Graduated penalties implemented")
        else:
            print("   ✗ NOT updated")

        print("\n3. Series C exception:")
        if "Series C with" in code and "emp < 300" in code:
            print("   ✓ <300 employee exception added")
        else:
            print("   ✗ NOT updated")

print("\n" + "=" * 60)
print("Import Job Evaluation Pipeline v6.11.json into n8n")
print("=" * 60)
