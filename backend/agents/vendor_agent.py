"""
Third-Party Vendor / API Discovery Subagent
Evaluates B2B SaaS and API providers using live growth metrics (headcount, traffic, reviews).
"""

import logging
from typing import Dict, Any, List
from backend.models.blueprint import VendorAgentConfig, StartupBlueprint
from backend.models.database import db
from backend.services.crustdata_funnel import crustdata_funnel
from backend.agents.event_bus import event_bus

logger = logging.getLogger("vendor_agent")


class VendorAgent:
    async def run(self, blueprint: StartupBlueprint, project_id: str) -> Dict[str, Any]:
        cfg: VendorAgentConfig = blueprint.agents.vendor_agent
        if not cfg.enabled:
            return {"status": "DISABLED"}

        run_id = db.record_agent_run(project_id, "VENDOR_AGENT", "RUNNING")
        
        all_shortlisted = []
        for svc in cfg.required_services:
            db.log_agent_action(
                project_id,
                "VENDOR_AGENT",
                "CRUSTDATA_SEARCH",
                f"Benchmarking vendors for '{svc.service_id}' via category keywords: {', '.join(svc.category_keywords)}"
            )

            vendors = crustdata_funnel.funnel_vendors(
                category_keywords=svc.category_keywords,
                min_headcount=svc.min_headcount,
                limit=3
            )

            db.log_agent_action(
                project_id,
                "VENDOR_AGENT",
                "LLM_SYNTHESIS",
                f"Evaluated {len(vendors)} vendors for {svc.service_id}. Scoring by MoM web traffic, headcount trends, and SLA."
            )

            for v in vendors:
                v["service_category"] = svc.service_id
                ent_id = db.save_entity(
                    project_id=project_id,
                    entity_type="VENDOR",
                    name=v["name"],
                    identifier=v["domain"],
                    match_score=v.get("recommendation_score", 0.9),
                    status="SHORTLISTED",
                    raw_data=v
                )
                v["id"] = ent_id
                all_shortlisted.append(v)

        db.update_agent_run(run_id, "COMPLETED", credits_used=0.5, summary=f"Shortlisted {len(all_shortlisted)} API vendors")
        return {"status": "COMPLETED", "vendors_count": len(all_shortlisted)}


vendor_agent = VendorAgent()

