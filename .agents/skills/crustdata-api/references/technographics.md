# Crustdata Technographics Guide & Reference

> **Beta Feature**: Technographics detects the tools, platforms, and technologies a company uses, as well as the technologies explicitly named in individual job postings.

---

## 1. Architectural Mental Model

Technographics operates on **two distinct levels**:

1. **Company Level (`POST /company/enrich` & `POST /company/search`)**:
   - Answers: *"What is this entire organization built on / what software does it use?"*
   - Signals gathered from:
     - Company web presence (`"web signals"`, e.g. frontend SDKs, DNS records, headers, scripts)
     - Job postings aggregated across the company (`"job posting"`, e.g. hiring for Snowflake, Kubernetes, Salesforce)
   - Read endpoint: `POST /company/enrich` with `"fields": ["technographics"]`
   - Filter endpoint: `POST /company/search` with `technographics.*` filter columns (filter-only, cannot be returned in search results).

2. **Job Posting Level (`POST /job/search`)**:
   - Answers: *"What technologies does this specific role require or mention?"*
   - Posting-scoped: Matches only if that specific job posting explicitly names the tool.
   - Sourced from: Professional network postings (`job_details.source = "professional_network"`).
   - Filter endpoint: `POST /job/search` with `technographics.technologies.*` filter columns (filter-only, cannot be returned in job search results).

---

## 2. The 12 Super-Categories

Every detected technology belongs to a kebab-case `category` slug, which maps to one of the **12 canonical `super_category` slugs**:

| Super-Category Slug | Typical Technologies Included |
| :--- | :--- |
| `cloud-infrastructure` | AWS, Google Cloud, Azure, Cloudflare, Terraform, Docker, Kubernetes |
| `collaboration-productivity` | Slack, Notion, Asana, Google Workspace, Microsoft 365, Jira, Linear |
| `customer-success-support` | Zendesk, Intercom, Freshdesk, Gainsight, HubSpot Service Hub |
| `data-analytics` | Snowflake, BigQuery, Databricks, Looker, Tableau, dbt, Mixpanel, Segment |
| `data-ml-platform` | PyTorch, TensorFlow, LangChain, OpenAI, Hugging Face, Weights & Biases |
| `ecommerce-payments` | Stripe, Shopify, Adyen, PayPal, Chargebee, Plaid |
| `engineering-devops` | GitHub, GitLab, Jenkins, Datadog, New Relic, Sentry, ArgoCD |
| `finance-operations` | NetSuite, QuickBooks, Brex, Ramp, Carta, Workday Financial |
| `hr-workforce` | Workday, Greenhouse, Lever, Rippling, Gusto, BambooHR |
| `languages-frameworks` | Python, TypeScript, React, Next.js, Node.js, Go, Rust, Java, Kotlin |
| `sales-marketing` | Salesforce, HubSpot, Marketo, Apollo, Outreach, ZoomInfo, Mailchimp |
| `security` | Okta, CrowdStrike, Palo Alto Networks, Wiz, 1Password, Snyk, Cloudflare Access |

> [!TIP]
> Use the `technology` and `technology_category` fields on `POST /company/search/autocomplete` and `POST /job/search/autocomplete` to discover exact canonical names (e.g. `"React"`, `"React Native"`) and category slugs. `super_category` has no autocomplete endpoint; use the 12 slugs above.

---

## 3. Reading a Company's Full Tech Stack (`POST /company/enrich`)

To read the tech stack for known companies, supply the domain, company name, Crustdata ID, or LinkedIn profile URL to `/company/enrich`, and explicitly pass `"fields": ["technographics"]`.

### Request
```bash
curl --request POST \
  --url https://api.crustdata.com/company/enrich \
  --header 'authorization: Bearer YOUR_API_KEY' \
  --header 'content-type: application/json' \
  --header 'x-api-version: 2025-11-01' \
  --data '{
    "domains": ["openai.com"],
    "fields": ["basic_info", "technographics"]
  }'
```

### Response Schema (`company_data.technographics`)
```json
{
  "total_technologies": 42,
  "top_technologies": ["Kubernetes", "PyTorch", "Python", "Cloudflare", "Slack"],
  "updated_at": "2025-10-15T08:30:00Z",
  "technologies": [
    {
      "name": "Kubernetes",
      "category": "containers-orchestration",
      "super_category": "cloud-infrastructure",
      "description": "Open-source system for automating deployment, scaling, and management of containerized applications.",
      "sources": ["web signals", "job posting"],
      "job_posting_evidence": [
        {
          "job_title": "Systems Software Engineer, Infrastructure",
          "job_url": "https://...",
          "posted_at": "2025-09-01"
        }
      ]
    },
    {
      "name": "Snowflake",
      "category": "data-warehouses",
      "super_category": "data-analytics",
      "description": "Cloud-based data-warehousing company.",
      "sources": ["job posting"],
      "job_posting_evidence": [...]
    }
  ]
}
```

---

