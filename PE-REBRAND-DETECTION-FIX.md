# PE Rebrand/Merger Detection Fix

**Issue:** Illumia (Transact Campus + CBORD, PE-backed by GTCR) scored 72 and was recommended as "research." GTCR is already in the `peFirms` array but never appeared in `allText` because Brave Search enrichment returned the new brand identity, not the ownership structure.

**Root cause:** Two gaps working together:
1. Merger language in JD/enrichment text isn't detected — `acquirePatterns` regex list doesn't include common rebrand/combination phrases
2. When a merger IS detected, there's no follow-up enrichment query to surface ownership of predecessor companies

**Fix:** Two changes. No new Haiku calls. No structural pipeline changes. One regex update, one conditional Brave Search addition.

---

## Change 1: Add Merger/Rebrand Patterns to `acquirePatterns`

**Location:** Phase 1 enrichment code node, inside the `acquirePatterns` array

**Current patterns that exist (for reference):**
```javascript
const acquirePatterns = [
  /acquired\s+by\s+([A-Z][a-zA-Z0-9\s&]+)/i,
  /bought\s+by\s+([A-Z][a-zA-Z0-9\s&]+)/i,
  /merged\s+with\s+([A-Z][a-zA-Z0-9\s&]+)/i,
  /part\s+of\s+([A-Z][a-zA-Z0-9\s&]+(?:Group|Holdings|Capital|Inc|Corp))/i,
  /subsidiary\s+of\s+([A-Z][a-zA-Z0-9\s&]+)/i,
  /now\s+owned\s+by\s+([A-Z][a-zA-Z0-9\s&]+)/i,
  /joined\s+([A-Z][a-zA-Z0-9\s&]+)\s+family/i,
  /portfolio\s+company\s+of\s+([A-Z][a-zA-Z0-9\s&]+(?:Capital|Partners|Equity)?)/i
];
```

**Add these patterns:**
```javascript
// Merger/rebrand language — signals PE roll-up or corporate combination
/built\s+on\s+(?:the\s+)?(?:collective\s+)?expertise\s+of\s+([A-Z][a-zA-Z0-9\s&]+)/i,
/(?:newly\s+)?combined\s+compan(?:y|ies)/i,
/bringing\s+together\s+([A-Z][a-zA-Z0-9\s&]+)\s+(?:and|&|\+)\s+([A-Z][a-zA-Z0-9\s&]+)/i,
/formed\s+(?:from|by)\s+(?:the\s+)?(?:merger|combination|union)\s+of/i,
/formerly\s+known\s+as\s+([A-Z][a-zA-Z0-9\s&]+)/i,
/rebranded\s+(?:from|as)\s+([A-Z][a-zA-Z0-9\s&]+)/i,
/now\s+(?:known\s+as|operating\s+as|doing\s+business\s+as)/i,
/(?:the\s+)?integration\s+of\s+([A-Z][a-zA-Z0-9\s&]+)\s+(?:and|&|\+)\s+([A-Z][a-zA-Z0-9\s&]+)/i,
/([A-Z][a-zA-Z0-9\s&]+)\s+\+\s+([A-Z][a-zA-Z0-9\s&]+)\s+(?:now|is\s+now|became|becomes)/i
```

**Note:** Some of these don't capture a group (e.g., `combined companies`). That's fine — they trigger the merger detection flag. The predecessor name extraction is a separate step below.

---

## Change 2: Merger Detection Flag + Conditional Ownership Query

**Location:** New logic block in the Phase 1 enrichment code node, AFTER the existing `acquirePatterns` loop and BEFORE the data is passed to Phase 2 gates.

### Step A: Detect merger signal and extract predecessor names

```javascript
// === MERGER/REBRAND DETECTION ===
// Runs against allText (JD + company description + Brave Search summary)
const mergerKeywords = [
  'built on the collective expertise of',
  'built on the expertise of',
  'newly combined companies',
  'newly combined',
  'combined companies',
  'bringing together',
  'formed from the merger',
  'formed by the combination',
  'formerly known as',
  'now known as',
  'rebranded as',
  'rebranded from',
  'joined forces',
  'integration of',
  'platform acquisition',
  'roll-up',
  'rollup'
];

const lowerText = allText.toLowerCase();
const hasMergerSignal = mergerKeywords.some(kw => lowerText.includes(kw));

// Also flag if acquirePatterns already matched (isAcquired from existing code)
const needsOwnershipCheck = hasMergerSignal || isAcquired;

// Try to extract predecessor company names
let predecessorNames = [];
if (needsOwnershipCheck) {
  // Pattern: "expertise of X + Y" or "X and Y" or "bringing together X and Y"
  const combinationPatterns = [
    /expertise\s+of\s+([A-Z][A-Za-z\s]+?)\s*(?:\+|and|&)\s*([A-Z][A-Za-z\s]+?)(?:\.|,|;|\s+and\s|\s+to\s|\s+now)/i,
    /bringing\s+together\s+([A-Z][A-Za-z\s]+?)\s*(?:\+|and|&)\s*([A-Z][A-Za-z\s]+?)(?:\.|,|;|\s+to\s)/i,
    /(?:merger|combination)\s+of\s+([A-Z][A-Za-z\s]+?)\s*(?:\+|and|&)\s*([A-Z][A-Za-z\s]+?)(?:\.|,|;)/i,
    /formerly\s+known\s+as\s+([A-Z][A-Za-z\s]+?)(?:\.|,|;|\s+and)/i,
    /rebranded\s+from\s+([A-Z][A-Za-z\s]+?)(?:\.|,|;|\s+to)/i
  ];

  for (const pattern of combinationPatterns) {
    const match = allText.match(pattern);
    if (match) {
      if (match[1]) predecessorNames.push(match[1].trim());
      if (match[2]) predecessorNames.push(match[2].trim());
      break;
    }
  }

  // Dedupe and clean
  predecessorNames = [...new Set(predecessorNames)]
    .map(n => n.replace(/\s+/g, ' ').trim())
    .filter(n => n.length > 2 && n.length < 60);
}
```

