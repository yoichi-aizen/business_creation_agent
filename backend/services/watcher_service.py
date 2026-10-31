"""
Watcher & Ingestion Engine
Handles incoming webhooks from Crustdata Entity Watchers and simulates live diff checks.
"""

import logging
from typing import Dict, Any
from backend.models.database import db
from backend.agents.event_bus import event_bus
from backend.agents.competitor_agent import competitor_agent

logger = logging.getLogger("watcher_service")


class WatcherService:
    async def handle_crustdata_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes real webhook delivery from Crustdata Watcher endpoints.
        Payload carries entity diff (e.g., employment_details changed).
        """
        event_name = payload.get("event") or payload.get("type", "ENTITY_UPDATED")
        logger.info(f"Received Crustdata webhook: {event_name}")

        diff = payload.get("diff", {})
        entity_id = payload.get("entity_id") or payload.get("crustdata_person_id")

        # Check if an employment end-date changed (job departure)
        if "experience" in diff or "employment_details" in diff or "job_departure" in str(payload).lower():
            cand_name = payload.get("name", "Departing Engineer")
            prev_comp = payload.get("previous_company", "Competitor")
            role = payload.get("role", "Senior Software Engineer")
            proj_id = payload.get("project_id", "proj_default")

            await competitor_agent.trigger_talent_departure(
                project_id=proj_id,
                project_name="Startup",
                candidate_name=cand_name,
                previous_company=prev_comp,
                role=role
            )
            return {"status": "POACHING_TRIGGERED", "candidate": cand_name}

        return {"status": "INGESTED", "event": event_name}

    async def simulate_poaching_event(
        self,
        project_id: str,
        project_name: str = "BuildPay AI",
        candidate_name: str = "Gautam Raj",
        previous_company: str = "Stripe",
        role: str = "Staff Distributed Systems Engineer",
        profile_url: str = "https://www.linkedin.com/in/gautamraj"
    ) -> Dict[str, Any]:
        """
        Demo harness: Simulates a Crustdata Entity Watcher webhook firing.
        Demonstrates the real-time Poaching Loop for hackathon presentations.
        """
        await competitor_agent.trigger_talent_departure(
            project_id=project_id,
            project_name=project_name,
            candidate_name=candidate_name,
            previous_company=previous_company,
            role=role,
            profile_url=profile_url
        )
        return {
            "status": "SIMULATION_EMITTED",
            "candidate": candidate_name,
            "previous_company": previous_company,
            "role": role,
            "profile_url": profile_url
        }


watcher_service = WatcherService()

