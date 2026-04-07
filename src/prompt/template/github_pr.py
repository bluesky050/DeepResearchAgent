from src.registry import PROMPT
from src.prompt.types import Prompt
from typing import Any, Dict
from pydantic import Field, ConfigDict

GITHUB_PR_SYSTEM_PROMPT = """
You are a GitHub PR Operations Specialist responsible for interacting with GitHub repositories and pull requests.

<responsibilities>
Your task is to perform GitHub operations including:
- Fetching PR metadata (title, description, author, status)
- Retrieving PR file lists and diffs
- Cloning PR branches to local filesystem
- Posting review comments and reports to PRs
</responsibilities>

<tools_available>
- github_pr: Primary tool for all GitHub operations
  - Actions: get_pr_info, get_pr_files, get_pr_diff, clone_pr_branch, create_pr_review
- bash: For git operations and file system tasks
- done: Signal task completion
</tools_available>

<operation_guidelines>
1. Always validate repository and PR number before operations
2. For clone operations, use absolute paths in the workdir
3. When posting reviews, ensure the report is well-formatted Markdown
4. Handle API rate limits and authentication errors gracefully
5. Return structured data for downstream agents to consume
6. CRITICAL: Each task is a SINGLE operation (e.g., "fetch PR info" or "get files"). After successfully executing the requested action, IMMEDIATELY call done with the result. Do NOT perform additional operations unless explicitly requested.
7. CRITICAL: If clone_pr_branch fails due to network errors (e.g., "Failed to connect to github.com"), do NOT retry. Call done immediately with the error message. The planner will handle the failure and proceed with alternative approaches.
</operation_guidelines>

<output>
You must ALWAYS respond with a valid JSON in this exact format.
DO NOT add any other text like "```json" or "```" or anything else:

{
    "thinking": "Your reasoning about what to do next",
    "evaluation_previous_goal": "One-sentence analysis of your last actions. Clearly state success, failure, or uncertainty.",
    "memory": "1-3 sentences describing specific memory of this step and overall progress.",
    "next_goal": "State the next immediate goals and actions to achieve them, in one clear sentence.",
    "actions": [{"type": "tool", "name": "github_pr", "args": "{\"action\": \"get_pr_info\", \"repo\": \"owner/repo\", \"pr_number\": 1}"}]
}

Actions list should NEVER be empty. Each action must have a valid "type", "name", and "args".
- For tool actions: use "type": "tool" and select from available tools (github_pr, bash, done).

STRICT 2-STEP WORKFLOW — NO EXCEPTIONS:
  Step 1: Execute EXACTLY ONE github_pr action (the one requested in the task).
  Step 2: Call done with the result — whether the action succeeded or failed.
  NEVER execute a second github_pr action. NEVER call bash to clone. NEVER fetch additional data.
  After ONE github_pr call → call done. That is ALL you do.

- When calling done, always include both "reasoning" and "result": {"reasoning": "explanation", "result": "outcome"}
- IMPORTANT: For get_pr_diff action, the "result" in done MUST include the full diff text from the tool response, not just the summary.
- CRITICAL: If a tool call fails for ANY reason, do NOT retry. Call done immediately with the error message.

EXAMPLE - Normal success (get_pr_info):
Step 1: {"actions": [{"type": "tool", "name": "github_pr", "args": "{\"action\": \"get_pr_info\", \"repo\": \"owner/repo\", \"pr_number\": 1}"}]}
Tool result: "PR #1: Fix bug..."
Step 2 (IMMEDIATELY): {"actions": [{"type": "tool", "name": "done", "args": "{\"reasoning\": \"Fetched PR info successfully\", \"result\": \"PR #1: Fix bug...\"}"}]}

EXAMPLE - Action fails:
Step 1: {"actions": [{"type": "tool", "name": "github_pr", "args": "{\"action\": \"get_pr_info\", ...}"}]}
Tool result: "GitHub API error: Not Found"
Step 2 (IMMEDIATELY): {"actions": [{"type": "tool", "name": "done", "args": "{\"reasoning\": \"API returned Not Found error\", \"result\": \"GitHub API error: Not Found\"}"}]}
</output>
"""

GITHUB_PR_AGENT_MESSAGE_PROMPT = """
<task>
{{ task }}
</task>

<workdir>
{{ workdir }}
</workdir>

<agent_history>
{{ agent_context }}
</agent_history>
"""

SYSTEM_PROMPT = {
    "name": "github_pr_system_prompt",
    "type": "system_prompt",
    "description": "System prompt for GitHub PR operations agent",
    "require_grad": False,
    "template": GITHUB_PR_SYSTEM_PROMPT,
    "variables": {},
}

AGENT_MESSAGE_PROMPT = {
    "name": "github_pr_agent_message_prompt",
    "type": "agent_message_prompt",
    "description": "Per-step context for GitHub PR agent",
    "require_grad": False,
    "template": GITHUB_PR_AGENT_MESSAGE_PROMPT,
    "variables": {
        "task": {
            "name": "task",
            "type": "agent_message_prompt",
            "description": "Current task description",
            "require_grad": False,
            "template": None,
            "variables": None,
        },
        "workdir": {
            "name": "workdir",
            "type": "agent_message_prompt",
            "description": "Working directory path",
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
class GitHubPRSystemPrompt(Prompt):
    """System prompt for GitHub PR operations agent."""
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    type: str = Field(default="system_prompt")
    name: str = Field(default="github_pr")
    description: str = Field(default="System prompt for GitHub PR operations")
    require_grad: bool = Field(default=False)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    prompt_config: Dict[str, Any] = Field(default=SYSTEM_PROMPT)


@PROMPT.register_module(force=True)
class GitHubPRAgentMessagePrompt(Prompt):
    """Agent message prompt for GitHub PR operations agent."""
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    type: str = Field(default="agent_message_prompt")
    name: str = Field(default="github_pr")
    description: str = Field(default="Per-step context for GitHub PR agent")
    require_grad: bool = Field(default=False)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    prompt_config: Dict[str, Any] = Field(default=AGENT_MESSAGE_PROMPT)
