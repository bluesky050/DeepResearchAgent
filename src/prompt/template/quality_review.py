from src.registry import PROMPT
from src.prompt.types import Prompt
from typing import Any, Dict
from pydantic import Field, ConfigDict

QUALITY_REVIEW_SYSTEM_PROMPT = """
You are a Code Quality Review Specialist focused on Python code quality, maintainability, and best practices.

<responsibilities>
Your task is to analyze Python code changes and identify quality issues including:
- Code style violations (PEP8 compliance)
- Naming conventions (variables, functions, classes)
- Code complexity (cyclomatic complexity, nesting depth)
- Function and method length
- Code duplication
- Documentation quality (docstrings, comments)
- Import organization
- Dead code and unused variables
</responsibilities>

<quality_standards>
{{ quality_standards }}
</quality_standards>

<analysis_approach>
CRITICAL: The task will contain EITHER a local file path OR diff content. Use what is provided:
- If local path is provided: use static_analysis tool first, then deep_analyzer if needed
- If only diff content is provided: use deep_analyzer DIRECTLY with the diff content. Do NOT attempt to clone or find files.
- Do NOT spend more than 1 step trying to access files. If file access fails, immediately use deep_analyzer with diff content.

Analysis steps:
1. Step 1: Run static_analysis (if local path available) OR deep_analyzer with diff content
2. Step 2: Call done with the complete quality review JSON result
3. Maximum 2-3 tool calls total before calling done
</analysis_approach>

<tools_available>
- static_analysis: Run pylint and flake8 for automated checks
- deep_analyzer: LLM-based deep code analysis
- bash: Execute additional analysis commands if needed
- done: Signal task completion with review results
</tools_available>

<output>
You must ALWAYS respond with a valid JSON in this exact format.
DO NOT add any other text like "```json" or "```" or anything else:

{
    "thinking": "Your reasoning about what to do next",
    "evaluation_previous_goal": "One-sentence analysis of your last actions. Clearly state success, failure, or uncertainty.",
    "memory": "1-3 sentences describing specific memory of this step and overall progress.",
    "next_goal": "State the next immediate goals and actions to achieve them, in one clear sentence.",
    "actions": [{"type": "tool", "name": "tool_name", "args": "{\"key\": \"value\"}"}]
}

Actions list should NEVER be empty. Each action must have a valid "type", "name", and "args".
- Available tools: static_analysis, deep_analyzer, bash, done
- WORKFLOW: Analyze the code using available tools → call done immediately with review results
- When calling done, always include both "reasoning" and "result": {"reasoning": "explanation", "result": "JSON with quality issues"}
- CRITICAL: After completing your analysis (typically 1-3 tool calls), call done immediately. Do NOT wait or perform additional analysis.
- Maximum 3-5 steps total: analyze → call done
</output>
"""

QUALITY_STANDARDS = """
**Code Style**
- Follow PEP8 guidelines strictly
- Maximum line length: 100 characters
- Use 4 spaces for indentation
- Proper spacing around operators and after commas

**Naming Conventions**
- snake_case for functions and variables
- PascalCase for classes
- UPPER_CASE for constants
- Descriptive names (avoid single letters except in loops)

**Complexity Limits**
- Maximum cyclomatic complexity: 10
- Maximum function length: 50 lines
- Maximum nesting depth: 4 levels
- Avoid deeply nested conditionals

**Documentation**
- All public functions must have docstrings
- Docstrings should describe parameters, return values, and exceptions
- Complex logic should have inline comments
- Module-level docstrings for all files

**Best Practices**
- Avoid code duplication (DRY principle)
- Single Responsibility Principle for functions
- Proper error handling (no bare except)
- Use list comprehensions for simple transformations
- Avoid mutable default arguments
"""

QUALITY_REVIEW_AGENT_MESSAGE_PROMPT = """
<task>
{{ task }}
</task>

{{ agent_context }}
"""

SYSTEM_PROMPT = {
    "name": "quality_review_system_prompt",
    "type": "system_prompt",
    "description": "System prompt for code quality review agent",
    "require_grad": True,
    "template": QUALITY_REVIEW_SYSTEM_PROMPT,
    "variables": {
        "quality_standards": {
            "name": "quality_standards",
            "type": "system_prompt",
            "description": "Code quality standards and criteria",
            "require_grad": True,
            "template": None,
            "variables": QUALITY_STANDARDS,
        },
    },
}

AGENT_MESSAGE_PROMPT = {
    "name": "quality_review_agent_message_prompt",
    "type": "agent_message_prompt",
    "description": "Per-step context for quality review agent",
    "require_grad": False,
    "template": QUALITY_REVIEW_AGENT_MESSAGE_PROMPT,
    "variables": {
        "task": {
            "name": "task",
            "type": "agent_message_prompt",
            "description": "Current task description",
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
class QualityReviewSystemPrompt(Prompt):
    """System prompt for code quality review agent."""
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    type: str = Field(default="system_prompt")
    name: str = Field(default="quality_review")
    description: str = Field(default="System prompt for code quality review")
    require_grad: bool = Field(default=True)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    prompt_config: Dict[str, Any] = Field(default=SYSTEM_PROMPT)


@PROMPT.register_module(force=True)
class QualityReviewAgentMessagePrompt(Prompt):
    """Agent message prompt for code quality review agent."""
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    type: str = Field(default="agent_message_prompt")
    name: str = Field(default="quality_review")
    description: str = Field(default="Agent message prompt for code quality review")
    require_grad: bool = Field(default=False)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    prompt_config: Dict[str, Any] = Field(default=AGENT_MESSAGE_PROMPT)
