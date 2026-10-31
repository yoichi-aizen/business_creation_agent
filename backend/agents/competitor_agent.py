"""
Competitor Intelligence & Talent Poaching Subagent
Tracks competitor roadmaps, department headcount growth, technographics,
and triggers the 'Poaching Loop' when key talent moves.
"""

import logging
from typing import Dict, Any, List
from backend.models.blueprint import CompetitorAgentConfig, StartupBlueprint
from backend.models.database import db
from backend.services.crustdata_funnel import crustdata_funnel
from backend.agents.event_bus import event_bus

logger = logging.getLogger("competitor_agent")


class CompetitorAgent:
    async def run(self, blueprint: StartupBlueprint, project_id: str) -> Dict[str, Any]:
        cfg: CompetitorAgentConfig = blueprint.agents.competitor_agent
        if not cfg.enabled:
            return {"status": "DISABLED"}

        run_id = db.record_agent_run(project_id, "COMPETITOR_AGENT", "RUNNING")
        db.log_agent_action(
            project_id,
            "COMPETITOR_AGENT",
            "CRUSTDATA_SEARCH",
            f"Scanning competitors {', '.join(cfg.seed_competitors)} for department headcount shifts and technographics"
        )

        competitors = crustdata_funnel.funnel_competitors(cfg.seed_competitors)

        db.log_agent_action(
            project_id,
            "COMPETITOR_AGENT",
            "LLM_SYNTHESIS",
            f"Extracted {len(competitors)} competitor profiles. Tracking live engineering openings and tech stack vulnerabilities."
        )

        saved = []
        for comp in competitors:
            ent_id = db.save_entity(
                project_id=project_id,
                entity_type="COMPETITOR",
                name=comp["name"],
                identifier=comp["domain"],
                match_score=0.95 if comp.get("threat_level") == "HIGH" else 0.85,
                status="DISCOVERED",
                raw_data=comp
            )
            comp["id"] = ent_id
            saved.append(comp)

        db.update_agent_run(run_id, "COMPLETED", credits_used=0.4, summary=f"Tracking {len(saved)} competitors")
        return {"status": "COMPLETED", "competitors_count": len(saved)}

    async def trigger_talent_departure(
        self,
        project_id: str,
        project_name: str,
        candidate_name: str = "Gautam Raj",
        previous_company: str = "Stripe",
        role: str = "Staff Distributed Systems Engineer",
        profile_url: str = "https://www.linkedin.com/in/gautamraj"
    ):
        """
        Emits the HIGH_VALUE_TALENT_DEPARTURE domain event through the Event Bus
        to wake up the Talent Agent within 60s!
        """
        db.log_agent_action(
            project_id,
            "COMPETITOR_AGENT",
            "EVENT_EMITTED",
            f"Detected engineer departure at {previous_company}: {candidate_name} ({role}). Emitting domain event to Talent Agent!"
        )

        await event_bus.emit({
            "event_type": "HIGH_VALUE_TALENT_DEPARTURE",
            "source_agent": "competitor_agent",
            "target_agent": "talent_agent",
            "payload": {
                "project_id": project_id,
                "project_name": project_name,
                "candidate_name": candidate_name,
                "previous_company": previous_company,
                "role": role,
                "profile_url": profile_url,
                "priority": "CRITICAL"
            }
        })


competitor_agent = CompetitorAgent()

