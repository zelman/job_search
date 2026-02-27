# VC Scraper Expansion: Green Energy, Healthcare & Social Justice

## Context
This document extends an existing VC portfolio scraper that monitors early-stage (seed / Series A / pre-Series A) SaaS investments. The goal is to detect new portfolio additions as early as possible so the user can target ground-floor support/ops roles at nascent startups.

The existing scraper already covers 15 VC firms + 2 job board sources using a mix of scrape methods: Browserless, HTTP GET, Sitemap XML, and Sanity API. See the existing codebase for patterns and conventions.

---

## New VC Targets

### Green Energy / Climate Tech

| # | VC Firm | Portfolio URL | Likely Scrape Method | Notes |
|---|---------|--------------|---------------------|-------|
| 1 | Congruent Ventures | https://congruent.vc/portfolio | HTTP GET or Sitemap | Seed/Series A climate tech, SF-based. SaaS-friendly. Clean portfolio page. |
| 2 | Clean Energy Ventures | https://cleanenergyventures.com/portfolio/ | HTTP GET | Early-stage clean energy/decarbonization, Boston-based. |
| 3 | Prelude Ventures | https://www.preludeventures.com/portfolio | HTTP GET or Sitemap | Climate/sustainability, seed–Series B. Well-structured portfolio page. |
| 4 | Lowercarbon Capital | https://lowercarboncapital.com/companies/ | Browserless | Chris Sacca's climate fund. JS-heavy site, likely needs headless browser. |
| 5 | Energize Capital | https://www.energizecap.com/portfolio | HTTP GET | Energy transition software/services, Chicago-based. Good descriptions for SaaS filtering. |

### Healthcare

| # | VC Firm | Portfolio URL | Likely Scrape Method | Notes |
|---|---------|--------------|---------------------|-------|
| 6 | Flare Capital Partners | https://www.flarecapital.com/portfolio | HTTP GET | Healthcare IT/SaaS, seed–Series A. High relevance for support ops roles. |
| 7 | 7wireVentures | https://7wireventures.com/portfolio/ | HTTP GET | Digital health, early stage, Chicago-based. |
| 8 | Define Ventures | https://www.defineventures.com/portfolio | HTTP GET or Browserless | Healthcare tech seed/Series A, SF-based. Founded by former Rock Health partner. |
| 9 | Oak HC/FT | https://www.oakhcft.com/portfolio | Browserless | Healthcare + fintech. Slightly later stage but catches companies at Series A. |
| 10 | Digitalis Ventures | https://www.digitalisventures.com/portfolio | HTTP GET | Digital health, early stage. Smaller fund = portfolio companies match target size. |

### Social Justice / Equity-Driven

| # | VC Firm | Portfolio URL | Likely Scrape Method | Notes |
|---|---------|--------------|---------------------|-------|
| 11 | Backstage Capital | https://backstagecapital.com/portfolio/ | HTTP GET or Browserless | Arlan Hamilton's fund. Invests exclusively in underrepresented founders (women, BIPOC, LGBTQ+). Early stage. |
| 12 | Harlem Capital | https://www.harlemcapital.com/portfolio | HTTP GET | Mission: invest in 1,000 diverse founders over 20 years. Seed/Series A. |
| 13 | Precursor Ventures | https://precursorvc.com/portfolio/ | HTTP GET | Charles Hudson's fund, strong commitment to underrepresented founders. Pre-seed/seed. |
| 14 | Impact America Fund | https://www.impactamericafund.com/portfolio | HTTP GET or Browserless | Invests in companies serving communities of color. Early stage, SaaS-friendly. |
| 15 | Collab Capital | https://www.collabcapital.com/portfolio | HTTP GET | Black-founded, invests in Black entrepreneurs. Atlanta-based, early stage. |
| 16 | Cleo Capital | https://www.cleocapital.com/portfolio | HTTP GET | Founded by Sarah Kunst, focuses on diverse founders. Pre-seed/seed. |
| 17 | Obvious Ventures | https://obvious.com/portfolio/ | HTTP GET or Browserless | "World positive" investments: health, sustainability, equity. Co-founded by Ev Williams. |

