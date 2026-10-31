# Crustdata Job Postings API Reference

Base URL: `https://api.crustdata.com`
Headers:
- `Authorization: Bearer <API_KEY>`
- `x-api-version: 2025-11-01`
- `Content-Type: application/json`

---

## 1. Endpoints Overview

| Method | Path | Cost (Credits) | Rate Limit | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/job/search` | 0.03/result | 30 req/min | Search millions of indexed job listings with filters, aggregations, and technographics |
| `POST` | `/job/search/autocomplete` | **Free (0)** | 30 req/min | Autocomplete job titles, categories, technologies, and locations |
| `POST` | `/job/professional_network/search/live` | Plan-specific | 10 req/min | Fetch real-time active openings directly for a company |

---

## 2. Job Search (`POST /job/search`)

Searches the indexed job database. Allows finding open roles by title, seniority, salary, location, hiring company, and required tech stack.

### Request Body
```json
{
  "filters": {
    "op": "and",
    "conditions": [
      { "field": "job_details.title", "type": "(.)", "value": "Founding Engineer" },
      { "field": "technographics.technologies.name", "type": "in", "value": ["Next.js", "TypeScript"] },
      { "field": "locations.country", "type": "=", "value": "USA" },
      { "field": "metadata.date_added", "type": "=>", "value": "2025-01-01" }
    ]
  },
  "limit": 25,
  "cursor": null,
  "sorts": [
    { "field": "metadata.date_added", "order": "desc" }
  ],
  "fields": [
    "crustdata_job_id",
    "job_details.title",
    "job_details.location",
    "job_details.url",
    "company.basic_info.name",
    "company.basic_info.primary_domain",
    "metadata.date_added"
  ]
}
```

> [!NOTE]
> `metadata.date_added` is the **job-posted date** (when the listing went live on the source job portal), NOT the Crustdata crawl time.

---

## 3. ID Semantics in Job Search
Keep these three identifiers straight:
1. `crustdata_job_id`: Unique identifier for the job listing. Use this for deduplication.
2. `company.basic_info.crustdata_company_id`: Crustdata company identifier returned on the job row.
3. `company.basic_info.company_id`: Filter alias used in `filters` and `aggregations.column` to filter by employer.

---

## 4. Aggregations (Hiring Analytics & Trends)

You can compute counts and group distributions across the job dataset:

### Count by Company (Top Hiring Companies):
```json
{
  "filters": {
    "field": "job_details.title",
    "type": "(.)",
    "value": "AI Engineer"
  },
  "aggregations": {
    "type": "group_by",
    "column": "company.basic_info.company_id",
    "limit": 10
  }
}
```
Response:
```json
{
  "aggregations": [
    {
      "key": 629097,
      "count": 48,
      "metadata": {
        "company_name": "OpenAI",
        "company_website_domain": "openai.com"
      }
    }
  ]
}
```

---

## 5. Posting-Level Technographics

Filter job postings by technologies named directly in the job description:
- `technographics.technologies.name`: (e.g. `["Kubernetes", "Go"]`)
- `technographics.technologies.category`: (e.g. `["cloud-platforms-iaas"]`)
- `technographics.technologies.super_category`: (one of the 12 super-categories, e.g. `"engineering-devops"`)

> [!WARNING]
> Technographics on jobs are filter-only and never returned in `fields`. They only match postings where the technology was explicitly detected in the job posting text.