### Step B: Conditional Brave Search for ownership

**This only fires when `needsOwnershipCheck === true`.** Low volume, low cost.

```javascript
// === OWNERSHIP ENRICHMENT (conditional) ===
let ownershipEnrichment = '';

if (needsOwnershipCheck) {
  const ownershipQueries = [];

  // Always query the company itself
  const companyName = companyData.company_name || '';
  if (companyName) {
    ownershipQueries.push(`"${companyName}" private equity investors`);
  }

  // Query predecessor names if extracted
  for (const pred of predecessorNames) {
    ownershipQueries.push(`"${pred}" private equity acquisition`);
  }

  // Run queries (cap at 3 to limit API calls)
  const queryResults = [];
  for (const query of ownershipQueries.slice(0, 3)) {
    try {
      // Use your existing Brave Search API call pattern
      const result = await braveSearch(query); // replace with actual API call
      if (result) queryResults.push(result);
    } catch (e) {
      // Brave Search failure is non-fatal — log and continue
    }
  }

  ownershipEnrichment = queryResults.join(' ');

  // Append to allText so existing peFirms check catches it
  allText = allText + ' ' + ownershipEnrichment;
}

// Flag for downstream logging
const mergerDetected = needsOwnershipCheck;
const predecessorsFound = predecessorNames;
```

### Step C: Existing PE check now catches it

No change needed here. The existing code already does:
```javascript
const isPEBacked = peFirms.some(f => new RegExp(f, 'i').test(allText));
```

Because `ownershipEnrichment` (containing "GTCR" from the Brave Search results) was appended to `allText`, this check now fires correctly.

---

## What This Catches

**Illumia specifically:**
1. JD says "built on the collective expertise of Transact Campus + CBORD" → `mergerKeywords` match on "built on the collective expertise of"
2. `predecessorNames` extracts ["Transact Campus", "CBORD"]
3. Brave Search query: `"Transact Campus" private equity acquisition` → returns GTCR ownership info
4. "GTCR" now appears in `allText`
5. Existing `peFirms` check matches GTCR → `isPEBacked = true` → HARD FAIL at Phase 2

**Other PE roll-up patterns this catches:**
- "Illumia was built on the collective expertise of Transact Campus + CBORD" ✓
- "Our newly combined companies bring together X and Y" ✓
- "Formerly known as CompanyA, now rebranded as CompanyB" ✓
- "Formed from the merger of CompanyA and CompanyB" ✓
- Any company where `isAcquired` was already true but acquirer wasn't in peFirms (now gets a follow-up query) ✓

---

## Implementation Notes

1. **No new n8n nodes required** if Brave Search is called inline in the code node. If your architecture requires a separate HTTP Request node for Brave Search, add a conditional branch: merger detected → HTTP Request → merge back.

2. **Log `mergerDetected` and `predecessorsFound` to Airtable** as new fields (or append to existing rationale). This lets you audit how often the merger detector fires and whether it's producing false positives.

3. **The ownership query only fires when merger language is detected.** Expected volume: <5% of companies. Cost: 1-3 extra Brave Search API calls per flagged company.

4. **Test against known cases:**
   - Illumia / Transact Campus + CBORD (GTCR) → should now HARD FAIL
   - Campspot / Northgate Resorts (PE-originated) → should still catch via existing patterns
   - ESO / Vista Equity → should still catch via existing patterns (Vista already in allText)

5. **Also update the Transact Campus record in Airtable** to "Not a Fit" with corrected rationale noting PE backing via GTCR.

---

## Airtable Record Fix

Update `recaLhcJUJgnNvTqo` (Transact Campus / Illumia, currently scored 72):
- Review Status → "Not a Fit"
- Tide-Pool Score → 0
- Rationale → "PE-BACKED: GTCR owns Transact Campus. Illumia is a PE roll-up combining Transact Campus + CBORD. Merger language in JD ('built on the collective expertise of') was not caught by pipeline v9.8. Additionally: manage-and-optimize mandate (existing team of 7-8 CSMs), NRR-first accountability framing, headcount well over 150. Multiple hard disqualifiers."
