# Crustdata Web, Watcher, Batch & Account APIs Reference

Base URL: `https://api.crustdata.com`
Headers:
- `Authorization: Bearer <API_KEY>`
- `x-api-version: 2025-11-01`

---

## 1. Web Search & Web Fetch APIs

### Web Search (`POST /web/search/live`)
Search the live web across news, academic papers, web articles, social media, and deep research summaries.
- Cost: 1 credit per query
- Rate limit: 10 req/min

```json
{
  "query": "Recent Series B AI agent startups funded in 2025",
  "sources": ["web", "news"],
  "limit": 10
}
```

### Web Fetch (`POST /web/enrich/live`)
Extract full HTML and page title for up to 10 URLs in one synchronous call.
- Cost: 1 credit per URL
- Rate limit: 10 req/min

```json
{
  "urls": [
    "https://example.com/about",
    "https://example.com/pricing"
  ]
}
```

---

## 2. Watcher APIs (Event-Driven Webhooks & Feeds)

Crustdata Watchers allow you to turn searches or entity lists into automated notification feeds.

### Two Watcher Paradigms:
1. **Entity Watcher (`POST /watch/company` or `POST /watch/person`)**:
   - Monitor a known list of companies or people you supply.
   - Triggers when an entity profile changes: funding round, headcount jump, title change, new certification, rebrand.
   - Delivers the exact JSON diff.
2. **Discovery Watcher (`POST /watch/company/search` or `POST /watch/person/search` or `POST /watch/social_post/search`)**:
   - Evaluates a saved search filter periodically (e.g. `every_hours: 24`).
   - Delivers newly matching entities that crossed into the filter.

### Delivery Channels:
- Webhooks (`POST` payload to your HTTPS endpoint)
- Slack webhooks
- Google Chat webhooks
- Email notifications
- Pull-only (`[]` notifications array; poll `/watch/{watch_id}/runs` via API)

---

## 3. Batch APIs (Asynchronous High-Throughput Jobs)

For bulk enrichment or queries larger than 25 records at a time, use the Batch API:

| Endpoint | Max Batch Size | Delivery Format |
| :--- | :--- | :--- |
| `POST /batch/company/enrich` | 10,000 companies | Pre-signed download link (CSV / JSONL) |
| `POST /batch/company/search` | Up to 10,000 results | Pre-signed download link |
| `POST /batch/person/enrich` | Up to 10,000 profiles | Pre-signed download link |
| `POST /batch/person/contact/enrich` | Up to 10,000 profiles | Pre-signed download link |
| `POST /batch/job/search` | Up to 10 companies | Pre-signed download link |

### Workflow:
1. Submit batch job: `POST /batch/<type>` $\rightarrow$ returns `{"batch_id": "..."}`.
2. Check status: `GET /batch/{batch_id}` $\rightarrow$ returns status (`"pending"`, `"processing"`, `"completed"`, `"failed"`).
3. Download results: When completed, extract `download_url`.

---

## 4. Account & Credit Management APIs

### Check Credit Balance (`GET /account/credits`)
Free endpoint. Returns remaining credits and next grant renewal.
```bash
curl --request GET \
  --url https://api.crustdata.com/account/credits \
  --header 'authorization: Bearer YOUR_API_KEY' \
  --header 'x-api-version: 2025-11-01'
```
Response:
```json
{
  "credit_balance": 2450.5,
  "recurring_credit_grant": {
    "grant_size": 5000,
    "frequency": "monthly",
    "next_refresh_date": "2025-12-01T00:00:00Z"
  }
}
```

### List Endpoint Permissions & Rates (`GET /account/endpoints`)
Free endpoint. Lists every endpoint, enabled response fields, effective rate limits, and custom credit costs for your API key.
```bash
curl --request GET \
  --url https://api.crustdata.com/account/endpoints \
  --header 'authorization: Bearer YOUR_API_KEY' \
  --header 'x-api-version: 2025-11-01'
```

### Usage Tracking (`GET /account/usage/summary`)
Inspect how credits were spent across your endpoints and dates.
```bash
curl --request GET \
  --url 'https://api.crustdata.com/account/usage/summary?group_by=endpoint' \
  --header 'authorization: Bearer YOUR_API_KEY' \
  --header 'x-api-version: 2025-11-01'
```

