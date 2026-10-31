# Crustdata Company API Reference

Base URL: `https://api.crustdata.com`
Headers:
- `Authorization: Bearer <API_KEY>`
- `x-api-version: 2025-11-01`
- `Content-Type: application/json`

---

## 1. Endpoints Overview

| Method | Path | Cost (Credits) | Rate Limit | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/company/identify` | **Free (0)** | 30 req/min | Resolve ambiguous domain/name/URL to Crustdata ID and basic info |
| `POST` | `/company/enrich` | 2 (base) / +2 (technographics) | 15 req/min | Deep profile enrichment (headcount, funding, CXOs, technographics, news) |
| `POST` | `/company/search` | 0.03/res + premium groups | 30 req/min | Filter and rank indexed companies with boolean logic & hybrid search |
| `POST` | `/company/search/autocomplete` | **Free (0)** | 45 req/min | Retrieve valid filter values with doc frequencies |
| `POST` | `/company/professional_network/search/live`| Plan-specific | 10 req/min | Real-time web-scraped company search |

---

## 2. Company Identify (`POST /company/identify`)

Use this for entity resolution, deduplication, and pre-enrichment.

> [!TIP]
> **Free Endpoint**: Does not consume credits. Use this before expensive enrichment calls to confirm that Crustdata has the entity.

### Request Body
Must provide **exactly one** identifier type (array of strings, max 25 per request):
```json
{
  "domains": ["openai.com", "stripe.com"],
  "exact_match": true
}
```
*Alternative identifier keys:*
- `"names": ["OpenAI", "Stripe"]`
- `"professional_network_profile_urls": ["https://linkedin.com/company/openai"]`
- `"crustdata_company_ids": [629097]`

### Response Body
```json
[
  {
    "matched_on": "openai.com",
    "match_type": "domain",
    "matches": [
      {
        "confidence_score": 0.99,
        "company_data": {
          "crustdata_company_id": 629097,
          "basic_info": {
            "name": "OpenAI",
            "primary_domain": "openai.com",
            "description": "OpenAI is an AI research and deployment company.",
            "profile_url": "https://linkedin.com/company/openai",
            "industries": ["Artificial Intelligence", "Technology"]
          }
        }
      }
    ]
  }
]
```

---

## 3. Company Enrich (`POST /company/enrich`)

Fetches detailed company profiles. Supports multi-identifier batching (up to 25 per request).

### Request Parameters
- Exactly one identifier array: `domains`, `names`, `professional_network_profile_urls`, or `crustdata_company_ids` (max 25).
- `fields`: Array of field groups to retrieve. If omitted, returns only `basic_info` and `crustdata_company_id`.
- `exact_match`: Boolean (optional).

### Available `fields` Groups:
- `basic_info`: Name, domain, description, logo, founding year, type, social links.
- `headcount`: Headcount trends, department breakdown, growth rates.
- `funding`: Total raised, last round type, round date, investor lists, valuation.
- `people`: Key executives, CXOs, founders, decision-makers.
- `hiring`: Active job opening counts, department hiring velocity.
- `technographics`: Complete software and tooling tech stack (add-on, +2 credits).
- `web_traffic`: Traffic volume, monthly visits, bounce rate, traffic rank.
- `employee_reviews`: Glassdoor / employee sentiment metrics and ratings.
- `news`: Recent press articles and company updates.
- `taxonomy`: Categories, sub-industries, tags.

### Example Request
```json
{
  "domains": ["retool.com"],
  "fields": [
    "basic_info",
    "headcount",
    "funding",
    "technographics",
    "people"
  ]
}
```

---

## 4. Company Search (`POST /company/search`)

Search the indexed company dataset. Supports **hybrid ranked search** (natural language) and **structured filter trees**.

### Request Body Structure
```json
{
  "search": {
    "query": "cloud data warehouse and ETL platforms",
    "mode": "hybrid"
  },
  "filters": {
    "op": "and",
    "conditions": [
      { "field": "locations.country", "type": "=", "value": "USA" },
      { "field": "funding.last_round_type", "type": "in", "value": ["series_a", "series_b"] },
      { "field": "headcount.headcount", "type": "=>", "value": 20 },
      { "field": "technographics.technologies.name", "type": "=", "value": "Snowflake" }
    ]
  },
  "limit": 20,
  "cursor": null,
  "fields": ["basic_info", "funding", "headcount"]
}
```

### Search Modes (`search.mode`):
- `hybrid` (Default): Combines semantic retrieval with keyword matching. Best for general discovery.
- `lexical`: Exact keyword matching.
- `semantic`: Pure conceptual similarity.

### Pagination
- Max `limit`: 100 per page.
- Returns `next_cursor` in response: pass as `"cursor": "<next_cursor>"` in subsequent requests.
- Cursors expire after 20 minutes. Up to 1,000 candidate positions reachable per search.

### Searchable & Filterable Fields:
- `basic_info.name`, `basic_info.primary_domain`, `basic_info.industries`
- `locations.country`, `locations.city`, `locations.headquarters` (geo operators supported)
- `headcount.headcount`, `headcount.growth_rates.*`
- `funding.total_funding_usd`, `funding.last_round_type`, `funding.last_round_date`
- `technographics.technologies.name`, `technographics.technologies.category`, `technographics.technologies.super_category`, `technographics.total_technologies`

---

## 5. Company Autocomplete (`POST /company/search/autocomplete`)

Discover valid values before running search queries.

```json
{
  "field": "basic_info.industries",
  "query": "Soft"
}
```
Returns:
```json
[
  { "value": "Software Development", "count": 284000 },
  { "value": "Software Infrastructure", "count": 52100 }
]
```
Common autocomplete fields:
- `basic_info.industries`
- `locations.country`, `locations.city`
- `taxonomy.categories`
- `technology`, `technology_category`

