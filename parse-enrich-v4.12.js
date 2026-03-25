// v4.12: DQ Duplication Fix (Mar 2026)
//
// Fixes duplicate DQ reasons bug where detection logic ran even when
// pre-existing DQ reasons were present, causing accumulating duplicates
// on each rescore run.
//
// Previous fixes (v4.11):
// 1. Funding hard cap: $450M → $75M (catches HouseRx, Candid Health)
// 2. Employee hard cap: 350 → 150 (catches HouseRx, Candid Health)
// 3. PE acquisition detection patterns (catches SmarterDx/New Mountain Capital)
// 4. Hardware/deeptech keywords - power transmission, nuclear, grid (catches Veir, Last Energy)
// 5. Funding-per-head ratio gate >$2M/head at <50 emp (catches Gumloop)

const captured = $('Capture').first().json;
const RECORD_ID = captured.RECORD_ID;
const company_name = captured.company_name;
const company_url = captured.company_url;
const description = captured.description;
const source = captured.source;
const existing_dq_reasons = captured.existing_dq_reasons || '';
const existing_employee_count = captured.existing_employee_count || null;
const existing_stage = captured.existing_stage || null;
const existing_score = captured.existing_score || 0;
const existing_founded_year = captured.existing_founded_year || null;
const existing_total_funding = captured.existing_total_funding || null;

const isRescore = (existing_score === 0 || existing_score === null) && existing_dq_reasons.length > 0;

const braveResponse = $json;
const searchResults = braveResponse?.web?.results || [];
const currentYear = new Date().getFullYear();

// === SCOPED RESULT FILTERING ===
const companyNameLower = company_name.toLowerCase().trim();
const companyNameNormalized = companyNameLower.replace(/[^a-z0-9]/g, '');

