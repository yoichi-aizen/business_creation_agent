"""
Crustdata Hackathon Project Starter Recipes
Four production-ready patterns for building B2B AI applications.

Usage:
    export CRUSTDATA_API_KEY="your_key"
    python examples/hackathon_starters.py
"""

import os
import sys
import json

# Ensure parent directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from crustdata_client import CrustdataClient, CrustdataError


def recipe_1_competitive_displacement(client: CrustdataClient, competitor_tech: str = "Salesforce", target_country: str = "USA"):
    """
    Recipe 1: Competitive Displacement Finder
    Find companies currently running a competitor tool within a specific country and headcount range,
    then enrich the top match with full technographics and decision makers.
    """
    print(f"\n--- [Recipe 1] Finding companies using '{competitor_tech}' in {target_country} ---")

    filters = {
      "op": "and",
      "conditions": [
        { "field": "locations.country", "type": "=", "value": target_country },
        { "field": "headcount.headcount", "type": "=>", "value": 50 },
        { "field": "headcount.headcount", "type": "=<", "value": 500 },
        { "field": "technographics.technologies.name", "type": "=", "value": competitor_tech }
      ]
    }

    try:
        results = client.search_companies(
            filters=filters,
            limit=5,
            fields=["basic_info", "headcount", "funding"]
        )
        companies = results.get("companies", [])
        print(f"Found {results.get('total_count', len(companies))} companies running {competitor_tech}.")
        for c in companies[:3]:
            basic = c.get("basic_info", {})
            print(f" - {basic.get('name')} ({basic.get('primary_domain')}): ~{c.get('headcount', {}).get('headcount')} employees")

        # Enrich the first company to get full tech stack and executives
        if companies:
            first_domain = companies[0].get("basic_info", {}).get("primary_domain")
            if first_domain:
                print(f"\nEnriching tech stack & CXOs for: {first_domain}...")
                enriched = client.enrich_company(
                    domains=[first_domain],
                    fields=["basic_info", "people", "technographics"]
                )
                if enriched and enriched[0].get("matches"):
                    match_data = enriched[0]["matches"][0]["company_data"]
                    tech_data = match_data.get("technographics", {})
                    print(f"Total technologies detected: {tech_data.get('total_technologies')}")
                    print(f"Top technologies: {', '.join(tech_data.get('top_technologies', [])[:8])}")
    except CrustdataError as e:
        print(f"Recipe 1 Error: {e}")


def recipe_2_hiring_signals_tracker(client: CrustdataClient, technology: str = "Kubernetes"):
    """
    Recipe 2: Hiring Signals & Stack Expansion Tracker
    Find active job openings requiring specific engineering tools (posting-level technographics).
    """
    print(f"\n--- [Recipe 2] Finding active job postings requiring '{technology}' ---")

    filters = {
      "op": "and",
      "conditions": [
        { "field": "technographics.technologies.name", "type": "=", "value": technology },
        { "field": "locations.country", "type": "=", "value": "USA" }
      ]
    }

    try:
        results = client.search_jobs(
            filters=filters,
            limit=5,
            sorts=[{"field": "metadata.date_added", "order": "desc"}],
            fields=[
                "crustdata_job_id",
                "job_details.title",
                "job_details.location",
                "company.basic_info.name",
                "company.basic_info.primary_domain",
                "metadata.date_added"
            ]
        )
        jobs = results.get("jobs", [])
        print(f"Found {len(jobs)} recent open roles requiring {technology}:")
        for j in jobs:
            details = j.get("job_details", {})
            company = j.get("company", {}).get("basic_info", {})
            print(f" - [{company.get('name')}] {details.get('title')} ({details.get('location')}) posted on {j.get('metadata', {}).get('date_added')}")
    except CrustdataError as e:
        print(f"Recipe 2 Error: {e}")


def recipe_3_executive_hunter_semantic(client: CrustdataClient, query: str = "Head of AI or VP of Engineering building LLM agents"):
    """
    Recipe 3: Executive & Talent Hunter with Semantic Search
    Uses natural-language queries across professional profiles with structured title normalization.
    """
    print(f"\n--- [Recipe 3] Semantic search for talent: '{query}' ---")

    try:
        results = client.search_people(
            search_query=query,
            search_mode="hybrid",
            limit=5,
            fields=["basic_profile", "experience"]
        )
        profiles = results.get("profiles", [])
        print(f"Found {len(profiles)} matching profiles:")
        for p in profiles:
            basic = p.get("basic_profile", {})
            norm_title = basic.get("normalized_title", {})
            print(f" - {basic.get('name')} | {basic.get('headline')}")
            if norm_title:
                print(f"   Normalized: {norm_title.get('department')} -> {norm_title.get('matched_title')}")
    except CrustdataError as e:
        print(f"Recipe 3 Error: {e}")


def main():
    api_key = os.environ.get("CRUSTDATA_API_KEY")
    if not api_key:
        print("Please export CRUSTDATA_API_KEY before running hackathon recipes.")
        return

    client = CrustdataClient(api_key=api_key)
    print("Crustdata Client initialized.")
    recipe_1_competitive_displacement(client, competitor_tech="Snowflake", target_country="USA")
    recipe_2_hiring_signals_tracker(client, technology="Next.js")
    recipe_3_executive_hunter_semantic(client)
    print(f"\nTotal Credits Used across recipes: {client.total_credits_used}")


if __name__ == "__main__":
    main()

