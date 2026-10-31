"""
Layer 1: Prompt Enricher & Config SDK
Converts raw founder prompt into a strictly validated StartupBlueprint (config.yaml).
Uses Gemini / LLM if available, with an intelligent domain heuristic fallback.
"""

import os
import re
import json
import logging
from typing import Optional
from backend.models.blueprint import (
    StartupBlueprint,
    ProjectMetadata,
    OrchestrationConfig,
    AgentsConfig,
    TalentAgentConfig,
    VendorAgentConfig,
    RequiredService,
    VcAgentConfig,
    CompetitorAgentConfig
)
from backend import config

logger = logging.getLogger("prompt_enricher")


def enrich_prompt_heuristic(raw_prompt: str) -> StartupBlueprint:
    """Intelligent fallback synthesizer based on industry patterns."""
    p_lower = raw_prompt.lower()

    # Determine Project Name & Sector
    name = "NewCo AI"
    sector = "B2B SaaS / Applied AI"

    if "construction" in p_lower and ("payable" in p_lower or "invoice" in p_lower or "accounting" in p_lower):
        name = "BuildPay AI"
        sector = "Construction Fintech / Automated Accounts Payable"
        roles = ["Founding Engineer", "Senior Full-Stack Engineer", "Head of Growth"]
        skills = ["TypeScript", "Go", "PostgreSQL", "Fintech", "LLM Orchestration"]
        backgrounds = ["Procore", "Ramp", "Brex", "Stripe", "Plaid", "Briq"]
        vendor_services = [
            RequiredService(
                service_id="ocr_engine",
                category_keywords=["Document AI", "Invoice OCR API", "Financial Document Parsing"],
                min_headcount=15,
                min_traffic_growth_mom=5.0
            ),
            RequiredService(
                service_id="payment_rails",
                category_keywords=["Embedded Payments API", "B2B ACH Issuing", "Banking as a Service"],
                min_headcount=50,
                min_traffic_growth_mom=0.0
            )
        ]
        thesis_keywords = ["Construction Tech", "B2B Fintech", "Vertical SaaS", "CFO Stack"]
        competitors = ["briq.com", "sitetracker.com", "ramp.com"]

    elif "healthcare" in p_lower or "medical" in p_lower or "clinic" in p_lower:
        name = "CareFlow AI"
        sector = "Digital Health / Clinical Workflow Automation"
        roles = ["Founding Engineer", "Full-Stack Bio Engineer", "Head of Product"]
        skills = ["Python", "TypeScript", "FHIR / HL7", "HIPAA Compliance", "FastAPI"]
        backgrounds = ["Epic", "Cerner", "Flatiron Health", "Oscar Health", "Ro"]
        vendor_services = [
            RequiredService(
                service_id="ehr_integrations",
                category_keywords=["EHR Integration API", "Healthcare Interoperability", "FHIR API"],
                min_headcount=20
            ),
            RequiredService(
                service_id="hipaa_storage",
                category_keywords=["HIPAA Compliant Cloud", "Medical Document Storage"],
                min_headcount=30
            )
        ]
        thesis_keywords = ["Digital Health", "HealthTech", "AI Clinical Copilots", "Workflow Automation"]
        competitors = ["athenahealth.com", "doximity.com", "canvasmedical.com"]

    elif "legal" in p_lower or "law" in p_lower or "contract" in p_lower:
        name = "LexiCraft AI"
        sector = "LegalTech / AI Contract Intelligence"
        roles = ["Founding Engineer", "LLM Systems Engineer", "Head of Sales"]
        skills = ["Python", "TypeScript", "Vector Search", "LangChain", "RAG Systems"]
        backgrounds = ["Ironclad", "Robin AI", "Harvey", "EvenUp", "Palantir"]
        vendor_services = [
            RequiredService(
                service_id="contract_diff",
                category_keywords=["Document Comparison API", "PDF Parsing API"],
                min_headcount=10
            )
        ]
        thesis_keywords = ["LegalTech", "Enterprise AI", "Contract Lifecycle Management", "Vertical AI"]
        competitors = ["ironcladapp.com", "harvey.ai", "robinai.com"]

    else:
        # General AI B2B
        first_few_words = [w for w in re.findall(r"\w+", raw_prompt) if len(w) > 3][:2]
        if first_few_words:
            name = "".join(w.capitalize() for w in first_few_words) + " AI"
        roles = ["Founding Full-Stack Engineer", "Founding AI/ML Engineer", "Head of Growth"]
        skills = ["TypeScript", "Python", "PostgreSQL", "RAG", "Next.js", "Docker"]
        backgrounds = ["Stripe", "Ramp", "OpenAI", "Databricks", "Vercel"]
        vendor_services = [
            RequiredService(
                service_id="llm_gateway",
                category_keywords=["LLM Gateway", "AI Model Provider", "Vector Database"],
                min_headcount=10
            )
        ]
        thesis_keywords = ["B2B SaaS", "Vertical AI", "Applied AI", "Developer Tooling"]
        competitors = ["notion.so", "linear.app", "ramp.com"]

    return StartupBlueprint(
        project_metadata=ProjectMetadata(
            name=name,
            sector=sector,
            stage="Pre-Seed",
            geography=["United States"]
        ),
        orchestration=OrchestrationConfig(
            max_daily_crustdata_credits=500,
            human_in_the_loop_outreach=True
        ),
        agents=AgentsConfig(
            talent_agent=TalentAgentConfig(
                enabled=True,
                target_roles=roles,
                required_skills=skills,
                target_company_backgrounds=backgrounds,
                seniority_levels=["Senior", "Staff", "Principal", "Founder"]
            ),
            vendor_agent=VendorAgentConfig(
                enabled=True,
                required_services=vendor_services,
                watch_interval_days=7
            ),
            vc_agent=VcAgentConfig(
                enabled=True,
                target_stages=["Pre-Seed", "Seed"],
                thesis_keywords=thesis_keywords
            ),
            competitor_agent=CompetitorAgentConfig(
                enabled=True,
                seed_competitors=competitors,
                auto_discover_similar=True
            )
        )
    )