## 4. Filtering Companies by Tech Stack (`POST /company/search`)

You can target companies by their stack on `POST /company/search`. 

> [!WARNING]
> **Filter-Only Field**: In `/company/search`, `technographics.*` can ONLY be used in `filters` and `sorts`. Do **NOT** pass `technographics` in the `fields` array on `/company/search`, or the API returns a `400` error. To read the stack, take the matching company IDs/domains and call `POST /company/enrich`.

### Available Filter Paths on Company Search:

| Path | Filter Type | Valid Operators | Example Value | Description |
| :--- | :--- | :--- | :--- | :--- |
| `technographics.technologies.name` | array of strings | `=`, `in`, `not_in` | `"Snowflake"` or `["Snowflake", "Databricks"]` | Match companies running this tool |
| `technographics.technologies.category` | array of strings | `=`, `in`, `not_in` | `"data-warehouses"` | Match companies running any tool in category |
| `technographics.technologies.super_category` | array of strings | `=`, `in`, `not_in` | `"data-analytics"` | Match companies running any tool in super-category |
| `technographics.total_technologies` | integer | `=`, `!=`, `<`, `=<`, `>`, `=>` | `20` | Filter by tech maturity / stack size |
| `technographics.top_technologies` | array of strings | `=`, `in`, `not_in` | `"AWS"` | Match companies where tool is in top technologies |

### Example: Finding Companies Using Competitor Tech (Competitive Displacement)
Target US companies with 50-500 employees that run Salesforce but NOT HubSpot:

```json
{
  "filters": {
    "op": "and",
    "conditions": [
      { "field": "locations.country", "type": "=", "value": "USA" },
      { "field": "headcount.headcount", "type": "=>", "value": 50 },
      { "field": "headcount.headcount", "type": "=<", "value": 500 },
      { "field": "technographics.technologies.name", "type": "=", "value": "Salesforce" },
      { "field": "technographics.technologies.name", "type": "not_in", "value": ["HubSpot"] }
    ]
  },
  "limit": 25,
  "fields": ["basic_info", "headcount", "funding"]
}
```

---

## 5. Filtering Job Postings by Technology (`POST /job/search`)

Use this when you want to find open roles requiring specific tech skills or tools.

### Available Filter Paths on Job Search:

| Path | Filter Type | Valid Operators | Description |
| :--- | :--- | :--- | :--- |
| `technographics.technologies.name` | array of strings | `=`, `in`, `not_in`, `is_not_null` | Technology named in the posting |
| `technographics.technologies.category` | array of strings | `=`, `in`, `not_in` | Category of technology named in posting |
| `technographics.technologies.super_category` | array of strings | `=`, `in`, `not_in` | Super-category of tech named in posting |

> [!IMPORTANT]
> **Posting-scoped, not employer-scoped**: A job matches only if that specific job posting explicitly names the tool. It does NOT inherit the employer's company-level stack.
> To ensure postings have undergone technographics detection, filter for `job_details.source = "professional_network"` or check `"field": "technographics.technologies.name", "type": "is_not_null", "value": null`.

### Example: Finding Open Machine Learning Roles Mentioning PyTorch and AWS
```json
{
  "filters": {
    "op": "and",
    "conditions": [
      { "field": "job_details.title", "type": "(.)", "value": "Machine Learning Engineer" },
      { "field": "technographics.technologies.name", "type": "=", "value": "PyTorch" },
      { "field": "technographics.technologies.name", "type": "=", "value": "Amazon Web Services" }
    ]
  },
  "limit": 10,
  "fields": ["crustdata_job_id", "job_details.title", "job_details.location", "company.basic_info.name"]
}
```

---

## 6. Autocomplete for Technologies

Never guess the exact name or category slug:

```bash
curl --request POST \
  --url https://api.crustdata.com/company/search/autocomplete \
  --header 'authorization: Bearer YOUR_API_KEY' \
  --header 'content-type: application/json' \
  --header 'x-api-version: 2025-11-01' \
  --data '{
    "field": "technology",
    "query": "kube"
  }'
```
Response:
```json
[
  { "value": "Kubernetes", "count": 14200 },
  { "value": "Kubeflow", "count": 1850 }
]
```

Fields supported on Autocomplete:
- `"technology"`: Tool names (e.g. `"React"`, `"Kubernetes"`, `"Databricks"`)
- `"technology_category"`: Category slugs (e.g. `"data-warehouses"`, `"frontend-frameworks"`)

---

## 7. Pricing & Quota Considerations

- **Enrichment Cost**: Base company enrich is **2 credits**. Requesting `"technographics"` adds **+2 credits** (total 4 credits per enriched company that returns technographics). If no technographics are found, only the base fee is billed.
- **Search Filtering**: Filtering on `technographics.*` in `/company/search` costs base search (0.03 credits/result) + 1 credit per result for the technographics filter group.
- **Job Search Filtering**: Standard Job Search pricing (0.03 credits/result) with **no add-on fee** for filtering by technographics.

