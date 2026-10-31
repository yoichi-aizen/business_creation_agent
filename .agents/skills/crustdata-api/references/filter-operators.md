# Crustdata Filter Grammar & Operators Reference

Crustdata search APIs (`/company/search`, `/person/search`, `/job/search`, `/social_post/search`, and watcher endpoints) use a unified JSON filter tree specification.

---

## 1. Filter Structure (The AST)

A filter payload is either:
1. A **single leaf condition**: An object with `field`, `type`, and `value`.
2. A **compound condition node**: An object with `op` (`"and"` or `"or"`) and a `conditions` array containing nested conditions or groups.

### Single Condition Example:
```json
{
  "field": "basic_info.name",
  "type": "=",
  "value": "Crustdata"
}
```

### Compound Condition Tree Example:
```json
{
  "op": "and",
  "conditions": [
    { "field": "locations.country", "type": "=", "value": "USA" },
    {
      "op": "or",
      "conditions": [
        { "field": "funding.last_round_type", "type": "=", "value": "seed" },
        { "field": "funding.last_round_type", "type": "=", "value": "series_a" }
      ]
    },
    { "field": "headcount.headcount", "type": "=>", "value": 10 }
  ]
}
```

---

## 2. Complete Operator Reference Table

| Operator (`type`) | Value Shape | Meaning | Example Value | Critical Notes |
| :--- | :--- | :--- | :--- | :--- |
| `=` | scalar | Exact match | `"retool.com"` | Case-insensitive for text fields. |
| `!=` | scalar | Not equal | `"acquired"` | Excludes exact value. |
| `<` | scalar | Strictly less than | `1000` | Numbers and ISO date strings (`"YYYY-MM-DD"`). |
| `=<` | scalar | Less than or equal to | `50` | ⚠️ **Use `=<`, NOT `<=`!** (`<=` returns `400`). |
| `>` | scalar | Strictly greater than | `2021` | Numbers and ISO date strings. |
| `=>` | scalar | Greater than or equal to | `"2024-01-01"` | ⚠️ **Use `=>`, NOT `>=`!** (`>=` returns `400`). |
| `in` | array | Included in list | `["USA", "CAN", "GBR"]` | Case-insensitive if list $\le 100$ items. Case-sensitive if $> 100$ items. Matches if ANY element in field matches ANY element in list. |
| `not_in` | array | Not in list | `["Intern", "Contractor"]` | Same case rules as `in`. |
| `is_null` | `null` | Field has no value | `null` | ⚠️ **The `"value": null` key is strictly required.** |
| `is_not_null`| `null` | Field has a non-null value | `null` | ⚠️ **The `"value": null` key is strictly required.** |
| `(.)` | string | Fuzzy all-words match | `"Senior Software Engineer"` | Every word in query must appear in the target string in any order; typo-tolerant. |
| `[.]` | string | Exact phrase match | `"Software Development"` | Words must be contiguous and in exact order without typos. Case-insensitive. |
| `(!)` | string | Fuzzy negation | `"Intern"` | Excludes records matching the words/substrings. |
| `has_all` | array | Array contains all elements | `[629097, 632500]` | Matches when nested elements satisfy all conditions. Supported on specific array fields. |
| `geo_distance` | object | Within radius of location | `{"location": "San Francisco, CA", "distance": 50, "unit": "km"}` | Works on headquarters/locations. Units: `km`, `mi`, `miles`, `m`, `meters`, `ft`, `feet`. |
| `geo_exclude` | object | Outside radius of location | `{"location": "London, UK", "distance": 100, "unit": "km"}` | Inverse of `geo_distance`. |
| `geo_polygon` | object | Inside polygon coordinate boundary | `{"points": [[37.8, -122.5], [37.8, -122.3], [37.6, -122.4]]}` | Strict coordinate polygon bounding. |

---

## 3. High-Priority Pitfalls & Gotchas

### 🚨 Pitfall 1: Inequality Comparison Syntax
- ❌ `"type": "<="` or `"type": ">="` will fail with HTTP 400.
- ✅ Always use `"type": "=<"` and `"type": "=>"`.

### 🚨 Pitfall 2: Null Checks
- ❌ Do not send `{ "field": "email", "type": "is_null" }`.
- ✅ You must supply `"value": null`:
  ```json
  { "field": "email", "type": "is_null", "value": null }
  ```

### 🚨 Pitfall 3: Multi-value List Fields (e.g. Industries)
- To require that a company has BOTH `"Artificial Intelligence"` AND `"Healthcare"`, do not use `has_all` (which is unsupported on industries).
- Put two separate `=` conditions in an `"and"` block:
  ```json
  {
    "op": "and",
    "conditions": [
      { "field": "basic_info.industries", "type": "=", "value": "Artificial Intelligence" },
      { "field": "basic_info.industries", "type": "=", "value": "Healthcare" }
    ]
  }
  ```

### 🚨 Pitfall 4: Text Matching Modes (`(.)` vs `[.]`)
- Use `(.)` when order does not matter or you want typo-tolerance:
  - `(.) "Machine Learning"` matches `"Senior Machine Learning Engineer"` AND `"Learning Machine Systems"`.
- Use `[.]` when exact sequence matters:
  - `[.] "Data Scientist"` matches `"Lead Data Scientist"` but rejects `"Scientist of Data"`.

---

## 4. Geographic Filtering Cheat-Sheet

Geo filters apply to `locations.headquarters` (Company) and `location` (Job / Person).

### Radius Search via Place Name:
```json
{
  "field": "locations.headquarters",
  "type": "geo_distance",
  "value": {
    "location": "Austin, TX",
    "distance": 30,
    "unit": "mi"
  }
}
```

### Radius Search via Exact Coordinates:
```json
{
  "field": "locations.headquarters",
  "type": "geo_distance",
  "value": {
    "lat_lng": [37.7749, -122.4194],
    "distance": 50,
    "unit": "km"
  }
}
```

