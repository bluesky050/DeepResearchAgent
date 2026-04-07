"""Code Review Planner Agent — orchestrates the multi-agent PR review workflow."""

from typing import Optional, Dict, Any
from pydantic import Field, ConfigDict

from src.agent.planning_agent import PlanningAgent
from src.registry import AGENT


@AGENT.register_module(force=True)
class CodeReviewPlannerAgent(PlanningAgent):
    """Planning agent that coordinates specialized code review agents.

    Analyzes PR characteristics, dispatches review agents in parallel, and
    synthesizes results into a comprehensive report posted to the PR.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    name: str = Field(
        default="code_review_planner",
        description="The name of the code review planner agent.",
    )
    description: str = Field(
        default=(
            "Coordinates GitHub PR code review by dispatching specialized agents "
            "(quality, security, performance, test coverage) in parallel and synthesizing results."
        ),
        description="Description of the code review planner agent.",
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)
    require_grad: bool = Field(default=True)
