"""Specialized code review agents for GitHub PR analysis."""

from typing import Optional, Dict, Any
from pydantic import Field, ConfigDict

from src.agent.tool_calling_agent import ToolCallingAgent
from src.registry import AGENT


@AGENT.register_module(force=True)
class GithubPRAgent(ToolCallingAgent):
    """Agent specialized in GitHub PR operations."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    name: str = Field(default="github_pr")
    description: str = Field(
        default="Fetches PR info, files, diffs, clones branches, and posts reviews to GitHub PRs"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)
    require_grad: bool = Field(default=False)


@AGENT.register_module(force=True)
class QualityReviewAgent(ToolCallingAgent):
    """Agent specialized in code quality analysis."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    name: str = Field(default="quality_review")
    description: str = Field(
        default="Analyzes code style, complexity, maintainability, and best practices using static analysis and LLM review"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)
    require_grad: bool = Field(default=True)


@AGENT.register_module(force=True)
class SecurityReviewAgent(ToolCallingAgent):
    """Agent specialized in security vulnerability detection."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    name: str = Field(default="security_review")
    description: str = Field(
        default="Detects security vulnerabilities, injection risks, and unsafe practices using bandit and LLM analysis"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)
    require_grad: bool = Field(default=True)


@AGENT.register_module(force=True)
class PerformanceReviewAgent(ToolCallingAgent):
    """Agent specialized in performance analysis."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    name: str = Field(default="performance_review")
    description: str = Field(
        default="Analyzes algorithm complexity, memory usage, and performance bottlenecks"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)
    require_grad: bool = Field(default=True)


@AGENT.register_module(force=True)
class TestCoverageAgent(ToolCallingAgent):
    """Agent specialized in test coverage analysis."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    name: str = Field(default="test_coverage")
    description: str = Field(
        default="Checks test coverage, identifies missing tests, and validates test quality"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)
    require_grad: bool = Field(default=True)


@AGENT.register_module(force=True)
class ReportGeneratorAgent(ToolCallingAgent):
    """Agent specialized in synthesizing review results into reports."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    name: str = Field(default="report_generator")
    description: str = Field(
        default="Synthesizes all review findings into a comprehensive Markdown report for GitHub PR"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)
    require_grad: bool = Field(default=False)
