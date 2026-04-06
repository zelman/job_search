#!/usr/bin/env python3
"""
extract-thresholds.py -- Pull numeric thresholds from n8n workflow JSON files.

Usage:
  python3 extract-thresholds.py <workflow.json> [<workflow2.json>]

Single file: prints all extracted thresholds.
Two files: prints side-by-side comparison with MATCH/MISMATCH flags.

Designed to be run by Claude Code as part of the audit procedure.
"""

import json
import re
import sys

# Patterns to extract from JavaScript code nodes
THRESHOLD_PATTERNS = [
    # Named constants (const NAME = value)
    (r'const\s+(HARD_FUNDING_CAP|SOFT_FUNDING_CAP|MAX_BELIEVABLE_FUNDING|MAX_VALUATION|MIN_EMPLOYEES|HARD_EMPLOYEE_CAP|SOFT_EMPLOYEE_CAP|MIN_FOUNDED_YEAR)\s*=\s*(\d+)', 'constant'),
    # Score bucket boundaries
    (r'finalScore\s*>=\s*(\d+)\)\s*bucket\s*=\s*[\'"]APPLY[\'"]', 'apply_threshold'),
    (r'finalScore\s*>=\s*(\d+)\)\s*bucket\s*=\s*[\'"]WATCH[\'"]', 'watch_threshold'),
    # Hardcoded comparisons (rescore workflow style)
    (r'employeeCount\s*>\s*(\d+)', 'employee_cap_hardcoded'),
    (r'totalFunding\s*>\s*(\d+)', 'funding_cap_hardcoded'),
    (r'valuation\s*>=?\s*(\d+)', 'valuation_cap_hardcoded'),
    # CS Readiness ceiling
    (r'Math\.min\(.+?,\s*(\d+)\)', 'cs_readiness_ceiling'),
    # CS likelihood caps
    (r'finalScore\s*>\s*(\d+).*cs.*unlikely', 'cs_unlikely_cap'),
    (r'finalScore\s*>\s*(\d+).*cs.*low', 'cs_low_cap'),
    # Headcount penalty ranges
    (r'employeeCount\s*>=\s*(\d+)\s*&&\s*employeeCount\s*<=?\s*(\d+)', 'headcount_penalty_range'),
]

def extract_from_workflow(filepath):
    with open(filepath) as f:
        data = json.load(f)
    
    results = {}
    nodes = data.get('nodes', [])
    
    for node in nodes:
        node_name = node.get('name', '')
        code = node.get('parameters', {}).get('jsCode', '')
        body = node.get('parameters', {}).get('jsonBody', node.get('parameters', {}).get('body', ''))
        
        if not code and not body:
            continue
        
        text = code or str(body)
        
        # Extract named constants
        for match in re.finditer(r'const\s+(\w+)\s*=\s*(\d+)', text):
            name, value = match.group(1), int(match.group(2))
            if any(kw in name.upper() for kw in ['CAP', 'MAX', 'MIN', 'THRESHOLD', 'EMPLOYEE', 'FUNDING', 'FOUNDED', 'VALUATION', 'BELIEVABLE']):
                results[f'{node_name}::{name}'] = value
        
        # Extract hardcoded comparisons
        for match in re.finditer(r'employeeCount\s*(?:&&\s*employeeCount\s*)?>\s*(\d+)', text):
            val = int(match.group(1))
            if val > 10:  # Skip trivial checks
                results[f'{node_name}::employee_hard_cap'] = val
        
        for match in re.finditer(r'totalFunding\s*>\s*(\d+)', text):
            results[f'{node_name}::funding_hard_cap'] = int(match.group(1))
        
        for match in re.finditer(r'valuation\s*>=?\s*(\d+)', text):
            val = int(match.group(1))
            if val > 1000000:
                results[f'{node_name}::valuation_cap'] = val
        
        # Score thresholds
        for match in re.finditer(r'finalScore\s*>=\s*(\d+)\)\s*bucket\s*=\s*[\'"]APPLY[\'"]', text):
            results[f'{node_name}::APPLY_threshold'] = int(match.group(1))
        for match in re.finditer(r'finalScore\s*>=\s*(\d+)\)\s*bucket\s*=\s*[\'"]WATCH[\'"]', text):
            results[f'{node_name}::WATCH_threshold'] = int(match.group(1))
        
        # CS likelihood caps
        for match in re.finditer(r"csHireLikelihood\s*===\s*'unlikely'[\s\S]{0,100}finalScore\s*>\s*(\d+)", text):
            results[f'{node_name}::cs_unlikely_cap'] = int(match.group(1))
        for match in re.finditer(r"csHireLikelihood\s*===\s*'low'[\s\S]{0,100}finalScore\s*>\s*(\d+)", text):
            results[f'{node_name}::cs_low_cap'] = int(match.group(1))
        
        # Headcount penalty zones
        for match in re.finditer(r'employeeCount\s*>=\s*(\d+)\s*&&\s*employeeCount\s*<=?\s*(\d+)', text):
            lo, hi = int(match.group(1)), int(match.group(2))
            if lo >= 100:
                results[f'{node_name}::headcount_penalty_{lo}_{hi}'] = f'{lo}-{hi}'
        
        # Min employees
        for match in re.finditer(r'employeeCount\s*<\s*(\w+|[0-9]+)', text):
            val = match.group(1)
            try:
                val = int(val)
                if 5 <= val <= 50:
                    results[f'{node_name}::min_employees'] = val
            except ValueError:
                pass  # It's a variable reference, caught by constant extraction
        
        # Score set to -1 on DQ
        if 'Tide-Pool Score' in text and '-1' in text:
            results[f'{node_name}::score_on_dq'] = -1
    
    return results

