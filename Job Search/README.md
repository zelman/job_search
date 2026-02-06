# VC Portfolio Scraper

An n8n workflow that automatically scrapes portfolio companies from mission-aligned venture capital firms, classifies them using Claude AI, and adds them to Airtable for job search tracking.

## Features

- Scrapes portfolio pages from 6 VC firms
- Deduplicates against existing Airtable records
- AI-powered classification via Anthropic Claude API:
  - Industry/vertical detection
  - Company stage detection (Seed/Early, Growth, Late/Public)
  - Mission alignment scoring (1-5 scale)
- Automated scheduling (Mon/Thu at 8am)

## Supported VCs

| VC Firm | Method | Focus |
|---------|--------|-------|
| Unusual Ventures | Browserless | Enterprise, B2B |
| First Round Capital | Sanity CMS API | Seed stage |
| Essence VC | HTTP + HTML parsing | Early stage |
| Costanoa Ventures | Sitemap XML | Enterprise |
| Khosla Ventures | Browserless | Climate, cleantech, healthcare |
| Kapor Capital | Sitemap XML | Social impact, diversity |

## Stage Guide

- **Seed/Early**: New startup, pre-product or early product, small team, not widely known
- **Growth**: Scaling company, established product, Series B-D, growing but not dominant
- **Late/Public**: Large company, IPO'd, acquired by major company, or household name (e.g., Uber, DoorDash, Stripe)
- **Unknown**: Cannot determine stage

## Mission Score Guide

- **5**: Strong mission around healthcare, environment/climate, or education
- **4**: Moderate alignment with healthcare, environment, or education
- **3**: Neutral - general tech, enterprise software, consumer apps
- **2**: Lower priority - fintech, adtech, crypto
- **1**: Lowest priority - military, defense

## Requirements

- n8n (Cloud or self-hosted)
- Browserless.io account (for JS-rendered pages)
- Anthropic API key (for Claude classification)
- Airtable base with "Funding Alerts" table

## Airtable Schema

Required fields:
- Company Name (text)
- VC Firm (single select)
- Company Description (long text)
- Company URL (URL)
- Status (single select)
- First Seen Date (date)
- Source (single select)
- Industry (text)
- Stage (single select: Seed/Early, Growth, Late/Public, Unknown)
- Mission Score (number)
- Mission Notes (text)

## Setup

1. Import the JSON workflow into n8n
2. Configure credentials:
   - Browserless API token
   - Anthropic API key
   - Airtable API token
3. Add VC firm names to Airtable single select field
4. Test run the workflow
5. Enable the schedule trigger

## Files

- `VC Portfolio Scraper v17.json` - Current version with 6 VCs
- `VC Portfolio Scraper v16.json` - Previous version with 4 VCs
