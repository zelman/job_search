#!/usr/bin/env python3
"""
Fix PE Backed false positives in Funding Alerts.

Uses the PE Firms table as a lookup to determine which records
actually have PE investors vs VC investors incorrectly flagged.

Run with: python3 fix-pe-false-positives.py

Requires: AIRTABLE_API_KEY environment variable
"""

import os
import json
import requests
import time

# Airtable configuration
BASE_ID = "appFEzXvPWvRtXgRY"
FUNDING_ALERTS_TABLE = "tbl7yU6QYfIFSC2nD"
PE_FIRMS_TABLE = "tblU2izcb0wnCNMuV"

# Field IDs
FIELD_COMPANY_NAME = "fldM1oukZjLZ8n0WX"
FIELD_VC_FIRM = "fldiR3epFbkYJvtAc"
FIELD_PE_BACKED = "fldTqUT6fcYE72AMk"
FIELD_PE_FIRM_NAME = "fld0Sy2B10LbiGDbt"
FIELD_PE_ALIASES = "fldVSKfXCijPSe9c0"
FIELD_PE_ACTIVE = "fldeH5HBBwX2MszSt"

API_KEY = os.environ.get("AIRTABLE_API_KEY")
if not API_KEY:
    print("ERROR: Set AIRTABLE_API_KEY environment variable")
    print("  export AIRTABLE_API_KEY='pat...'")
    exit(1)

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def fetch_pe_firms():
    """Fetch all PE firms and build a lookup set."""
    url = f"https://api.airtable.com/v0/{BASE_ID}/{PE_FIRMS_TABLE}"
    pe_firms = set()

    offset = None
    while True:
        params = {"pageSize": 100}
        if offset:
            params["offset"] = offset

        resp = requests.get(url, headers=HEADERS, params=params)
        resp.raise_for_status()
        data = resp.json()

        for rec in data.get("records", []):
            fields = rec.get("fields", {})
            # Only include active firms (field: Active / fldeH5HBBwX2MszSt)
            if not fields.get("Active", True):
                continue

            # Add firm name (field: Firm Name / fld0Sy2B10LbiGDbt) - lowercase for matching
            name = fields.get("Firm Name", "").lower().strip()
            if name:
                pe_firms.add(name)

            # Add aliases (field: Aliases / fldVSKfXCijPSe9c0)
            aliases = fields.get("Aliases", "")
            if aliases:
                for alias in aliases.split(","):
                    alias = alias.strip().lower()
                    if alias:
                        pe_firms.add(alias)

        offset = data.get("offset")
        if not offset:
            break

    return pe_firms

def is_pe_firm(vc_firm, pe_firms_lookup):
    """Check if a VC firm name matches any PE firm."""
    if not vc_firm:
        return False

    # Skip null/empty/placeholder values
    vc_lower = vc_firm.lower().strip()
    if not vc_lower or vc_lower in ("null", "none", "unknown", "n/a", "sec form d"):
        return False

    # Direct match
    if vc_lower in pe_firms_lookup:
        return True

    # Partial match (PE firm name contained in VC field or vice versa)
    # Only match if the PE name is 4+ chars to avoid false positives on short strings
    for pe in pe_firms_lookup:
        if len(pe) >= 4:
            if pe in vc_lower or vc_lower in pe:
                return True

    return False

def fetch_pe_backed_records():
    """Fetch all records where PE Backed = true."""
    url = f"https://api.airtable.com/v0/{BASE_ID}/{FUNDING_ALERTS_TABLE}"
    records = []

    offset = None
    page = 0
    while True:
        page += 1
        params = {
            "filterByFormula": "{PE Backed} = TRUE()",
            "fields[]": ["Company Name", "VC Firm", "PE Backed"],
            "pageSize": 100
        }
        if offset:
            params["offset"] = offset

        resp = requests.get(url, headers=HEADERS, params=params)
        resp.raise_for_status()
        data = resp.json()

        records.extend(data.get("records", []))
        print(f"  Page {page}: fetched {len(data.get('records', []))} records (total: {len(records)})")

        offset = data.get("offset")
        if not offset:
            break

        time.sleep(0.2)  # Rate limiting

    return records

def update_records(record_ids, pe_backed_value):
    """Update PE Backed field for a batch of records."""
    url = f"https://api.airtable.com/v0/{BASE_ID}/{FUNDING_ALERTS_TABLE}"

    # Process in batches of 10
    batches = [record_ids[i:i+10] for i in range(0, len(record_ids), 10)]

    updated = 0
    for i, batch in enumerate(batches):
        records = [{"id": rid, "fields": {"PE Backed": pe_backed_value}} for rid in batch]

        resp = requests.patch(url, headers=HEADERS, json={"records": records})
        resp.raise_for_status()

        updated += len(batch)
        if (i + 1) % 10 == 0:
            print(f"    Updated {updated}/{len(record_ids)} records...")

        time.sleep(0.2)  # Rate limiting

    return updated

def main():
    import sys
    dry_run = "--dry-run" in sys.argv

    print("=" * 60)
    print("PE False Positive Cleanup")
    if dry_run:
        print(">>> DRY RUN MODE - no changes will be made <<<")
    print("=" * 60)

    # Step 1: Build PE firms lookup
    print("\n1. Fetching PE Firms lookup table...")
    pe_firms = fetch_pe_firms()
    print(f"   Loaded {len(pe_firms)} PE firm names/aliases")

    # Step 2: Fetch all PE Backed = true records
    print("\n2. Fetching Funding Alerts with PE Backed = true...")
    records = fetch_pe_backed_records()
    print(f"   Found {len(records)} records")

    # Step 3: Classify into true PE vs false positives
    print("\n3. Classifying records...")
    true_pe = []
    false_pe = []

    for rec in records:
        fields = rec.get("fields", {})
        company = fields.get("Company Name", "Unknown")
        vc_firm = fields.get("VC Firm", "")

        if is_pe_firm(vc_firm, pe_firms):
            true_pe.append((rec["id"], company, vc_firm))
        else:
            false_pe.append((rec["id"], company, vc_firm))

    print(f"   TRUE PE (keep as is): {len(true_pe)}")
    print(f"   FALSE PE (need to flip): {len(false_pe)}")

    # Show samples
    print("\n   Sample TRUE PE:")
    for rid, company, vc in true_pe[:5]:
        print(f"     - {company}: {vc}")

    print("\n   Sample FALSE PE:")
    for rid, company, vc in false_pe[:10]:
        print(f"     - {company}: {vc or '(empty)'}")

    # Step 4: Flip false positives
    if false_pe:
        if dry_run:
            print(f"\n4. DRY RUN: Would flip {len(false_pe)} false positives to PE Backed = false")
            print("   Run without --dry-run to apply changes.")
        else:
            print(f"\n4. Flipping {len(false_pe)} false positives to PE Backed = false...")
            false_pe_ids = [r[0] for r in false_pe]
            updated = update_records(false_pe_ids, False)
            print(f"   Done! Updated {updated} records.")
    else:
        print("\n4. No false positives to fix!")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total records checked: {len(records)}")
    print(f"True PE (unchanged): {len(true_pe)}")
    print(f"False PE {'(would flip)' if dry_run else '(flipped)'}: {len(false_pe)}")
    if dry_run:
        print("\nThis was a DRY RUN. Run without --dry-run to apply changes.")
    else:
        print("\nRe-run rescore to update scores for affected companies.")
    print("=" * 60)

if __name__ == "__main__":
    main()
