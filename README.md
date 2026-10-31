# Autonomous Startup OS ("Founder-in-a-Box")

[![Crustdata API](https://img.shields.io/badge/Crustdata%20API-v2025--11--01-indigo)](https://docs.crustdata.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python)](https://python.org)

An AI-native command center that transforms a solo founder's raw startup idea into an active, 24/7 operations team. Instead of spending months manually hunting for founding engineers, researching third-party APIs, building investor lists, and stalking competitors, a founder simply enters their idea—and an orchestrated swarm of specialized AI agents executes the groundwork autonomously.

---

## Architecture Overview

```
Founder Natural Language Prompt
         │
         ▼
[ Prompt Enricher & Pydantic SDK ] ──► [ Validated config.yaml ]
                                                │
                                                ▼
                                    [ PARENT SUPERVISOR AGENT ]
                                    (Routes Events & Enforces Budget)
                                                │
                 ┌──────────────┬───────────────┴──────────────┬──────────────┐
                 ▼              ▼                              ▼              ▼
          [ Talent Agent ] [ Vendor Agent ]              [ VC Agent ]   [ Competitor Agent ]
           (Recruiting)     (API/B2B SaaS)                (Fundraising)  (Intel & Radar)
                 │              │                              │              │
                 └──────────────┴───────────────┬──────────────┴──────────────┘
                                                ▼
                           [ Hub-and-Spoke Event Bus & SQLite State ]
                                                ▲
                                                │ (Triggers & Diffs)
                                    [ WATCHER INGESTION ENGINE ]
                                 (POST /webhooks/crustdata & Diff Cron)
```

### The 4 Autonomous Subagents & Watchers
1. **Talent & Recruiting Subagent**: Discovers high-caliber founding engineers (Ramp, Stripe, Brex, Procore alumni), enriches profiles with recent LinkedIn posts, and drafts hyper-personalized cold outreach emails into the Human-in-the-Loop queue.
2. **Third-Party Vendor / API Agent**: Benchmarks B2B SaaS and API providers needed to build the product using real growth metrics (headcount growth %, web traffic, employee reviews, and pricing models).
3. **VC & Investor Matching Subagent**: Identifies venture firms and specific partners with a high probability of investing by analyzing who funded similar vertical startups and which investors are actively posting about the founder's thesis.
4. **Competitor Intelligence & Talent Poaching Subagent**: Tracks competitor product roadmaps, department headcount shifts, and embedded tech stacks (technographics).
   - **The Poaching Loop**: When a key engineer leaves a competitor, emits a `HIGH_VALUE_TALENT_DEPARTURE` event to the Parent Supervisor, waking up the Talent Agent within 60 seconds to draft an instant outreach email!

---

## Quickstart

### 1. Configure Your API Keys
Open `.env` in the root folder and add your Crustdata API key:
```bash
CRUSTDATA_API_KEY="your_crustdata_api_key_here"
```
*(Optional: Add `GEMINI_API_KEY` for LLM prompt compilation and email synthesis.)*

### 2. Activate Virtual Environment & Run
```bash
# Activate existing virtual environment
source .venv/bin/activate

# Launch the OS Server & Dashboard
python run.py
```

### 3. Open the Master Control Dashboard
Navigate to:
```
http://localhost:8000
```

---

## 5 Core Dashboard Views

1. **Command & Config View**: Visual form and raw YAML code editor for `config.yaml`.
2. **Agent Swarm Topology & Live Terminal**: Real-time pulsing node graph showing the Parent Supervisor and 4 Subagents, accompanied by a live-streaming SSE terminal log drawer.
3. **HITL Outreach Queue**: Split-screen candidate/VC profile cards paired with AI-drafted outreach and a 1-Click **"Approve & Send"** button.
4. **Vendor Comparison Matrix**: Side-by-side scorecard ranking B2B API providers by traffic growth, headcount trends, and pricing.
5. **Competitor Radar & Watcher Feed**: Real-time competitor tech stack breakdown, active job openings, and a **"Simulate Poaching Loop"** trigger.

---

## Testing

Run the automated integration test suite:
```bash
.venv/bin/python tests/test_backend.py
```
