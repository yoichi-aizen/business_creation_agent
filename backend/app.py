"""
FastAPI Application Root
Implements REST endpoints, SSE event streaming, Crustdata webhooks,
and serves the Master Control Dashboard.
"""

import os
import json
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from backend import config
from backend.models.blueprint import StartupBlueprint
from backend.models.database import db
from backend.services.prompt_enricher import generate_blueprint_from_prompt
from backend.agents.supervisor import supervisor
from backend.agents.event_bus import event_bus
from backend.services.watcher_service import watcher_service

app = FastAPI(
    title="Autonomous Startup OS ('Founder-in-a-Box')",
    description="Multi-agent operations swarm powered by Crustdata B2B Intelligence",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ------------------------------------------------------------------------------
# 1. Blueprint Generation & Editing
# ------------------------------------------------------------------------------

@app.post("/api/blueprint/generate")
async def generate_blueprint(payload: Dict[str, str]):
    """
    Prompt to Blueprint: Takes founder natural language prompt and compiles it
    into a structured, editable config.yaml.
    """
    prompt = payload.get("prompt", "")
    if not prompt.strip():
        raise HTTPException(status_code=400, detail="Startup idea prompt cannot be empty.")

    blueprint = generate_blueprint_from_prompt(prompt)
    return {
        "blueprint": blueprint.model_dump(),
        "yaml": blueprint.to_yaml()
    }


@app.post("/api/blueprint/launch")
async def launch_orchestration(payload: Dict[str, Any], background_tasks: BackgroundTasks):
    """
    Kicks off the Parent Supervisor and dispatches the 4 subagents.
    """
    raw_prompt = payload.get("raw_prompt", "")
    yaml_content = payload.get("yaml", "")

    if yaml_content:
        blueprint = StartupBlueprint.from_yaml(yaml_content)
    elif "blueprint" in payload:
        blueprint = StartupBlueprint(**payload["blueprint"])
    else:
        raise HTTPException(status_code=400, detail="Must provide either 'yaml' or 'blueprint'.")

    # Run orchestration in background task so UI remains non-blocking
    background_tasks.add_task(supervisor.launch_project_orchestration, blueprint, raw_prompt)

    return {
        "status": "LAUNCHED",
        "project_id": blueprint.project_metadata.id,
        "name": blueprint.project_metadata.name
    }


# ------------------------------------------------------------------------------
# 2. Project State, Topology & Entities
# ------------------------------------------------------------------------------

@app.get("/api/project/current")
async def get_current_project():
    """Returns currently loaded project or latest from DB."""
    project = db.get_latest_project()
    if not project:
        # Load sample config if no project exists yet
        sample_path = Path(__file__).resolve().parent.parent / "sample_config.yaml"
        if sample_path.exists():
            with open(sample_path) as f:
                content = f.read()
            bp = StartupBlueprint.from_yaml(content)
            db.save_project(bp.project_metadata.id, bp.project_metadata.name, "BuildPay sample", content)
            project = db.get_latest_project()

    if not project:
        return {"project": None}

    return {
        "project": project,
        "yaml": project["config_yaml"]
    }


@app.get("/api/topology")
async def get_topology():
    """Returns real-time node status for Parent Supervisor and the 4 Subagents."""
    proj = db.get_latest_project()
    project_id = proj["id"] if proj else "proj_default"
    return supervisor.get_topology_status(project_id)


@app.get("/api/entities")
async def get_entities(type: Optional[str] = None):
    """
    Returns discovered Candidates, Vendors, VCs, and Competitors.
    """
    proj = db.get_latest_project()
    project_id = proj["id"] if proj else "proj_default"
    entities = db.get_entities(project_id, entity_type=type.upper() if type else None)
    return {"entities": entities}


@app.get("/api/logs")
async def get_logs(limit: int = 50):
    """Fetch granular agent audit logs."""
    proj = db.get_latest_project()
    project_id = proj["id"] if proj else "proj_default"
    return {"logs": db.get_audit_logs(project_id, limit=limit)}


# ------------------------------------------------------------------------------
# 3. Live Server-Sent Events (SSE) Log & Event Streaming
# ------------------------------------------------------------------------------

@app.get("/api/stream/events")
async def stream_events(request: Request):
    """
    Real-time SSE event stream powering the UI terminal and live topology pulses.
    """
    q = event_bus.register_sse_listener()

    async def event_generator():
        try:
            # Yield initial connection heartbeat
            yield {
                "event": "connected",
                "data": json.dumps({"status": "CONNECTED", "msg": "Event stream active"})
            }
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(q.get(), timeout=15.0)
                    yield {
                        "event": "agent_event",
                        "data": json.dumps(event)
                    }
                except asyncio.TimeoutError:
                    # Heartbeat
                    yield {
                        "event": "ping",
                        "data": json.dumps({"timestamp": "ping"})
                    }
        finally:
            event_bus.remove_sse_listener(q)

    return EventSourceResponse(event_generator())


# ------------------------------------------------------------------------------
# 4. Human-In-The-Loop Approval & Outreach
# ------------------------------------------------------------------------------

@app.post("/api/outreach/{entity_id}/approve")
async def approve_outreach(entity_id: str):
    """
    1-Click Approve & Send action on the dashboard.
    Marks status from DRAFT_READY -> EMAIL_SENT.
    """
    db.update_entity_status(entity_id, status="EMAIL_SENT")
    proj = db.get_latest_project()
    if proj:
        db.log_agent_action(
            proj["id"],
            "SUPERVISOR",
            "EMAIL_DISPATCHED",
            f"Founder approved email outreach for entity {entity_id}. Dispatched via delivery worker."
        )
    return {"status": "SUCCESS", "entity_id": entity_id, "state": "EMAIL_SENT"}


# ------------------------------------------------------------------------------
# 5. Crustdata Webhook Receiver & Simulation Harness
# ------------------------------------------------------------------------------

@app.post("/webhooks/crustdata")
async def crustdata_webhook(request: Request):
    """
    Ingests live Crustdata Entity Watcher notifications.
    """
    payload = await request.json()
    result = await watcher_service.handle_crustdata_webhook(payload)
    return result


@app.post("/api/simulate/poach")
async def simulate_poaching():
    """
    Demo Trigger: Simulates an engineer departing a key competitor.
    Emits the poaching event and verifies the 60s wake-up loop.
    """
    proj = db.get_latest_project()
    project_id = proj["id"] if proj else "proj_default"
    project_name = proj["name"] if proj else "BuildPay AI"

    res = await watcher_service.simulate_poaching_event(
        project_id=project_id,
        project_name=project_name,
        candidate_name="Gautam Raj",
        previous_company="Stripe",
        role="Staff Distributed Systems Engineer",
        profile_url="https://www.linkedin.com/in/gautamraj"
    )
    return res


# ------------------------------------------------------------------------------
# 6. Master Control Dashboard Frontend
# ------------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """Serves the Master Control Dashboard."""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        with open(index_file) as f:
            return f.read()
    return "<h1>Autonomous Startup OS Dashboard</h1>"

