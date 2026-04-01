# Review Context: Tide Pool Job Search System

## Project Summary
AI-powered job search automation. VC portfolio scrapers and job board parsers feed companies/jobs through enrichment (Brave Search API) and scoring (Claude Haiku) pipelines, storing results in Airtable. Built on n8n cloud.

## Airtable
Base: appFEzXvPWvRtXgRY
- Funding Alerts (tbl7yU6QYfIFSC2nD): Company evaluations from VC scrapers
- Job Listings (tbl6ZV2rHjWz56pP3): Job evaluations from job scrapers
- Seen Opportunities (tbll8igHTftSqsTtQ): Cross-source dedup (BUG: not being populated by Dedup Register)
- LinkedIn Connections (tbliKHRPEVI6SceJX): Network matching (feature disabled in v9)
- Config (tblofzQpzGEN8igVS): Gate thresholds for config-driven architecture
- PE Firms (tblU2izcb0wnCNMuV): 43 PE/Growth Equity firms with aliases

## Key Workflow IDs
- E&E Pipeline v9.17: rcMNDrfZR6csHRsYKFn0W
- Job Eval Pipeline v6.8: v24qHkIsp8GVCwFkscHP8
- Dedup Check: bBjeG_RXRI10eAA5TiN7n
- Dedup Register: MDzcHPZMySqn1DrGh8J0- (BUG: not writing to Seen Opportunities)
- Config Fetcher: aCym9UVO8b7Lz2Lt
- Rescore v4.15: standalone, runs every 2 min

## Candidate Profile
- Target: VP/Director/Head of CS at VC-backed B2B SaaS, Series A/B, 20-150 employees
- 13 years at Bigtincan as founding CS hire, built 0-to-25 global team across 3 continents
- Domains: enterprise SaaS, healthcare tech, AI platforms, regulated industries
- Customer scale: 250+ Fortune 1000 accounts, 2M+ users, 15K+ annual cases, 93%+ CSAT
- Hard rules: No PE-backed, no NRR-first framing, no developer-as-customer without enterprise motion

## Never Claim (Hard Rules)
- No 25% cost-per-contact reduction (false metric)
- No Lean/Six Sigma (no training)
- No "3 data centers" (Bigtincan was not self-hosted)
- KB/self-service deflection was weak (no deflection wins)

## Tech Stack
n8n cloud (zelman.app.n8n.cloud), Claude Haiku 4.5 (scoring), Brave Search API (enrichment), Browserless.io (scraping), Airtable (storage), GitHub (code)

## Known Bugs
1. Dedup Register subworkflow not writing to Seen Opportunities table
2. Airtable batch node scrambles record IDs (use HTTP Request for PATCH)
3. Network Match Alerts disabled (duplicate record bug from parallel merge paths)

## Current Status (April 2026)
- E&E Pipeline: v9.17 (Pre-Brave Gate added)
- Rescore: v4.15 (isRescore bug fix)
- Job Eval: v6.8 (isPEBacked order fix)
- Brave API cost reduction in progress (Tiers 1 & 2 done, Tier 1.5 partial, Tier 3 pending)
- Dual-source dedup deployed to Growth Stage, Healthcare, Enterprise scrapers
- Still needed: Micro-VC, Social Justice, Climate Tech, Lightspeed