const isAboutTargetCompany = (result) => {
  const title = (result.title || '').toLowerCase();
  const url = (result.url || '').toLowerCase();
  const desc = (result.description || '').toLowerCase();

  const titleHasName = title.includes(companyNameLower) ||
                       title.includes(companyNameNormalized);

  const urlDomain = url.replace(/^https?:\/\//, '').split('/')[0].replace('www.', '');
  const domainHasName = urlDomain.includes(companyNameNormalized) ||
                        companyNameNormalized.includes(urlDomain.replace(/\.(com|io|co|org|net)$/, ''));

  const companyDomain = (company_url || '').toLowerCase().replace(/^https?:\/\//, '').split('/')[0].replace('www.', '');
  const isCompanySite = companyDomain && url.includes(companyDomain);

  const descStartsWithName = desc.startsWith(companyNameLower) ||
                             desc.match(new RegExp('^' + companyNameLower.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\b', 'i'));

  return titleHasName || domainHasName || isCompanySite || descStartsWithName;
};

const companyResults = searchResults.filter(isAboutTargetCompany);
const allResults = searchResults;

const companyText = companyResults.map(r => (r.title || '') + ' ' + (r.description || '')).join(' ');
const allText = allResults.map(r => (r.title || '') + ' ' + (r.description || '')).join(' ');

// === PE, SECTOR, STATUS DETECTION ===
// v4.8.2: Added New Mountain Capital, Marlin Equity, Alpine Investors, Norwest Equity
const peFirms = [
  'Vista Equity', 'Thoma Bravo', 'KKR', 'Blackstone', 'TPG', 'Carlyle',
  'Bain Capital', 'Silver Lake', 'Francisco Partners', 'Accel-KKR',
  'LLR Partners', 'Warburg Pincus', 'Apollo', 'Insight Partners', 'GTCR',
  'Clearlake', 'Welsh Carson', 'Providence Equity', 'Leonard Green',
  'Hellman & Friedman', 'Advent', 'Golden Gate Capital', 'TA Associates',
  'Brighton Park Capital', 'General Atlantic', 'Summit Partners', 'SoftBank Vision Fund',
  'EQT Partners', 'Permira', 'Jonas Software', 'Constellation Software', 'Volaris',
  'Harris Computer', 'Total Specific Solutions', 'N. Harris Computer',
  'Ares Management', 'Ares Capital', 'Spring Lake Equity', 'Vector Capital',
  // v4.8.2 additions
  'New Mountain Capital', 'New Mountain', 'Marlin Equity', 'Alpine Investors',
  'Norwest Equity', 'JMI Equity', 'Riverside Company', 'K1 Investment Management',
  'Mainsail Partners', 'Level Equity', 'Luminate Capital', 'Updata Partners'
];

const knownLargeCompanies = [
  'Zapier', 'SnapLogic', 'Stripe', 'Notion', 'Figma', 'Canva',
  'Airtable', 'Webflow', 'Monday.com', 'Asana', 'Modern Treasury',
  'Plaid', 'Brex', 'Ramp', 'Gusto', 'Rippling', 'Deel'
];

const knownOldCompanies = [
  { name: 'InternMatch', founded: 2009 },
  { name: 'VoltServer', founded: 2011 },
  { name: 'Mighty Networks', founded: 2010 },
  { name: 'Helcim', founded: 2006 },
  { name: 'Zapier', founded: 2011 },
  { name: 'Mailchimp', founded: 2001 },
  { name: 'HubSpot', founded: 2006 },
  { name: 'Zendesk', founded: 2007 },
  { name: 'Intercom', founded: 2011 },
  { name: 'Drift', founded: 2015 },
  { name: 'Pendo', founded: 2013 },
  { name: 'Gainsight', founded: 2011 },
  { name: 'Mixpanel', founded: 2009 },
  { name: 'Amplitude', founded: 2012 },
  { name: 'Segment', founded: 2011 },
  { name: 'Twilio', founded: 2008 },
  { name: 'SendGrid', founded: 2009 },
  { name: 'Clearbit', founded: 2014 }
];

const CX_TOOLING_KEYWORDS = [
  'cobrowsing', 'session replay', 'helpdesk', 'ticketing',
  'chatbot', 'customer support software', 'live chat',
  'contact center', 'support automation', 'knowledge base software',
  'customer service platform', 'help desk software', 'support ticketing'
];

// Helpers
const parseFundingAmount = (amountStr, unitStr) => {
  const amount = parseFloat(amountStr);
  const unit = unitStr.toLowerCase();
  if (unit === 'billion' || unit === 'b') return amount * 1000000000;
  if (unit === 'million' || unit === 'm') return amount * 1000000;
  return amount;
};

const formatFunding = (numeric) => {
  if (numeric >= 1000000000) return '$' + (numeric / 1000000000).toFixed(1) + 'B';
  if (numeric >= 1000000) return '$' + (numeric / 1000000).toFixed(1) + 'M';
  return '$' + numeric;
};

const median = (arr) => {
  if (arr.length === 0) return null;
  const sorted = [...arr].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 !== 0 ? sorted[mid] : Math.round((sorted[mid - 1] + sorted[mid]) / 2);
};

// === FUNDING STAGE DETECTION (needed for sanity bounds) ===
let fundingStage = null;
if (/Series\s*E/i.test(companyText)) fundingStage = 'Series E';
else if (/Series\s*D/i.test(companyText)) fundingStage = 'Series D';
else if (/Series\s*C/i.test(companyText)) fundingStage = 'Series C';
else if (/Series\s*B/i.test(companyText)) fundingStage = 'Series B';
else if (/Series\s*A/i.test(companyText)) fundingStage = 'Series A';
else if (/\bSeed\b/i.test(companyText)) fundingStage = 'Seed';

if (!fundingStage && existing_stage) {
  fundingStage = existing_stage;
}

// === SANITY BOUNDS DEFINITIONS ===
const stageMaxEmployees = {
  'Seed': 100,
  'Series A': 250,
  'Series B': 600,
  'Series C': 1500,
  'Series D': 3000,
  'Series E': 5000
};
const maxEmployeesForStage = stageMaxEmployees[fundingStage] || 2000;

const stageFundingCaps = {
  'Seed': 30000000,
  'Series A': 100000000,
  'Series B': 300000000,
  'Series C': 750000000,
  'Series D': 1500000000,
  'Series E': 3000000000
};
const maxFundingForStage = stageFundingCaps[fundingStage] || 500000000;

// Sanity check helper functions
const passesEmployeeSanity = (count) => {
  if (count === null || count === undefined) return false;
  return count > 0 && count <= maxEmployeesForStage;
};

const passesFundingSanity = (funding) => {
  if (funding === null || funding === undefined) return false;
  return funding > 0 && funding <= maxFundingForStage;
};

const passesFoundedYearSanity = (year) => {
  if (year === null || year === undefined) return false;
  const age = currentYear - year;
  return year >= 1980 && year <= currentYear && age <= 15;
};

// === EMPLOYEE COUNT EXTRACTION WITH REFINED SANITY ===
const empMatches = [...companyText.matchAll(/(\d[\d,]*)\s*(?:to\s*\d[\d,]*)?\s*employees?/gi)];
let extractedEmpCounts = empMatches.map(m => parseInt(m[1].replace(/,/g, ''))).filter(n => n > 0 && n < 100000);

// Range detection
const rangeMatch = companyText.match(/(\d+)\s*(?:to|-)\s*(\d+)\s*employees?/i);
if (rangeMatch && extractedEmpCounts.length === 0) {
  const upper = parseInt(rangeMatch[2]);
  if (upper > 0 && upper < 100000) {
    extractedEmpCounts.push(upper);
  }
}

// Get median of extracted values
let extractedEmployeeCount = extractedEmpCounts.length > 0
  ? (extractedEmpCounts.length > 1 ? median(extractedEmpCounts) : extractedEmpCounts[0])
  : null;
const employeeCountCorroborated = extractedEmpCounts.length >= 2;

// REFINED SANITY CHECK - check both extracted and Airtable
let employeeCount = null;
let employeeCountSource = 'none';

if (extractedEmployeeCount && passesEmployeeSanity(extractedEmployeeCount)) {
  employeeCount = extractedEmployeeCount;
  employeeCountSource = 'extracted';
} else if (existing_employee_count && passesEmployeeSanity(existing_employee_count)) {
  employeeCount = existing_employee_count;
  employeeCountSource = 'airtable_fallback';
} else {
  employeeCount = null;
  employeeCountSource = 'cleared';
}

// Additional trust check: if extracted but not corroborated and high, be cautious
let employeeCountTrusted = true;
if (employeeCountSource === 'extracted' && !employeeCountCorroborated && employeeCount > 200) {
  if (existing_employee_count && passesEmployeeSanity(existing_employee_count) && existing_employee_count !== extractedEmployeeCount) {
    employeeCount = existing_employee_count;
    employeeCountSource = 'airtable_preferred';
    employeeCountTrusted = false;
  }
}

// === FUNDING EXTRACTION WITH REFINED SANITY ===
let totalFunding = null, totalFundingRaw = null;
let fundingSource = 'none';

const fundingMatch = companyText.match(/(?:raised|funding|total funding)\s*\$?([\d.]+)\s*(million|billion|M|B)/i);
let extractedFunding = null;
if (fundingMatch) {
  extractedFunding = parseFundingAmount(fundingMatch[1], fundingMatch[2]);
}

// Parse existing funding from Airtable (might be string like "$41.0M")
let existingFundingNumeric = null;
if (existing_total_funding) {
  const existingMatch = existing_total_funding.match(/\$?([\d.]+)\s*(million|billion|M|B)/i);
  if (existingMatch) {
    existingFundingNumeric = parseFundingAmount(existingMatch[1], existingMatch[2]);
  }
}

// REFINED SANITY CHECK
if (extractedFunding && passesFundingSanity(extractedFunding)) {
  totalFunding = extractedFunding;
  totalFundingRaw = formatFunding(totalFunding);
  fundingSource = 'extracted';
} else if (existingFundingNumeric && passesFundingSanity(existingFundingNumeric)) {
  totalFunding = existingFundingNumeric;
  totalFundingRaw = formatFunding(totalFunding);
  fundingSource = 'airtable_fallback';
} else {
  totalFunding = null;
  totalFundingRaw = null;
  fundingSource = 'cleared';
}

// === VALUATION EXTRACTION ===
let valuation = null, valuationRaw = null;

const unicornInCompanyResults = companyResults.some(r => {
  const text = ((r.title || '') + ' ' + (r.description || '')).toLowerCase();
  return text.includes('unicorn') && text.includes(companyNameLower);
});

if (unicornInCompanyResults) {
  valuation = 1000000000;
  valuationRaw = '$1.0B (unicorn)';
} else {
  const valuationMatch = companyText.match(/(?:valued at|valuation of?)\s*\$?([\d.]+)\s*(million|billion|M|B)/i);
  if (valuationMatch) {
    valuation = parseFundingAmount(valuationMatch[1], valuationMatch[2]);
    valuationRaw = formatFunding(valuation);
  }
}

// === FOUNDED YEAR EXTRACTION WITH REFINED SANITY ===
let foundedYear = null;
let foundedYearSource = 'none';

const knownOldMatch = knownOldCompanies.find(c => company_name && company_name.toLowerCase().includes(c.name.toLowerCase()));
let extractedFoundedYear = null;

if (knownOldMatch) {
  extractedFoundedYear = knownOldMatch.founded;
} else {
  const foundMatch = companyText.match(/(?:founded|established|since)\s*(?:in)?\s*(20\d{2}|19\d{2})/i);
  if (foundMatch) {
    const year = parseInt(foundMatch[1]);
    if (year >= 1980 && year <= currentYear) {
      extractedFoundedYear = year;
    }
  }
}

// REFINED SANITY CHECK
if (extractedFoundedYear && passesFoundedYearSanity(extractedFoundedYear)) {
  foundedYear = extractedFoundedYear;
  foundedYearSource = 'extracted';
} else if (existing_founded_year && passesFoundedYearSanity(existing_founded_year)) {
  foundedYear = existing_founded_year;
  foundedYearSource = 'airtable_fallback';
} else {
  foundedYear = null;
  foundedYearSource = 'cleared';
}

const companyAge = foundedYear ? (currentYear - foundedYear) : null;
const isTooOld = companyAge !== null && companyAge > 8;
const isAgingFlag = companyAge !== null && companyAge > 5 && companyAge <= 8;
const isKnownOldCompany = knownOldMatch !== undefined;

// === REST OF EXTRACTION ===
const fundingStageRank = { 'Pre-Seed': 1, 'Seed': 2, 'Series A': 3, 'Series B': 4, 'Series C': 5, 'Series D': 6, 'Series E': 7 };
let suspiciousEmployeeCount = false;
let employeeCountFlag = null;

const isSeriesAPlus = fundingStage && fundingStageRank[fundingStage] >= 3;
const hasSignificantFunding = totalFunding && totalFunding >= 10000000;
if (employeeCount && employeeCount < 15 && (isSeriesAPlus || hasSignificantFunding)) {
  suspiciousEmployeeCount = true;
  employeeCountFlag = 'Employee count ' + employeeCount + ' seems low for ' + (fundingStage || 'significant funding') + ' with ' + (totalFundingRaw || '>$10M');
}

// Funding recency
let lastFundingYear = null;
let yearsSinceLastRound = null;
let fundingRecency = null;
const fundingYearPatterns = [
  /series\s*[a-e]\s*(?:round\s*)?(?:in\s*)?(20\d{2})/i,
  /raised.*?(20\d{2})/i,
  /(20\d{2}).*?series\s*[a-e]/i,
  /(?:funding|round).*?(20\d{2})/i
];
for (const pattern of fundingYearPatterns) {
  const match = companyText.match(pattern);
  if (match) {
    const year = parseInt(match[1]);
    if (year >= 2015 && year <= currentYear && (!lastFundingYear || year > lastFundingYear)) {
      lastFundingYear = year;
    }
  }
}
if (lastFundingYear) {
  yearsSinceLastRound = currentYear - lastFundingYear;
  if (yearsSinceLastRound < 1) fundingRecency = 'recent';
  else if (yearsSinceLastRound < 2) fundingRecency = 'moderate';
  else if (yearsSinceLastRound < 3) fundingRecency = 'aging';
  else fundingRecency = 'stale';
}

const isEarlyStage = ['Seed', 'Series A'].includes(fundingStage);
let fundingStalenessModifier = 0;
if (yearsSinceLastRound && isEarlyStage && (!employeeCount || employeeCount < 100)) {
  if (yearsSinceLastRound >= 4) fundingStalenessModifier = -15;
  else if (yearsSinceLastRound >= 3) fundingStalenessModifier = -10;
  else if (yearsSinceLastRound >= 2) fundingStalenessModifier = -5;
}

// CX Tooling Detection
let isCXToolingCompany = false;
let cxToolingSignals = [];
const allTextLower = allText.toLowerCase();
for (const keyword of CX_TOOLING_KEYWORDS) {
  if (allTextLower.includes(keyword.toLowerCase())) {
    cxToolingSignals.push(keyword);
  }
}
isCXToolingCompany = cxToolingSignals.length >= 2;

// Rebuild signal detection
let rebuildSignal = false;
let rebuildLeader = null;
let rebuildLeaderStart = null;
const isInRebuildRange = employeeCount && employeeCount >= 100 && employeeCount <= 300;
if (isInRebuildRange) {
  const rebuildPatterns = [
    /(?:hired|appointed|welcomed|joined|named)\s+(?:as\s+)?(?:our\s+)?(?:new\s+)?(?:CCO|Chief Customer Officer|VP (?:of )?Customer (?:Success|Experience)|Head of Customer (?:Success|Experience)|VP CS|VP CX|Chief Customer|Chief Experience Officer)/gi,
    /(?:CCO|Chief Customer Officer|VP (?:of )?Customer (?:Success|Experience)|Head of Customer (?:Success|Experience))\s+(?:hired|appointed|joined|started|welcomes|announced)/gi,
    /new (?:CCO|Chief Customer Officer|VP (?:of )?Customer|Head of Customer)/gi,
    /(?:joins|joined)\s+(?:as|the company as)\s+(?:CCO|Chief Customer Officer|VP (?:of )?Customer|Head of Customer)/gi
  ];
  for (const pattern of rebuildPatterns) {
    const match = companyText.match(pattern);
    if (match) {
      rebuildSignal = true;
      rebuildLeader = match[0].substring(0, 100);
      break;
    }
  }
}

// === v4.8.2: ENHANCED PE + ACQUISITION DETECTION ===
const isPEBackedByName = peFirms.some(f => new RegExp(f, 'i').test(allText));
const peBackerFoundByName = peFirms.find(f => new RegExp(f, 'i').test(allText)) || null;

// Acquisition pattern detection
const acquisitionPatterns = [
  /acquired by\s+([A-Z][A-Za-z\s&]+(?:Capital|Partners|Equity|Investment|Management))/gi,
  /(?:acquisition|acquired|bought)\s+by\s+([A-Z][A-Za-z\s&]+)/gi,
  /([A-Z][A-Za-z\s&]+(?:Capital|Partners|Equity))\s+(?:acquires|acquired|to acquire)/gi,
  /majority (?:stake|investment|ownership)\s+(?:by|from)\s+([A-Z][A-Za-z\s&]+)/gi,
  /(?:private equity|PE)\s+(?:firm|group|fund)\s+([A-Z][A-Za-z\s&]+)/gi
];

let acquisitionDetected = false;
let acquirerName = null;

for (const pattern of acquisitionPatterns) {
  const matches = [...allText.matchAll(pattern)];
  for (const match of matches) {
    const potentialAcquirer = match[1]?.trim();
    if (potentialAcquirer && potentialAcquirer.length > 3) {
      const isPEAcquirer = peFirms.some(f => potentialAcquirer.toLowerCase().includes(f.toLowerCase()));
      const hasPENaming = /(?:Capital|Partners|Equity|Investment|Management)$/i.test(potentialAcquirer);

      if (isPEAcquirer || hasPENaming) {
        acquisitionDetected = true;
        acquirerName = potentialAcquirer;
        break;
      }
    }
  }
  if (acquisitionDetected) break;
}

const isPEBacked = isPEBackedByName || acquisitionDetected;
const peBackerFound = peBackerFoundByName || acquirerName;

const isKnownLargeCompany = knownLargeCompanies.some(name =>
  company_name && company_name.toLowerCase().includes(name.toLowerCase())
);

// Status detection
const isAcquired = /\b(acquired|was acquired|acquisition|merged with|bought by|shut down|defunct)\b/i.test(companyText);
const isPublic = /\b(NYSE|NASDAQ|publicly traded|IPO|went public|stock ticker)\b/i.test(companyText);

// === v4.8.3: EXPANDED HARDWARE/DEEPTECH DETECTION ===
// Original hardware keywords
const hardwareKeywordsBasic = /\b(hardware|sensors|devices|robotics|manufacturing|semiconductor|solar|battery|EV charging)\b/i;

// v4.8.3: New deeptech/infrastructure keywords (catches Veir, Last Energy)
const hardwareKeywordsExpanded = /\b(power transmission|power lines|superconducting|grid infrastructure|energy infrastructure|utility infrastructure|modular nuclear|nuclear reactor|nuclear power|pilot deployment|physical infrastructure|transmission lines|high voltage|electrical grid|substation|transformer|cable manufacturing|industrial equipment)\b/i;

// Combined check: either keyword set triggers, as long as not clearly SaaS
const hasHardwareSignals = hardwareKeywordsBasic.test(allText) || hardwareKeywordsExpanded.test(allText);
const hasSaaSSignals = /\b(SaaS|software platform|cloud platform|API|software-as-a-service)\b/i.test(allText);
const isHardware = hasHardwareSignals && !hasSaaSSignals;

// Capture which hardware signals triggered (for debugging)
let hardwareSignalsFound = [];
if (hardwareKeywordsBasic.test(allText)) {
  const match = allText.match(hardwareKeywordsBasic);
  if (match) hardwareSignalsFound.push(match[0]);
}
if (hardwareKeywordsExpanded.test(allText)) {
  const match = allText.match(hardwareKeywordsExpanded);
  if (match) hardwareSignalsFound.push(match[0]);
}

// Other sector detection (unchanged)
const isBiotech = /\b(therapeutic|drug development|clinical trial|pharma|biotech|oncology|immunotherapy)\b/i.test(allText);
const isCrypto = /\b(blockchain|cryptocurrency|web3|NFT|DeFi|token|crypto|decentralized)\b/i.test(allText);
const isConsumer = /\b(consumer app|DTC|direct-to-consumer|B2C|telehealth|patient app|consumer health)\b/i.test(allText);
const isHRTech = /\b(HR tech|human resources|DEI|diversity equity|workforce analytics|recruiting platform|HRIS|payroll)\b/i.test(allText);
const isMarketplace = /\b(marketplace|two-sided market|gig economy|freelance platform|labor marketplace)\b/i.test(allText) && !/\b(SaaS|software platform|enterprise)\b/i.test(allText);
const isFintech = /\b(fintech|banking software|credit union|neobank|payment processing|lending platform|loan origination|mortgage tech|banking as a service|BaaS|open banking|core banking)\b/i.test(allText) && !/\b(healthcare billing|medical billing|revenue cycle)\b/i.test(allText);
const isConstructionTech = /\b(construction (?:tech|software|management)|general contractor|subcontractor management|job site|building information|BIM software)\b/i.test(allText);
const isFoodBiotech = /\b(fermentation|food science|food tech|cultured (?:meat|protein)|alternative protein|CPG brand|consumer packaged goods|beverage brand)\b/i.test(allText);
const isPhysicalSecurity = /\b(physical security|access control|surveillance|security camera|weapon detection|metal detector|perimeter security)\b/i.test(allText) && !/\b(cybersecurity|data security|cloud security)\b/i.test(allText);
const isInsurtech = /\b(insurtech|insurance (?:technology|software|platform)|policy management|claims processing|underwriting)\b/i.test(allText) && !/\b(healthcare|health plan|benefits administration)\b/i.test(allText);
const isSaaSManagement = /\b(SaaS management|software spend|IT asset management|license management|shadow IT|SaaS operations)\b/i.test(allText);
const isConsumerDigitalHealth = /\b(mental health app|therapy app|meditation app|wellness app|patient (?:portal|app)|health coaching app|digital therapeutic|DTx|fertility app|pregnancy app)\b/i.test(allText) && !/\b(provider-facing|clinician-facing|EHR|clinical workflow)\b/i.test(allText);

// GTM Motion detection
const plgSignals = [
  /free (?:tier|plan|trial)/i,
  /self[\s-]?serve/i,
  /product[\s-]?led/i,
  /freemium/i,
  /open[\s-]?source/i,
  /sign up free/i
];
const enterpriseSignals = [
  /enterprise (?:sales|team|customers)/i,
  /account (?:executive|manager)/i,
  /sales[\s-]?led/i,
  /high[\s-]?touch/i,
  /customer success (?:team|manager)/i,
  /enterprise[\s-]?grade/i
];
const plgSignalCount = plgSignals.filter(p => p.test(allText)).length;
const enterpriseSignalCount = enterpriseSignals.filter(p => p.test(allText)).length;
const isPLGDominant = plgSignalCount >= 3 && enterpriseSignalCount < 2;

// === v4.8.3: HEADCOUNT-TO-FUNDING RATIO DETECTION ===
// Catches companies like Gumloop: $70M raised / 24 employees = $2.9M per head
// A company with extreme funding-per-head doesn't need CS leadership yet
// They need sales and engineering, not support infrastructure

let fundingPerHead = null;
let isExtremeFundingRatio = false;
let fundingRatioFlag = null;

if (totalFunding && employeeCount && employeeCount > 0) {
  fundingPerHead = totalFunding / employeeCount;

  // Thresholds:
  // - Normal early stage: ~$500K-$1M per head
  // - High but reasonable: $1M-$2M per head
  // - Extreme (no CS need): >$2M per head at <50 employees
  //
  // At <50 employees with >$2M/head, they're in "scaling sales/product" mode
  // not "building CS infrastructure" mode

  if (employeeCount < 50 && fundingPerHead > 2000000) {
    isExtremeFundingRatio = true;
    fundingRatioFlag = 'Extreme funding/headcount ratio: ' + formatFunding(totalFunding) + ' / ' + employeeCount + ' emp = ' + formatFunding(fundingPerHead) + '/head (no CS need yet)';
  }
}

// === DISQUALIFIERS ===
const disqualifiers = [];
const flagsForReview = [];

if (!isRescore && existing_dq_reasons.length > 0) {
  if (!existing_dq_reasons.startsWith('Pre-existing DQ:')) {
    disqualifiers.push('Pre-existing DQ: ' + existing_dq_reasons);
  } else {
    disqualifiers.push(existing_dq_reasons);
  }
}

// v4.12: Only run detection if no pre-existing DQ reasons
// This prevents duplicate DQ reasons from accumulating on rescore runs
if (!existing_dq_reasons || existing_dq_reasons.length === 0) {

// === TIER 1: HARD GATES ===
if (isAcquired) disqualifiers.push('Acquired');
if (isPEBacked) {
  if (acquisitionDetected) {
    disqualifiers.push('PE-acquired (' + acquirerName + ')');
  } else {
    disqualifiers.push('PE-backed (' + peBackerFound + ')');
  }
}
if (isKnownLargeCompany) disqualifiers.push('Known large company (enrichment bypass)');

// v4.8.2: Employee cap at 150
if (employeeCount && employeeCount > 150) {
  disqualifiers.push('Too large (>' + 150 + ' employees: ' + employeeCount + ')');
} else if (suspiciousEmployeeCount) {
  flagsForReview.push(employeeCountFlag);
}

// v4.8.2: Funding cap at $75M
if (totalFunding && totalFunding > 75000000) {
  disqualifiers.push('>$75M funding (' + totalFundingRaw + ')');
}

if (valuation && valuation >= 1000000000) {
  disqualifiers.push('Unicorn valuation (>$1B: ' + valuationRaw + ')');
} else if (valuation && valuation > 500000000) {
  disqualifiers.push('>$500M valuation (' + valuationRaw + ')');
}

if (isPublic) disqualifiers.push('Public company');
if (['Series D', 'Series E'].includes(fundingStage)) disqualifiers.push('Late stage (' + fundingStage + ')');
if (isTooOld) disqualifiers.push('Company too old (' + companyAge + ' years)');

// === TIER 2: SECTOR GATES ===
if (isBiotech) disqualifiers.push('Biotech/pharma');
if (isHardware) disqualifiers.push('Hardware/deeptech (' + hardwareSignalsFound.join(', ') + ')');
if (isCrypto) disqualifiers.push('Crypto/Web3');
if (isConsumer) disqualifiers.push('Consumer/B2C');
if (isHRTech) disqualifiers.push('HR Tech');
if (isMarketplace) disqualifiers.push('Marketplace');
if (isFintech) disqualifiers.push('Fintech/Banking (wrong sector)');
if (isConstructionTech) disqualifiers.push('Construction Tech (wrong sector)');
if (isFoodBiotech) disqualifiers.push('Food science/CPG (not B2B SaaS)');
if (isPhysicalSecurity) disqualifiers.push('Physical security hardware (wrong sector)');
if (isInsurtech) disqualifiers.push('Insurtech (wrong sector)');
if (isSaaSManagement) disqualifiers.push('SaaS management (wrong buyer persona)');
if (isConsumerDigitalHealth) disqualifiers.push('Consumer digital health (patient-facing)');

// === TIER 3: GTM MOTION GATES ===
if (isPLGDominant) disqualifiers.push('PLG-dominant (no enterprise CS need)');

// v4.8.3: Extreme funding ratio gate
if (isExtremeFundingRatio) {
  disqualifiers.push('Extreme funding/headcount ratio (no CS need at this stage)');
}

} // End v4.12 detection skip block

// Headcount penalty modifier (for companies under the hard cap)
let headcountPenaltyModifier = 0;
if (employeeCount && employeeCount >= 100 && employeeCount <= 150) {
  if (rebuildSignal) {
    headcountPenaltyModifier = 0;
  } else {
    headcountPenaltyModifier = -10;
  }
}

// Warnings
const warnings = [];
if (employeeCount && employeeCount < 15 && !suspiciousEmployeeCount) warnings.push('Early stage (<15 employees) - monitor for growth');
if (isAgingFlag) warnings.push('Company aging (' + companyAge + ' years old)');
if (employeeCount && employeeCount >= 100 && employeeCount <= 150) {
  if (rebuildSignal) {
    warnings.push('Employee count ' + employeeCount + ' in upper range - no penalty (rebuild signal detected)');
  } else {
    warnings.push('Employee count ' + employeeCount + ' in penalty zone (-10 modifier)');
  }
}
if (fundingRecency === 'stale') warnings.push('Stale funding (' + yearsSinceLastRound + ' years since last round)');
if (isCXToolingCompany) warnings.push('CX tooling company (sells TO support teams): ' + cxToolingSignals.join(', '));

// Source tracking warnings
if (employeeCountSource === 'cleared') warnings.push('Employee count cleared (both extracted and Airtable failed sanity)');
if (employeeCountSource === 'airtable_fallback') warnings.push('Employee count from Airtable (extracted failed sanity)');
if (fundingSource === 'cleared') warnings.push('Funding cleared (both extracted and Airtable failed sanity)');
if (foundedYearSource === 'cleared') warnings.push('Founded year cleared (both extracted and Airtable failed sanity)');

// v4.8.2: Acquisition detection warning
if (acquisitionDetected) warnings.push('Acquisition detected: ' + acquirerName);

// v4.8.3: Funding ratio warning (even if not DQ'd)
if (fundingPerHead && fundingPerHead > 1500000 && !isExtremeFundingRatio) {
  warnings.push('High funding/headcount ratio: ' + formatFunding(fundingPerHead) + '/head');
}

return {
  json: {
    RECORD_ID: RECORD_ID,
    company_name: company_name,
    company_url: company_url,
    description: description,
    source: source,
    funding_stage: fundingStage,
    total_funding: totalFundingRaw,
    total_funding_numeric: totalFunding,
    valuation: valuationRaw,
    valuation_numeric: valuation,
    employee_count: employeeCount,
    employee_count_corroborated: employeeCountCorroborated,
    employee_count_trusted: employeeCountTrusted,
    suspicious_employee_count: suspiciousEmployeeCount,
    employee_count_flag: employeeCountFlag,
    pe_backed: isPEBacked,
    pe_acquisition_detected: acquisitionDetected,
    acquirer_name: acquirerName,
    founded_year: foundedYear,
    company_age: companyAge,
    is_too_old: isTooOld,
    is_aging_flag: isAgingFlag,
    is_known_large_company: isKnownLargeCompany,
    is_plg_dominant: isPLGDominant,
    is_hardware: isHardware,
    hardware_signals: hardwareSignalsFound.join(', '),
    last_funding_year: lastFundingYear,
    years_since_last_round: yearsSinceLastRound,
    funding_recency: fundingRecency,
    funding_staleness_modifier: fundingStalenessModifier,
    // v4.8.3: Funding ratio fields
    funding_per_head: fundingPerHead,
    funding_per_head_formatted: fundingPerHead ? formatFunding(fundingPerHead) + '/head' : null,
    is_extreme_funding_ratio: isExtremeFundingRatio,
    funding_ratio_flag: fundingRatioFlag,
    is_cx_tooling_company: isCXToolingCompany,
    cx_tooling_signals: cxToolingSignals.join(', '),
    rebuild_signal: rebuildSignal,
    rebuild_leader: rebuildLeader,
    rebuild_leader_start: rebuildLeaderStart,
    headcount_penalty_modifier: headcountPenaltyModifier,
    flags_for_review: flagsForReview.join('; '),
    disqualify_reasons: disqualifiers.join('; '),
    isAutoDisqualified: disqualifiers.length > 0,
    warnings: warnings,
    // Debug info
    _companyResultsCount: companyResults.length,
    _totalResultsCount: searchResults.length,
    _employeeCountSource: employeeCountSource,
    _fundingSource: fundingSource,
    _foundedYearSource: foundedYearSource,
    _version: '4.12'
  }
};
