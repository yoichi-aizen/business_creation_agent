"""
Cold Email Synthesis Service
Generates hyper-personalized cold outreach drafts for Talent and VCs based on
Crustdata career tenure, technographics, and social post signals.
"""

from typing import Dict, Any, Optional
from backend import config


def generate_talent_email(candidate: Dict[str, Any], project_name: str, sector: str) -> str:
    """
    Synthesizes candidate career tenure + recent social post + startup value proposition.
    """
    name = candidate.get("name", "there")
    first_name = name.split()[0] if name else "there"
    curr_company = candidate.get("current_company", "your team")
    recent_post = candidate.get("recent_posts", ["scaling production engineering"])[0]

    return f"""Subject: {project_name} & your work at {curr_company}

Hi {first_name},

Saw your impressive tenure scaling engineering at {curr_company}—and particularly enjoyed your recent insight: "{recent_post[:70]}..."

I'm the founder of {project_name}. We're building {sector}, solving manual AP reconciliation and payment workflows for mid-market teams. We're backed by top vertical fintech angels and currently looking for our Founding Engineer / Technical Lead.

Given your background in payments and ledger architecture, I'd love to share our technical roadmap and see if what we're building aligns with what you want to tackle next.

Would you be open to a casual 15-minute coffee or Zoom this Thursday?

Best,
The Founder
{project_name}"""


def generate_vc_email(vc: Dict[str, Any], project_name: str, sector: str) -> str:
    """
    Synthesizes VC thesis match + recent portfolio investments + warm intro angle.
    """
    name = vc.get("name", "there")
    first_name = name.split()[0] if name else "there"
    firm = vc.get("firm", "your fund")
    evidence = vc.get("thesis_evidence", "your focus on vertical SaaS")
    investments = ", ".join(vc.get("recent_investments", ["fintech"]))

    return f"""Subject: {project_name} (Pre-Seed) - {sector}

Hi {first_name},

Reaching out because of {firm}'s focus on vertical SaaS and your investments in {investments}.

I noticed your recent note: "{evidence[:80]}...". That thesis is exactly why we started {project_name}.

We are building {sector}. In short: automating construction invoice ingestion, lien waiver verification, and programmatic subcontractor ACH payouts on a single autonomous platform.

Quick traction snapshot:
- Architecture powered by real-time B2B intelligence and autonomous agent supervision
- Initial customer LOIs from 4 mid-market construction contractors ($35M combined volume)
- Experienced founding team with fintech and vertical software backgrounds

Raising a Pre-Seed round to accelerate integrations. Would love to send over our brief deck if this aligns with your current pipeline.

Best regards,
Founder, {project_name}"""


def generate_poaching_email(candidate_name: str, previous_company: str, role: str, project_name: str) -> str:
    """
    Triggered when an engineer departs a key competitor (The Poaching Loop).
    """
    first_name = candidate_name.split()[0] if candidate_name else "there"
    return f"""Subject: Congrats on the move / next chapter after {previous_company}

Hi {first_name},

Noticed your transition from {previous_company}—congratulations on concluding that chapter!

I'm the founder of {project_name}. Having tracked {previous_company}'s engineering moves, I know firsthand the depth of complex data and workflow challenges you tackled as {role}.

We are currently building the next-generation autonomous platform in this space and are quietly assembling a small, elite founding team. 

If you're exploring options or taking some time before your next move, I'd love to connect for 15 minutes to share what we're doing. Zero pressure, purely founder-to-engineer.

Congratulations again,
Founder, {project_name}"""