### Additional 10: Deepening Coverage

#### More Climate / Green Energy

| # | VC Firm | Portfolio URL | Likely Scrape Method | Notes |
|---|---------|--------------|---------------------|-------|
| 18 | Energy Impact Partners (EIP) | https://www.energyimpactpartners.com/portfolio/ | HTTP GET or Browserless | Utility-backed climate/energy fund. Strong SaaS portfolio in grid software, building efficiency. |
| 19 | G2 Venture Partners | https://www.g2vp.com/portfolio | Browserless | Spun out of Kleiner Perkins. Climate/sustainability, Series A–B. |
| 20 | Burnt Island Ventures | https://www.burntisland.vc/portfolio | HTTP GET | Early-stage climate tech, smaller fund. Good for ground-floor companies. |
| 21 | MCJ Collective | https://www.mcjcollective.com/portfolio | HTTP GET or Browserless | Climate-focused community + fund. Very early stage, strong deal flow visibility. |

#### More Healthcare / Digital Health

| # | VC Firm | Portfolio URL | Likely Scrape Method | Notes |
|---|---------|--------------|---------------------|-------|
| 22 | Andreessen Horowitz Bio + Health | https://a16z.com/portfolio/#bio-health | Browserless | a16z's dedicated bio/health fund. Larger checks but catches companies at seed. JS-heavy site. |
| 23 | Prima Materia | https://www.primamateria.com/portfolio | HTTP GET | Early-stage healthcare tech. Newer fund, smaller portfolio = easy to monitor. |
| 24 | Healthworx (CareFirst) | https://healthworx.com/portfolio/ | HTTP GET | Corporate VC arm focused on healthcare innovation. Seed/Series A. |

#### More Social Justice / Impact

| # | VC Firm | Portfolio URL | Likely Scrape Method | Notes |
|---|---------|--------------|---------------------|-------|
| 25 | Base10 Partners | https://base10.vc/portfolio/ | HTTP GET or Browserless | "Advancement Initiative" donates carry to HBCUs. Broad early-stage, strong social mission. |
| 26 | Kapor Capital | *(already in existing scraper)* | Sitemap XML | Gap-closing tech for underserved communities. Already tracked — listed here for completeness. |
| 27 | Zeal Capital Partners | https://www.zealcp.com/portfolio | HTTP GET | Invests in underrepresented founders, early stage. DC-based. |

---

## Implementation Notes

### Scrape Method Selection
- **HTTP GET**: Try this first. If the portfolio page returns company data in the initial HTML response, no headless browser needed.
- **Sitemap XML**: Check `robots.txt` and `/sitemap.xml` for each domain. Sitemaps with `<lastmod>` dates are ideal for detecting new additions (see Costanoa/Kapor pattern in existing scraper).
- **Browserless**: Fall back to headless browser if portfolio data is loaded via JavaScript (React/Next.js hydration, infinite scroll, etc.).
- **API discovery**: Check browser DevTools Network tab for XHR/fetch calls that return JSON. Some sites use headless CMS APIs (see First Round Capital's Sanity API pattern).

### Recommended Discovery Steps Per Site
1. `curl -s <portfolio_url>` — check if company names appear in raw HTML
2. `curl -s <domain>/sitemap.xml` — check for sitemap with portfolio entries
3. `curl -s <domain>/robots.txt` — check for sitemap references or API paths
4. If HTML is empty/minimal, use Browserless and inspect for API calls in network traffic

### Data to Extract Per Portfolio Company
Match existing schema. At minimum:
- Company name
- Company URL (website)
- One-line description (if available)
- Date added / last modified (if available)
- Sector tags (if available)

### Change Detection
- For sites with dates (`lastmod`, `_createdAt`, etc.): compare against last known date
- For sites without dates: hash the portfolio list and diff against previous snapshot
- Flag new additions for notification

---

## Tags / Categories
When storing results, tag these new entries:
- Firms 1–5, 18–21: `climate-tech`, `green-energy`
- Firms 6–10, 22–24: `healthcare`, `digital-health`
- Firms 11–17, 25–27: `social-justice`, `impact-investing`
- All: `early-stage`, `saas-target`
