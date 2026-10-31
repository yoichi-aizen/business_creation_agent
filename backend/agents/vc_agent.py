"""
VC & Investor Matching Subagent
Identifies venture firms and specific partners with high probability of investing
based on similar startup funding rounds and active social post thesis alignment.
"""

import logging
from typing import Dict, Any, List
from backend.models.blueprint import VcAgentConfig, StartupBlueprint
from backend.models.database import db
from backend.services.crustdata_funnel import crustdata_funnel
from backend.services.email_service import generate_vc_email
from backend.agents.event_bus import event_bus

logger = logging.getLogger("vc_agent")


class VcAgent:
    async def run(self, blueprint: StartupBlueprint, project_id: str) -> Dict[str, Any]:
        cfg: VcAgentConfig = blueprint.agents.vc_agent
        if not cfg.enabled:
            return {"status": "DISABLED"}

        run_id = db.record_agent_run(project_id, "VC_AGENT", "RUNNING")
        db.log_agent_action(
            project_id,
            "VC_AGENT",
            "CRUSTDATA_SEARCH",
            f"Querying Crustdata for {blueprint.project_metadata.sector} funding rounds & matching Partners ({', '.join(cfg.target_partner_titles[:2])})"
        )

        vcs = crustdata_funnel.funnel_vcs(
            sector=blueprint.project_metadata.sector,
            thesis_keywords=cfg.thesis_keywords,
            stages=cfg.target_stages,
            limit=3
        )

        db.log_agent_action(
            project_id,
            "VC_AGENT",
            "LLM_SYNTHESIS",
            f"Matched {len(vcs)} thesis-aligned venture partners. Synthesizing warm-intro pitches citing recent portco rounds..."
        )

        saved_vcs = []
        for vc in vcs:
            draft = generate_vc_email(
                vc,
                blueprint.project_metadata.name,
                blueprint.project_metadata.sector
            )
            ent_id = db.save_entity(
                project_id=project_id,
                entity_type="VC",
                name=f"{vc['name']} ({vc['firm']})",
                identifier=vc["profile_url"],
                match_score=vc["thesis_match_score"],
                status="DRAFT_READY",
                raw_data=vc,
                email_draft=draft
            )
            vc["id"] = ent_id
            saved_vcs.append(vc)

        db.update_agent_run(run_id, "COMPLETED", credits_used=0.35, summary=f"Matched {len(saved_vcs)} thesis-aligned VCs")
        return {"status": "COMPLETED", "vcs_count": len(saved_vcs)}


vc_agent = VcAgent()

