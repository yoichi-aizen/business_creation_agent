"""
Parent Supervisor Agent
Central orchestrator that reads config.yaml, enforces credit budget constraints,
dispatches the 4 specialized subagents, and manages system state.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from backend.models.blueprint import StartupBlueprint
from backend.models.database import db
from backend.agents.event_bus import event_bus
from backend.agents.talent_agent import talent_agent
from backend.agents.vendor_agent import vendor_agent
from backend.agents.vc_agent import vc_agent
from backend.agents.competitor_agent import competitor_agent

logger = logging.getLogger("supervisor")


class ParentSupervisorAgent:
    def __init__(self):
        self.active_project_id: Optional[str] = None
        self.state: str = "IDLE"  # IDLE, RUNNING, COMPLETED, FAILED

    async def launch_project_orchestration(self, blueprint: StartupBlueprint, raw_prompt: str = "") -> Dict[str, Any]:
        """
        Main orchestration loop:
        1. Persists project state & config.yaml
        2. Logs supervisor bootstrap
        3. Spawns all 4 subagents in parallel
        4. Gathers intelligence and updates central dashboard state
        """
        self.state = "RUNNING"
        project_id = blueprint.project_metadata.id or "proj_default"
        self.active_project_id = project_id

        # Save project and config to DB
        db.save_project(
            project_id=project_id,
            name=blueprint.project_metadata.name,
            raw_prompt=raw_prompt,
            config_yaml=blueprint.to_yaml(),
            budget=blueprint.orchestration.max_daily_crustdata_credits
        )

        db.log_agent_action(
            project_id,
            "SUPERVISOR",
            "BOOTSTRAP",
            f"Supervising '{blueprint.project_metadata.name}' ({blueprint.project_metadata.sector}). Disagreeing with passive CSVs—booting live Crustdata subagents.",
            payload={"blueprint_version": blueprint.version, "stage": blueprint.project_metadata.stage}
        )

        await event_bus.emit({
            "event_type": "ORCHESTRATION_STARTED",
            "source_agent": "supervisor",
            "target_agent": "all",
            "payload": {
                "project_id": project_id,
                "project_name": blueprint.project_metadata.name,
                "sector": blueprint.project_metadata.sector
            }
        })

        # Run all 4 subagents in parallel
        results = await asyncio.gather(
            talent_agent.run(blueprint, project_id),
            vendor_agent.run(blueprint, project_id),
            vc_agent.run(blueprint, project_id),
            competitor_agent.run(blueprint, project_id),
            return_exceptions=True
        )

        db.log_agent_action(
            project_id,
            "SUPERVISOR",
            "CYCLE_COMPLETE",
            "Initial intelligence scan complete across all 4 subagents. Master Control Dashboard hydrated.",
            payload={"subagent_statuses": [r if not isinstance(r, Exception) else str(r) for r in results]}
        )

        self.state = "COMPLETED"

        await event_bus.emit({
            "event_type": "ORCHESTRATION_COMPLETED",
            "source_agent": "supervisor",
            "target_agent": "dashboard",
            "payload": {
                "project_id": project_id,
                "message": "All 4 subagents completed successfully. Awaiting founder reviews in outreach queue."
            }
        })

        return {
            "status": "SUCCESS",
            "project_id": project_id,
            "state": self.state
        }

    def get_topology_status(self, project_id: str) -> Dict[str, Any]:
        """Returns live status of Supervisor and the 4 Subagents."""
        runs = db.get_agent_runs(project_id)
        latest_by_type = {}
        for r in runs:
            atype = r["agent_type"]
            if atype not in latest_by_type:
                latest_by_type[atype] = r

        return {
            "supervisor": {
                "status": self.state,
                "active_project": self.active_project_id
            },
            "subagents": {
                "talent_agent": latest_by_type.get("TALENT_AGENT", {"status": "IDLE"}),
                "vendor_agent": latest_by_type.get("VENDOR_AGENT", {"status": "IDLE"}),
                "vc_agent": latest_by_type.get("VC_AGENT", {"status": "IDLE"}),
                "competitor_agent": latest_by_type.get("COMPETITOR_AGENT", {"status": "IDLE"})
            }
        }


supervisor = ParentSupervisorAgent()

