"""
Integration Test Suite for Autonomous Startup OS
Tests the Prompt Enricher, Supervisor Agent, Event Bus, Funnel, and REST endpoints.
"""

import sys
from pathlib import Path

# Ensure root dir is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio
from fastapi.testclient import TestClient
from backend.app import app
from backend.services.prompt_enricher import generate_blueprint_from_prompt
from backend.models.blueprint import StartupBlueprint
from backend.models.database import db
from backend.agents.supervisor import supervisor

client = TestClient(app)

def test_prompt_to_blueprint():
    prompt = "I want to build an AI-powered automated accounts payable platform for mid-market construction companies in the US."
    bp = generate_blueprint_from_prompt(prompt)
    assert isinstance(bp, StartupBlueprint)
    assert bp.project_metadata.name != ""
    assert bp.agents.talent_agent.enabled is True
    assert len(bp.agents.talent_agent.target_roles) > 0
    yaml_str = bp.to_yaml()
    assert "project_metadata" in yaml_str
    print("✓ Prompt-to-Blueprint test passed!")

def test_api_endpoints():
    # 1. Blueprint Generate
    res = client.post("/api/blueprint/generate", json={
        "prompt": "AI accounts payable for construction contractors"
    })
    assert res.status_code == 200
    data = res.json()
    assert "yaml" in data

    # 2. Project Current
    res = client.get("/api/project/current")
    assert res.status_code == 200

    # 3. Topology
    res = client.get("/api/topology")
    assert res.status_code == 200

    # 4. Entities
    res = client.get("/api/entities")
    assert res.status_code == 200

    # 5. Simulate Poaching Loop
    res = client.post("/api/simulate/poach")
    assert res.status_code == 200
    assert res.json()["status"] == "SIMULATION_EMITTED"
    print("✓ API Endpoints test passed!")

def test_supervisor_orchestration():
    prompt = "AI accounts payable for construction"
    bp = generate_blueprint_from_prompt(prompt)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    res = loop.run_until_complete(supervisor.launch_project_orchestration(bp, prompt))
    assert res["status"] == "SUCCESS"
    assert supervisor.state == "COMPLETED"

    # Verify entities were saved
    entities = db.get_entities(bp.project_metadata.id)
    assert len(entities) > 0
    print(f"✓ Supervisor test passed! Saved {len(entities)} discovered entities.")

if __name__ == "__main__":
    test_prompt_to_blueprint()
    test_api_endpoints()
    test_supervisor_orchestration()
    print("\n🎉 ALL TESTS PASSED SUCCESSFULLY!")
