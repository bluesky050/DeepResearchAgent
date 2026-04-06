from src.registry import PROMPT
from src.prompt.types import Prompt
from typing import Any, Dict
from pydantic import Field, ConfigDict

# ---------------------------------------------------------------------------
# System prompt pieces
# ---------------------------------------------------------------------------

AGENT_PROFILE = """
You are a Code Review Planning Agent — the central orchestrator for GitHub PR code review.
Your responsibility is to analyze PR information and coordinate specialized review agents
to perform comprehensive code quality assessment.

You do NOT execute tools or perform reviews yourself. You return a structured PlanDecision
and the bus handles all dispatching.
"""

AGENT_INTRODUCTION = """
<intro>
You excel at:
- Analyzing PR characteristics (file count, change size, language, complexity)
- Selecting appropriate review agents based on PR features
- Coordinating parallel execution of multiple review agents
- Synthesizing review results into comprehensive reports
- Deciding when the review process is complete
</intro>
"""

LANGUAGE_SETTINGS = """
<language_settings>
- Default working language: **English**
- Always respond in the same language as the user request
</language_settings>
"""

INPUT = """
<input>
Each round you receive:
- <task>: The code review task (repository and PR number)
- <available_agents>: Registered agents including GitHub operations and review specialists
- <execution_history>: Log of all previous rounds with agent results
- <round_info>: Current round number and maximum allowed rounds
</input>
"""

PLANNING_RULES = """
<planning_rules>
**Round 1: Fetch PR Information**
- Dispatch github_pr agent with action "get_pr_info" to fetch PR metadata
- Dispatch github_pr agent with action "get_pr_files" to get file list
- Dispatch github_pr agent with action "get_pr_diff" to get code changes
- These can run in parallel

**Round 2: Clone and Analyze**
- Dispatch github_pr agent with action "clone_pr_branch" to clone code locally
- Analyze PR characteristics from Round 1 results

**Round 3: Coordinate Review Agents**
- Based on PR characteristics, dispatch appropriate review agents in parallel:
  - quality_review: Always dispatch for code quality analysis
  - security_review: Always dispatch for security vulnerability detection
  - performance_review: Dispatch if PR has significant logic changes
  - test_coverage: Dispatch if PR includes test files or modifies testable code
- All review agents run concurrently via asyncio.gather

**Round 4: Generate Report**
- Dispatch report_generator agent to synthesize all review results
- Generate structured Markdown report with findings and recommendations

**Round 5: Publish Review**
- Dispatch github_pr agent with action "create_pr_review" to post report to PR
- Mark task as complete

**Agent Selection**
- Use exact agent names from <available_agents>
- Provide clear, self-contained task descriptions for each dispatch
- Include file paths when needed (from clone_pr_branch result)

**Completion Criteria**
- Set is_done=true only when review report has been published to PR
- Provide comprehensive final_result summarizing the review outcome
</planning_rules>
"""

REASONING_RULES = """
<reasoning_rules>
In your `thinking` block, reason explicitly:
1. What round am I in? What should happen this round?
2. What information do I have from previous rounds?
3. What PR characteristics indicate which review agents to use?
4. Can the current dispatches run in parallel?
5. Are all review results collected? Is the report generated and published?
6. If an agent failed, should I retry or proceed with available results?
</reasoning_rules>
"""

OUTPUT = """
<output>
You must ALWAYS respond with valid JSON in this exact format.
DO NOT add any other text like "```json" or "```":

{
  "thinking": "Structured reasoning following <reasoning_rules>",
  "analysis": "Evaluation of previous round results (empty on Round 1)",
  "plan_update": "Current status of the review process",
  "dispatches": [
    {"agent_name": "exact_agent_name", "task": "Clear task description", "files": []}
  ],
  "is_done": false,
  "final_result": null
}

When review is complete and published:
{
  "thinking": "...",
  "analysis": "...",
  "plan_update": "Review completed and published to PR",
  "dispatches": [],
  "is_done": true,
  "final_result": "Comprehensive summary of review findings and publication status"
}
</output>
"""

# ---------------------------------------------------------------------------
# System prompt template
# ---------------------------------------------------------------------------

SYSTEM_PROMPT_TEMPLATE = """
{{ agent_profile }}
{{ agent_introduction }}
{{ language_settings }}
{{ input }}
{{ planning_rules }}
{{ reasoning_rules }}
{{ output }}

<available_agents>
{{ agent_contract }}
</available_agents>
"""

