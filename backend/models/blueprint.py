"""
Pydantic Schema for config.yaml (Single Source of Truth)
Defines project metadata, budget orchestration, and configuration for all 4 subagents.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import yaml


class ProjectMetadata(BaseModel):
    id: str = Field(default="proj_default")
    name: str = Field(description="Name of the startup project")
    sector: str = Field(description="Sector and vertical definition")
    stage: str = Field(default="Pre-Seed", description="Startup stage (e.g., Pre-Seed, Seed, Series A)")
    geography: List[str] = Field(default_factory=lambda: ["United States"])


class OrchestrationConfig(BaseModel):
    max_daily_crustdata_credits: int = Field(default=500, description="Daily credit budget ceiling")
    human_in_the_loop_outreach: bool = Field(default=True, description="Require human approval before sending emails")


class TalentAgentConfig(BaseModel):
    enabled: bool = True
    target_roles: List[str] = Field(default_factory=lambda: ["Founding Engineer", "Senior Full-Stack Engineer"])
    required_skills: List[str] = Field(default_factory=lambda: ["TypeScript", "Python", "PostgreSQL"])
    target_company_backgrounds: List[str] = Field(default_factory=lambda: ["Stripe", "Ramp", "Brex"])
    seniority_levels: List[str] = Field(default_factory=lambda: ["Senior", "Staff", "Principal", "Founder"])
    watch_triggers: List[str] = Field(default_factory=lambda: [
        "job_departure",
        "open_to_work_flag",
        "new_profile_matching_criteria"
    ])


class RequiredService(BaseModel):
    service_id: str
    category_keywords: List[str] = Field(default_factory=list)
    min_headcount: int = Field(default=10)
    min_traffic_growth_mom: float = Field(default=0.0)


class VendorAgentConfig(BaseModel):
    enabled: bool = True
    required_services: List[RequiredService] = Field(default_factory=list)
    watch_interval_days: int = Field(default=7)


class VcAgentConfig(BaseModel):
    enabled: bool = True
    target_stages: List[str] = Field(default_factory=lambda: ["Pre-Seed", "Seed"])
    thesis_keywords: List[str] = Field(default_factory=list)
    target_partner_titles: List[str] = Field(default_factory=lambda: [
        "Partner", "General Partner", "Principal", "Managing Director"
    ])


class CompetitorAgentConfig(BaseModel):
    enabled: bool = True
    seed_competitors: List[str] = Field(default_factory=list)
    auto_discover_similar: bool = True
    track_metrics: List[str] = Field(default_factory=lambda: [
        "engineering_headcount_growth",
        "active_job_openings",
        "tech_stack_changes",
        "key_employee_departures"
    ])


class AgentsConfig(BaseModel):
    talent_agent: TalentAgentConfig = Field(default_factory=TalentAgentConfig)
    vendor_agent: VendorAgentConfig = Field(default_factory=VendorAgentConfig)
    vc_agent: VcAgentConfig = Field(default_factory=VcAgentConfig)
    competitor_agent: CompetitorAgentConfig = Field(default_factory=CompetitorAgentConfig)


class StartupBlueprint(BaseModel):
    version: str = "1.0"
    project_metadata: ProjectMetadata
    orchestration: OrchestrationConfig = Field(default_factory=OrchestrationConfig)
    agents: AgentsConfig = Field(default_factory=AgentsConfig)

    def to_yaml(self) -> str:
        """Convert validated model to clean YAML string."""
        return yaml.dump(self.model_dump(), sort_keys=False, default_flow_style=False)

    @classmethod
    def from_yaml(cls, yaml_content: str) -> "StartupBlueprint":
        """Parse and validate YAML into StartupBlueprint."""
        data = yaml.safe_load(yaml_content)
        return cls(**data)

