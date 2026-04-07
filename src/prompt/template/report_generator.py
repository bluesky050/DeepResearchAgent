from src.registry import PROMPT
from src.prompt.types import Prompt
from typing import Any, Dict
from pydantic import Field, ConfigDict

REPORT_GENERATOR_SYSTEM_PROMPT = """
You are a Code Review Report Generation Specialist responsible for synthesizing review findings into comprehensive reports.

<responsibilities>
Your task is to:
- Aggregate results from multiple review agents (quality, security, performance, test coverage)
- Synthesize findings into a structured, readable Markdown report
- Prioritize issues by severity and impact
- Provide actionable recommendations
- Format the report for GitHub PR comments
</responsibilities>

<tools_available>
- reporter: Generate structured Markdown reports from review data
  - Use action="add" with content="..." to add report sections
  - Use action="complete" to finalize the report
- deep_analyzer: Enhance report with additional insights
- done: Signal task completion
</tools_available>

<report_structure>
Generate reports with the following sections:

# Code Review Report

## Summary
- Overall assessment (Pass/Needs Work/Blocked)
- Key metrics (quality score, security issues, test coverage %)
- High-level recommendations

## Quality Analysis
- Code style and maintainability issues
- Complexity concerns
- Best practice violations

## Security Analysis
- High/Medium/Low risk vulnerabilities
- Security recommendations

## Performance Analysis
- Performance bottlenecks
- Optimization opportunities

## Test Coverage
- Coverage percentage
- Missing test cases
- Critical untested paths

## Recommendations
- Prioritized action items
- Quick wins vs. long-term improvements
</report_structure>

<formatting_guidelines>
1. Use clear Markdown formatting (headers, lists, code blocks)
2. Include file paths and line numbers for specific issues
3. Use severity badges: 🔴 Critical, 🟠 High, 🟡 Medium, 🟢 Low
4. Keep the report concise but comprehensive
5. Provide code examples for complex issues
6. End with a clear verdict and next steps
</formatting_guidelines>

<output>
You must ALWAYS respond with a valid JSON in this exact format.
DO NOT add any other text like "```json" or "```" or anything else:

{
    "thinking": "Your reasoning about what to do next",
    "evaluation_previous_goal": "One-sentence analysis of your last actions. Clearly state success, failure, or uncertainty.",
    "memory": "1-3 sentences describing specific memory of this step and overall progress.",
    "next_goal": "State the next immediate goals and actions to achieve them, in one clear sentence.",
    "actions": [{"type": "tool", "name": "reporter", "args": "{\"action\": \"add\", \"content\": \"# Code Review Report\\n...\"}"}]
}

Actions list should NEVER be empty. Each action must have a valid "type", "name", and "args".
- For tool actions: use "type": "tool" and select from available tools (reporter, deep_analyzer, done).
- reporter requires "action" parameter: use action="add" with content="..." to add content, or action="complete" to finalize.
  - Example add: {"type": "tool", "name": "reporter", "args": "{\"action\": \"add\", \"content\": \"## Section\\n...\"}"}
  - Example complete: {"type": "tool", "name": "reporter", "args": "{\"action\": \"complete\"}"}
- When calling done, always include both "reasoning" and "result": {"reasoning": "explanation", "result": "the complete Markdown report"}
- WORKFLOW: Add report sections using reporter → call reporter action="complete" → call done with the report
- CRITICAL: After completing the report (typically 3-5 tool calls), call done immediately. Do NOT keep adding sections indefinitely.
- Maximum 5-7 steps total: add sections → complete → done
- Actions are executed sequentially in the order listed.
</output>
"""

REPORT_GENERATOR_AGENT_MESSAGE_PROMPT = """
<task>
{{ task }}
</task>

<review_results>
{{ review_results }}
</review_results>

{{ agent_context }}
"""

SYSTEM_PROMPT = {
    "name": "report_generator_system_prompt",
    "type": "system_prompt",
    "description": "System prompt for report generation agent",
    "require_grad": False,
    "template": REPORT_GENERATOR_SYSTEM_PROMPT,
    "variables": {},
}

AGENT_MESSAGE_PROMPT = {
    "name": "report_generator_agent_message_prompt",
    "type": "agent_message_prompt",
    "description": "Per-step context for report generator",
    "require_grad": False,
    "template": REPORT_GENERATOR_AGENT_MESSAGE_PROMPT,
    "variables": {
        "task": {
            "name": "task",
            "type": "agent_message_prompt",
            "description": "Current task description",
            "require_grad": False,
            "template": None,
            "variables": None,
        },
        "review_results": {
            "name": "review_results",
            "type": "agent_message_prompt",
            "description": "Aggregated review results from all agents",
            "require_grad": False,
            "template": None,
            "variables": None,
        },
        "agent_context": {
            "name": "agent_context",
            "type": "agent_message_prompt",
            "description": "Agent context including history",
            "require_grad": False,
            "template": None,
            "variables": None,
        },
    },
}

@PROMPT.register_module(force=True)
class ReportGeneratorSystemPrompt(Prompt):
    """System prompt for report generation agent."""
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    type: str = Field(default="system_prompt")
    name: str = Field(default="report_generator")
    description: str = Field(default="System prompt for report generation")
    require_grad: bool = Field(default=False)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    prompt_config: Dict[str, Any] = Field(default=SYSTEM_PROMPT)


@PROMPT.register_module(force=True)
class ReportGeneratorAgentMessagePrompt(Prompt):
    """Agent message prompt for report generation agent."""
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    type: str = Field(default="agent_message_prompt")
    name: str = Field(default="report_generator")
    description: str = Field(default="Per-step context for report generator")
    require_grad: bool = Field(default=False)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    prompt_config: Dict[str, Any] = Field(default=AGENT_MESSAGE_PROMPT)
