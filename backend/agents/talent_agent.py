"""
Talent & Recruiting Subagent
Identifies 10x founding engineers and operators, monitors movements, and drafts outreach.
"""

import logging
from typing import Dict, Any, List
from backend.models.blueprint import TalentAgentConfig, StartupBlueprint
from backend.models.database import db
from backend.services.crustdata_funnel import crustdata_funnel
from backend.services.email_service import generate_talent_email, generate_poaching_email
from backend.agents.event_bus import event_bus

logger = logging.getLogger("talent_agent")


class TalentAgent:
    def __init__(self):
        # Subscribe to poaching events from Competitor Agent
        event_bus.subscribe("HIGH_VALUE_TALENT_DEPARTURE", self.handle_poaching_event)

    async def run(self, blueprint: StartupBlueprint, project_id: str) -> Dict[str, Any]:
        cfg: TalentAgentConfig = blueprint.agents.talent_agent
        if not cfg.enabled:
            return {"status": "DISABLED"}

        run_id = db.record_agent_run(project_id, "TALENT_AGENT", "RUNNING")
        db.log_agent_action(
            project_id,
            "TALENT_AGENT",
            "CRUSTDATA_SEARCH",
            f"Querying Crustdata Person DB for candidates at {', '.join(cfg.target_company_backgrounds[:3])} with skills {', '.join(cfg.required_skills[:3])}"
        )

        # Execute two-stage talent funnel
        candidates = crustdata_funnel.funnel_talent(
            target_companies=cfg.target_company_backgrounds,
            roles=cfg.target_roles,
            skills=cfg.required_skills,
            limit=4
        )

        db.log_agent_action(
            project_id,
            "TALENT_AGENT",
            "LLM_SYNTHESIS",
            f"Enriched {len(candidates)} candidates. Synthesizing hyper-personalized cold outreach drafts..."
        )

        saved_candidates = []
        for cand in candidates:
            draft = generate_talent_email(
                cand,
                blueprint.project_metadata.name,
                blueprint.project_metadata.sector
            )
            ent_id = db.save_entity(
                project_id=project_id,
                entity_type="CANDIDATE",
                name=cand["name"],
                identifier=cand["profile_url"],
                match_score=cand["match_score"],
                status="DRAFT_READY",
                raw_data=cand,
                email_draft=draft
            )
            cand["id"] = ent_id
            saved_candidates.append(cand)

        # Register top candidate with Entity Watcher
        if saved_candidates:
            top_cand = saved_candidates[0]
            watch_id = db.save_watcher(project_id, "PERSON", top_cand["profile_url"], "query_watch_talent")
            db.log_agent_action(
                project_id,
                "TALENT_AGENT",
                "WATCHER_REGISTERED",
                f"Registered Person Entity Watcher for {top_cand['name']} ({top_cand['profile_url']})"
            )

        db.update_agent_run(run_id, "COMPLETED", credits_used=0.23, summary=f"Shortlisted {len(saved_candidates)} candidates")
        return {"status": "COMPLETED", "candidates_count": len(saved_candidates)}

    async def handle_poaching_event(self, event: Dict[str, Any]):
        """
        Woken up by Competitor Agent when a key engineer departs!
        """
        payload = event.get("payload", {})
        cand_name = payload.get("candidate_name", "Gautam Raj")
        prev_comp = payload.get("previous_company", "Stripe")
        role = payload.get("role", "Staff Software Engineer")
        project_id = payload.get("project_id", "proj_default")
        proj_name = payload.get("project_name", "BuildPay AI")
        prof_url = payload.get("profile_url") or "https://www.linkedin.com/in/gautamraj"

        logger.info(f"Poaching loop triggered for: {cand_name} from {prev_comp}")
        db.log_agent_action(
            project_id,
            "TALENT_AGENT",
            "POACHING_ALERT",
            f"⚡ CRITICAL POACHING SIGNAL: {cand_name} departed {prev_comp}. Allocating credits & drafting instant outreach!"
        )

        draft = generate_poaching_email(cand_name, prev_comp, role, proj_name)

        cand_data = {
            "name": cand_name,
            "headline": f"Ex-{prev_comp} | {role}",
            "title": role,
            "department": "Engineering",
            "profile_url": prof_url,
            "current_company": f"Ex-{prev_comp}",
            "match_score": 0.99,
            "recent_posts": [f"Wrapping up my journey at {prev_comp}. Excited for what is next in distributed systems."]
        }

        db.save_entity(
            project_id=project_id,
            entity_type="CANDIDATE",
            name=cand_name,
            identifier=cand_data["profile_url"],
            match_score=0.99,
            status="DRAFT_READY",
            raw_data=cand_data,
            email_draft=draft
        )

        # Notify UI via event bus
        await event_bus.emit({
            "event_type": "POACHING_ALERT_READY",
            "source_agent": "talent_agent",
            "target_agent": "dashboard",
            "payload": {
                "candidate_name": cand_name,
                "previous_company": prev_comp,
                "role": role,
                "message": f"Outreach draft ready for {cand_name} (departed {prev_comp})"
            }
        })


talent_agent = TalentAgent()