def enrich_prompt_with_gemini(raw_prompt: str, api_key: str) -> Optional[StartupBlueprint]:
    """Uses Google GenAI SDK to generate structured StartupBlueprint."""
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        system_instruction = """
        You are an elite Silicon Valley venture builder and CTO assistant.
        Given a founder's raw startup idea, extract and infer a structured startup blueprint.
        You must output JSON matching the StartupBlueprint Pydantic model:
        {
          "version": "1.0",
          "project_metadata": { "name": str, "sector": str, "stage": "Pre-Seed", "geography": ["United States"] },
          "orchestration": { "max_daily_crustdata_credits": 500, "human_in_the_loop_outreach": true },
          "agents": {
            "talent_agent": {
              "enabled": true,
              "target_roles": ["Founding Engineer", ...],
              "required_skills": ["TypeScript", ...],
              "target_company_backgrounds": ["Stripe", "Procore", ...],
              "seniority_levels": ["Senior", "Staff", ...]
            },
            "vendor_agent": {
              "enabled": true,
              "required_services": [
                { "service_id": "ocr", "category_keywords": ["Invoice OCR", ...], "min_headcount": 15, "min_traffic_growth_mom": 5.0 }
              ],
              "watch_interval_days": 7
            },
            "vc_agent": {
              "enabled": true,
              "target_stages": ["Pre-Seed", "Seed"],
              "thesis_keywords": ["Construction Tech", "Vertical SaaS", ...]
            },
            "competitor_agent": {
              "enabled": true,
              "seed_competitors": ["domain1.com", "domain2.com"],
              "auto_discover_similar": true
            }
          }
        }
        """

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"Founder Startup Idea:\n{raw_prompt}",
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                temperature=0.2
            )
        )

        data = json.loads(response.text)
        return StartupBlueprint(**data)
    except Exception as e:
        logger.warning(f"Gemini enrichment failed or unavailable: {e}. Falling back to heuristic synthesizer.")
        return None


def generate_blueprint_from_prompt(raw_prompt: str) -> StartupBlueprint:
    """Main entrypoint: Tries LLM if API key present, otherwise falls back smoothly to heuristic."""
    gemini_key = config.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")
    if gemini_key:
        bp = enrich_prompt_with_gemini(raw_prompt, gemini_key)
        if bp:
            return bp
    return enrich_prompt_heuristic(raw_prompt)

