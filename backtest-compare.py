#!/usr/bin/env python3
"""
Compare before/after scores from v5 rescore backtest.

Run this AFTER the rescore workflow has processed records.

Usage: python3 backtest-compare.py
"""

import json
import os

# Load pre-v5 snapshot
snapshot_path = '/Users/zelman/Desktop/Quarantine/Side Projects/Job Search/backtest-snapshot-pre-v5.json'

if not os.path.exists(snapshot_path):
    print("ERROR: Run the snapshot query first to create backtest-snapshot-pre-v5.json")
    exit(1)

with open(snapshot_path) as f:
    pre_v5 = json.load(f)

print("=" * 60)
print("V5 BACKTEST COMPARISON")
print("=" * 60)
print()
print("PRE-V5 SNAPSHOT:")
print(f"  Total records: {pre_v5['total_records']}")
print(f"  APPLY (70+):   {pre_v5['score_distribution']['APPLY (70+)']}")
print(f"  WATCH (40-69): {pre_v5['score_distribution']['WATCH (40-69)']}")
print(f"  PASS (<40):    {pre_v5['score_distribution']['PASS (<40)']}")
print(f"  Zero/DQ:       {pre_v5['score_distribution']['Zero/DQ']}")
print()
print("-" * 60)
print()
print("To see POST-V5 results, run this Airtable query in n8n or via API:")
print()
print("  Filter: Last Scored Version = 'v5.0'")
print("  Fields: Company Name, Tide-Pool Score, Status, Employee Count")
print()
print("Or use this curl command:")
print()
print('''curl "https://api.airtable.com/v0/appFEzXvPWvRtXgRY/Funding%20Alerts?filterByFormula={Last%20Scored%20Version}='v5.0'" \\
  -H "Authorization: Bearer YOUR_API_KEY" | python3 -c "
import json, sys
from collections import Counter
data = json.load(sys.stdin)
records = data.get('records', [])
scores = [r['fields'].get('Tide-Pool Score', 0) for r in records]
statuses = Counter(r['fields'].get('Status', 'Unknown') for r in records)

print(f'Records rescored with v5.0: {len(records)}')
print()
print('Score distribution:')
buckets = {'APPLY': 0, 'WATCH': 0, 'PASS': 0, 'Zero': 0}
for s in scores:
    if s == 0: buckets['Zero'] += 1
    elif s >= 70: buckets['APPLY'] += 1
    elif s >= 40: buckets['WATCH'] += 1
    else: buckets['PASS'] += 1
for b, c in buckets.items():
    print(f'  {b}: {c}')
print()
print('Status counts:')
for s, c in statuses.items():
    print(f'  {s}: {c}')
"
''')

print()
print("=" * 60)
print("EXPECTED CHANGES WITH V5:")
print("=" * 60)
print("""
1. Companies 150-300 employees should NO LONGER be auto-DQ'd
   - Will now score based on fit, with -5 to -10 pt penalty

2. Companies with $75M-$200M funding should NO LONGER be auto-DQ'd
   - Will now score based on fit

3. Series C companies <300 employees should be WATCH not DQ
   - Flagged for manual review

4. Companies with insufficient data should score 40-45 (WATCH)
   - Previously scored 0 (DQ)

5. "First hire" / "greenfield" / "0-to-1" roles get +15 bonus
   - May push some from WATCH to APPLY

EXPECTED OUTCOME:
- Fewer Auto-Disqualified records
- More WATCH scores (40-69)
- Some new APPLY scores (70+)
- Companies like Assort Health, Castor, PermitFlow should surface
""")
