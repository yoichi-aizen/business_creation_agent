# Crustdata Person API Reference

Base URL: `https://api.crustdata.com`
Headers:
- `Authorization: Bearer <API_KEY>`
- `x-api-version: 2025-11-01`
- `Content-Type: application/json`

---

## 1. Endpoints Overview

| Method | Path | Cost (Credits) | Rate Limit | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/person/identify` | 1/match (0 if no match) | 30 req/min | Resolve profile URLs, emails, or Google Scholar URLs to person ID and basic profile |
| `POST` | `/person/enrich` | 1 base (up to 4 with dev profile) | 15 req/min | Enrich person profile (work history, skills, education, patents, publications) |
| `POST` | `/person/contact/enrich` | Up to 5.5/match (enterprise) | 15 req/min | Retrieve verified business emails, personal emails, and phone numbers |
| `POST` | `/person/search` | 0.03/res + field tiers | 30 req/min | Search millions of professionals with filters, hybrid semantic search, and JTN |
| `POST` | `/person/search/autocomplete` | **Free (0)** | 30 req/min | Retrieve valid filter values (titles, companies, universities, skills) |
| `POST` | `/person/professional_network/enrich/live` | Plan-specific | 10 req/min | Real-time live profile scrape |

---

## 2. Person Identify (`POST /person/identify`)

Quickly resolve emails or profile URLs to the person behind them.
- Batch limit: up to 25 identifiers per call.
- Cost: 1 credit per successfully resolved identifier; 0 for misses.

### Request Body
Must provide **exactly one** identifier list:
```json
{
  "emails": ["alex@example.com", "sarah@techcorp.io"]
}
```
*Or:*
- `"professional_network_profile_urls": ["https://linkedin.com/in/alex-smith"]`
- `"research_profile_urls": ["https://scholar.google.com/citations?user=..."]`

---

## 3. Person Enrich (`POST /person/enrich`)

Enrich up to 25 person profiles from the cached dataset.

### Request Body
```json
{
  "professional_network_profile_urls": [
    "https://linkedin.com/in/satyanadella"
  ],
  "fields": [
    "basic_profile",
    "experience",
    "education",
    "skills",
    "languages"
  ]
}
```

### Available Field Groups:
- `basic_profile`: Full name, headline, summary, normalized title, location, photo.
- `experience`: Work history (company names, titles, start/end dates, descriptions).
- `education`: Degrees, fields of study, institutions, dates.
- `skills`: Endorsed and detected technical/business skills.
- `certifications`: Professional licenses and certifications.
- `honors`: Awards and achievements.
- `languages`: Spoken languages and proficiencies.

---

## 4. Contact Enrichment (`POST /person/contact/enrich`)

Fetch direct contact details (business emails, personal emails, phone numbers).

> [!NOTE]
> Gated to enterprise plans. Returns `403` on self-serve starter plans.

### Request Body
```json
{
  "professional_network_profile_urls": [
    "https://linkedin.com/in/example-executive"
  ],
  "fields": [
    "contact.business_emails",
    "contact.personal_emails",
    "contact.phone_numbers"
  ],
  "verified": true
}
```
- `verified: true`: Runs real-time SMTP deliverability check on business emails (+0.5 credits). Guarantees only deliverable / catch-all emails are returned.

---

## 5. Person Search (`POST /person/search`)

Search professionals using structured filters, semantic queries, or both.

### Request Schema:
```json
{
  "search": {
    "query": "Senior distributed systems engineers with Rust and Raft experience in San Francisco",
    "mode": "hybrid"
  },
  "filters": {
    "op": "and",
    "conditions": [
      { "field": "experience.employment_details.current.company_name", "type": "in", "value": ["OpenAI", "Anthropic", "Stripe"] },
      { "field": "basic_profile.normalized_title.department", "type": "=", "value": "Engineering" },
      { "field": "basic_profile.normalized_title.category", "type": "=", "value": "Software Engineering" },
      { "field": "skills.name", "type": "in", "value": ["Rust", "Distributed Systems"] },
      { "field": "professional_network.location.country", "type": "=", "value": "United States" }
    ]
  },
  "limit": 20,
  "cursor": null,
  "fields": [
    "basic_profile",
    "experience"
  ]
}
```

### Search Modes (`search.mode`):
- `hybrid`: Combines semantic vectors and lexical text match.
- `lexical`: Exact keyword matching.
- `semantic`: Pure semantic embeddings.

---

## 6. Job Title Normalization (JTN)

Every person profile returned includes structured job title taxonomy: `basic_profile.normalized_title`.

### Normalized Title Object:
```json
{
  "basic_profile": {
    "name": "Jane Doe",
    "headline": "MTS at TechCo | ex-Googler",
    "normalized_title": {
      "department": "Engineering",
      "category": "Software Engineering",
      "matched_title": "Software Engineer",
      "confidence_score": 0.94
    }
  }
}
```

### Why use JTN in Search:
Instead of trying to enumerate all permutations ("MTS", "SDE 2", "Senior Software Developer", "Programmer"), filter directly on:
- `basic_profile.normalized_title.department`: `"Engineering"`, `"Sales"`, `"Marketing"`, `"Product"`, `"Operations"`, etc.
- `basic_profile.normalized_title.category`: `"Software Engineering"`, `"DevOps & Cloud"`, `"Data Science"`, `"Account Management"`, etc.
- `basic_profile.normalized_title.matched_title`: `"Software Engineer"`, `"Engineering Manager"`, etc.