def format_value(v):
    if isinstance(v, int) and v >= 1000000:
        if v >= 1000000000:
            return f'{v:,} (${v/1000000000:.1f}B)'
        return f'{v:,} (${v/1000000:.0f}M)'
    return str(v)

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 extract-thresholds.py <workflow.json> [<workflow2.json>]")
        sys.exit(1)
    
    file1 = sys.argv[1]
    results1 = extract_from_workflow(file1)
    
    if len(sys.argv) >= 3:
        file2 = sys.argv[2]
        results2 = extract_from_workflow(file2)
        
        # Cross-reference
        print(f"\n=== THRESHOLD COMPARISON ===")
        print(f"File 1: {file1}")
        print(f"File 2: {file2}\n")
        
        # Normalize keys for comparison (strip node name, keep threshold name)
        def normalize_key(k):
            return k.split('::')[-1]
        
        norm1 = {}
        for k, v in results1.items():
            nk = normalize_key(k)
            norm1.setdefault(nk, []).append((k, v))
        
        norm2 = {}
        for k, v in results2.items():
            nk = normalize_key(k)
            norm2.setdefault(nk, []).append((k, v))
        
        all_keys = sorted(set(list(norm1.keys()) + list(norm2.keys())))
        
        mismatches = []
        for nk in all_keys:
            vals1 = norm1.get(nk, [])
            vals2 = norm2.get(nk, [])
            
            v1_set = set(str(v) for _, v in vals1)
            v2_set = set(str(v) for _, v in vals2)
            
            if vals1 and vals2:
                match = v1_set == v2_set
                status = "MATCH" if match else "MISMATCH"
                if not match:
                    mismatches.append(nk)
                v1_str = ', '.join(format_value(v) for _, v in vals1)
                v2_str = ', '.join(format_value(v) for _, v in vals2)
                print(f"  {nk:40s} | {v1_str:20s} | {v2_str:20s} | {status}")
            elif vals1:
                v1_str = ', '.join(format_value(v) for _, v in vals1)
                print(f"  {nk:40s} | {v1_str:20s} | {'(missing)':20s} | ONLY IN FILE 1")
            else:
                v2_str = ', '.join(format_value(v) for _, v in vals2)
                print(f"  {nk:40s} | {'(missing)':20s} | {v2_str:20s} | ONLY IN FILE 2")
        
        if mismatches:
            print(f"\n  MISMATCHES FOUND: {len(mismatches)}")
            for m in mismatches:
                print(f"    - {m}")
        else:
            print(f"\n  All shared thresholds match.")
    else:
        print(f"\n=== THRESHOLDS EXTRACTED FROM {file1} ===\n")
        for k, v in sorted(results1.items()):
            print(f"  {k:60s} = {format_value(v)}")

if __name__ == '__main__':
    main()