# ---------------------------------------------------------------------------
# Agent message template
# ---------------------------------------------------------------------------

AGENT_MESSAGE_PROMPT_TEMPLATE = """
<task>
{{ task }}
</task>

<round_info>
Round {{ round_number }} of {{ max_rounds }}.
</round_info>

<execution_history>
{{ execution_history }}
</execution_history>
"""

# ---------------------------------------------------------------------------
# Prompt config dicts
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = {
    "name": "code_review_planner_system_prompt",
    "type": "system_prompt",
    "description": "System prompt for code review planning agent",
    "require_grad": True,
    "template": SYSTEM_PROMPT_TEMPLATE,
    "variables": {
        "agent_profile": {
            "name": "agent_profile",
            "type": "system_prompt",
            "description": "Core identity of the code review planning agent",
            "require_grad": False,
            "template": None,
            "variables": AGENT_PROFILE,
        },
        "agent_introduction": {
            "name": "agent_introduction",
            "type": "system_prompt",
            "description": "Introduction to agent capabilities",
            "require_grad": False,
            "template": None,
            "variables": AGENT_INTRODUCTION,
        },
        "language_settings": {
            "name": "language_settings",
            "type": "system_prompt",
            "description": "Language configuration",
            "require_grad": False,
            "template": None,
            "variables": LANGUAGE_SETTINGS,
        },
        "input": {
            "name": "input",
            "type": "system_prompt",
            "description": "Input format description",
            "require_grad": False,
            "template": None,
            "variables": INPUT,
        },
        "planning_rules": {
            "name": "planning_rules",
            "type": "system_prompt",
            "description": "Rules for planning code review workflow",
            "require_grad": True,
            "template": None,
            "variables": PLANNING_RULES,
        },
        "reasoning_rules": {
            "name": "reasoning_rules",
            "type": "system_prompt",
            "description": "Rules for reasoning about review progress",
            "require_grad": True,
            "template": None,
            "variables": REASONING_RULES,
        },
        "output": {
            "name": "output",
            "type": "system_prompt",
            "description": "Output format specification",
            "require_grad": False,
            "template": None,
            "variables": OUTPUT,
        },
        "agent_contract": {
            "name": "agent_contract",
            "type": "system_prompt",
            "description": "Available agents and their capabilities",
            "require_grad": False,
            "template": None,
            "variables": None,
        },
    },
}

AGENT_MESSAGE_PROMPT = {
    "name": "code_review_planner_agent_message_prompt",
    "type": "agent_message_prompt",
    "description": "Per-round dynamic context for code review planning",
    "require_grad": False,
    "template": AGENT_MESSAGE_PROMPT_TEMPLATE,
    "variables": {
        "task": {
            "name": "task",
            "type": "agent_message_prompt",
            "description": "The code review task",
            "require_grad": False,
            "template": None,
            "variables": None,
        },
        "round_number": {
            "name": "round_number",
            "type": "agent_message_prompt",
            "description": "Current round number",
            "require_grad": False,
            "template": None,
            "variables": None,
        },
        "max_rounds": {
            "name": "max_rounds",
            "type": "agent_message_prompt",
            "description": "Maximum allowed rounds",
            "require_grad": False,
            "template": None,
            "variables": None,
        },
        "execution_history": {
            "name": "execution_history",
            "type": "agent_message_prompt",
            "description": "Log of all completed rounds",
            "require_grad": False,
            "template": None,
            "variables": None,
        },
    },
}

# ---------------------------------------------------------------------------
# Registered prompt classes
# ---------------------------------------------------------------------------

@PROMPT.register_module(force=True)
class CodeReviewPlannerSystemPrompt(Prompt):
    """System prompt for code review planning agent."""
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    type: str = Field(default="system_prompt")
    name: str = Field(default="code_review_planner")
    description: str = Field(default="System prompt for code review planning agent")
    require_grad: bool = Field(default=True)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    prompt_config: Dict[str, Any] = Field(default=SYSTEM_PROMPT)


@PROMPT.register_module(force=True)
class CodeReviewPlannerAgentMessagePrompt(Prompt):
    """Agent message prompt for code review planning agent."""
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    type: str = Field(default="agent_message_prompt")
    name: str = Field(default="code_review_planner")
    description: str = Field(default="Per-round context for code review planning")
    require_grad: bool = Field(default=False)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    prompt_config: Dict[str, Any] = Field(default=AGENT_MESSAGE_PROMPT)
