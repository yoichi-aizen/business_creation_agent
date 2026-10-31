---
name: crustdata-api
description: >-
  Comprehensive guide and operational runbook for the Crustdata B2B Intelligence API (v2025-11-01).
  Use when building applications that search, identify, and enrich companies, people, jobs, web pages,
  and social posts, or analyzing company technographics, tech stacks, and hiring intelligence.
---

# Crustdata API Master Skill & Hackathon Reference

Welcome to the Crustdata API integration guide. This skill provides an agent-friendly, production-ready reference for building on the Crustdata platform (API Version `2025-11-01`).

---

## 1. Quick Reference & Core Conventions

- **Base URL**: `https://api.crustdata.com`
- **Required Headers** (on every request):
  - `Authorization: Bearer <CRUSTDATA_API_KEY>`
  - `x-api-version: 2025-11-01`
  - `Content-Type: application/json`
- **Credit Tracking Header**: Every response returns `X-Credits-Used` indicating the credit charge for that call.
- **Detailed Sub-References**:
  - [Technographics Guide](file:///Users/anirudhgoel/Downloads/crusdata_hck/.agents/skills/crustdata-api/references/technographics.md): Full breakdown of tech stacks, 12 super-categories, job posting evidence, and competitive targeting.
  - [Filter Grammar & Operators](file:///Users/anirudhgoel/Downloads/crusdata_hck/.agents/skills/crustdata-api/references/filter-operators.md): Syntax rules, AST boolean trees, and inequality traps.
  - [Company API](file:///Users/anirudhgoel/Downloads/crusdata_hck/.agents/skills/crustdata-api/references/company-api.md): Search, Identify, Enrich, and Autocomplete.
  - [Person API](file:///Users/anirudhgoel/Downloads/crusdata_hck/.agents/skills/crustdata-api/references/person-api.md): Search, Identify, Enrich, Contact Data, Semantic Search, and Job Title Normalization (JTN).
  - [Job API](file:///Users/anirudhgoel/Downloads/crusdata_hck/.agents/skills/crustdata-api/references/job-api.md): Postings Search, Aggregations, and Job Technographics.
  - [Web, Watchers & Account APIs](file:///Users/anirudhgoel/Downloads/crusdata_hck/.agents/skills/crustdata-api/references/web-watchers-account.md): Web Fetch, Web Search, Watchers/Webhooks, and Batch processing.

---

## 2. API Endpoints Directory

| API Area | Method | Endpoint Path | Credits Cost | Rate Limit | Primary Use Case |
| :--- | :---: | :--- | :--- | :--- | :--- |
| **Account** | `GET` | `/account/credits` | **Free (0)** | 300 rpm | Check remaining balance & grant refresh |
| **Account** | `GET` | `/account/endpoints` | **Free (0)** | 300 rpm | Verify accessible endpoints & permissions |
| **Company** | `POST` | `/company/identify` | **Free (0)** | 30 rpm | Deduplicate & resolve domain/name to company ID |
| **Company** | `POST` | `/company/search/autocomplete` | **Free (0)** | 45 rpm | Typeahead discovery of valid industries & tech |
| **Company** | `POST` | `/company/search` | 0.03/res + add-ons | 30 rpm | Filter & rank companies by headcount, funding, stack |
| **Company** | `POST` | `/company/enrich` | 2 (base) / +2 (tech) | 15 rpm | Full company profiles, headcount trends, technographics |
| **Person** | `POST` | `/person/identify` | 1/match (0 on miss) | 30 rpm | Resolve email or profile URL to person ID |
| **Person** | `POST` | `/person/search/autocomplete` | **Free (0)** | 30 rpm | Discover valid job titles, skills, universities |
| **Person** | `POST` | `/person/search` | 0.03/res + tiers | 30 rpm | Hybrid semantic search across professionals & titles |
| **Person** | `POST` | `/person/enrich` | 1 (base) | 15 rpm | Full employment history, skills, education |
| **Person** | `POST` | `/person/contact/enrich` | Up to 5.5 (enterprise) | 15 rpm | Verified business email, personal email, phone |
| **Job** | `POST` | `/job/search` | 0.03/res | 30 rpm | Search job listings, tech requirements, aggregations |
| **Job** | `POST` | `/job/search/autocomplete` | **Free (0)** | 30 rpm | Discover exact job titles, technologies, skills |
| **Web** | `POST` | `/web/search/live` | 1/query | 10 rpm | Real-time multi-source web search |
| **Web** | `POST` | `/web/enrich/live` | 1/URL | 10 rpm | Clean HTML extraction for up to 10 URLs |
| **Watch** | `POST` | `/watch/company` or `/person` | Plan-specific | 30 rpm | Set event-driven alerts for entity changes |

---

## 3. High-Priority Filter Traps & Rules

Crustdata search engines enforce strict syntax rules:

> [!WARNING]
> 1. **Inequality Operators**: Standard `>=` and `<=` DO NOT EXIST.
>    - Use `=>` for Greater Than or Equal To.
>    - Use `=<` for Less Than or Equal To.
> 2. **Null Checks**: Must explicitly include `"value": null`.
>    - `{ "field": "...", "type": "is_null", "value": null }`
>    - `{ "field": "...", "type": "is_not_null", "value": null }`
> 3. **Single vs Multiple Identifiers in Enrich/Identify**:
>    - Supply **exactly one** identifier type per request: e.g. `"domains": ["..."]` OR `"names": ["..."]`. Combining keys returns `400 Bad Request`.
> 4. **Text Matching Operators**:
>    - `(.)`: Fuzzy all-words match (typo-tolerant, order-independent).
>    - `[.]`: Exact contiguous phrase match.
>    - `(!)`: Fuzzy negation.

---

## 4. Technographics Cheat-Sheet

Technographics unlocks company tech stacks and posting-level skill demands:

```
Company Level:                                 Job Posting Level:
POST /company/enrich                          POST /job/search
-> "fields": ["technographics"]               -> "technographics.technologies.name": "React"
-> Returns company_data.technographics        -> Matches postings explicitly demanding tool
(Web signals + company-wide jobs)             (Posting-scoped, professional network)
```

### The 12 Canonical Super-Categories:
1. `cloud-infrastructure` (AWS, GCP, Azure, Kubernetes, Terraform)
2. `collaboration-productivity` (Slack, Notion, Asana, Google Workspace)
3. `customer-success-support` (Zendesk, Intercom, Freshdesk, Gainsight)
4. `data-analytics` (Snowflake, BigQuery, Databricks, Looker, dbt)
5. `data-ml-platform` (PyTorch, TensorFlow, OpenAI, Hugging Face, LangChain)
6. `ecommerce-payments` (Stripe, Shopify, Adyen, Plaid, Chargebee)
7. `engineering-devops` (GitHub, GitLab, Datadog, Sentry, New Relic)
8. `finance-operations` (NetSuite, QuickBooks, Brex, Ramp, Carta)
9. `hr-workforce` (Workday, Greenhouse, Lever, Rippling, Gusto)
10. `languages-frameworks` (Python, TypeScript, React, Next.js, Go, Rust)
11. `sales-marketing` (Salesforce, HubSpot, Apollo, Marketo, Outreach)
12. `security` (Okta, CrowdStrike, Wiz, Palo Alto, 1Password, Snyk)

### Typical Technographics Workflow:
1. **Search & Target**: Use `POST /company/search` with `technographics.technologies.name` in `filters` to isolate target accounts.
2. **Enrich & Inspect**: Use `POST /company/enrich` with `"fields": ["technographics"]` on matching accounts to read their complete stack and job posting evidence.

---

## 5. Rapid Hackathon Starter Patterns

### Pattern A: "Search to Narrow, Enrich to Read"
```
POST /company/search (filters: country = USA, funding = series_a, tech = Salesforce)
    │
    ▼ returns 20 company matches (crustdata_company_id, name, domain)
POST /company/enrich (domains: [...], fields: ["basic_info", "headcount", "people", "technographics"])
    │
    ▼ returns full profiles with founders, CXOs, employee growth, and complete tech stack
```

### Pattern B: Executive Hunter / Persona Prospector
```
POST /person/search (query: "VP of Engineering or Head of AI", filters: company in ["Stripe", "Databricks"])
    │
    ▼ returns profiles with basic_profile.normalized_title and experience
POST /person/contact/enrich (enterprise) or POST /person/enrich
    │
    ▼ returns verified business email, personal email, phone, or deep LinkedIn history
```

### Pattern C: Real-Time Competitive Displacement Radar
1. Query `POST /company/search` for companies using Competitor Tool (e.g. `technographics.technologies.name = "LegacyVendor"`).
2. Query `POST /job/search` for open roles at those companies mentioning migration or complementary technologies.
3. Query `POST /person/search` for the Head of Infrastructure or Engineering Manager at those companies.
4. Synthesize tailored outreach citing their current stack and hiring initiatives.

---

## 6. Ready-to-Use Python SDK (`crustdata_client.py`)

A battle-tested client is available in [crustdata_client.py](file:///Users/anirudhgoel/Downloads/crusdata_hck/crustdata_client.py):
- Automatically attaches `x-api-version: 2025-11-01` and auth tokens.
- Tracks credits consumed via `X-Credits-Used`.
- Implements helper methods for `search_companies()`, `enrich_company()`, `identify_company()`, `search_people()`, `enrich_person()`, `search_jobs()`, `get_credits()`.
- Validates inequality operators (`=<` and `=>`) to prevent 400 Bad Request errors.
