from mmengine.config import read_base
with read_base():
    from .base import memory_config, window_size, max_tokens
    from .agents.code_review_planner import code_review_planner_agent
    from .agents.github_pr import github_pr_agent
    from .agents.quality_review import quality_review_agent
    from .agents.security_review import security_review_agent
    from .agents.performance_review import performance_review_agent
    from .agents.test_coverage import test_coverage_agent
    from .agents.report_generator import report_generator_agent
    from .tools.github_pr import github_pr_tool
    from .tools.static_analysis import static_analysis_tool
    from .tools.security_scan import security_scan_tool
    from .tools.deep_analyzer import deep_analyzer_tool
    from .tools.reporter import reporter_tool
    from .tools.bash import bash_tool
    from .environments.file_system import environment as file_system_environment
    from .memory.general_memory_system import memory_system as general_memory_system

tag = "code_review_bus"
workdir = f"workdir/{tag}"
log_path = "code_review.log"

use_local_proxy = False
version = "1.0.0"
model_name = "deepseek/deepseek-chat"

# Planner orchestrates; 6 specialized agents run in parallel via AgentBus
agent_names = [
    "code_review_planner",  # PlanningAgent: orchestrates all rounds
    "github_pr",            # Fetches PR info, clones repo, publishes review
    "quality_review",       # Analyzes code style, complexity, best practices
    "security_review",      # Detects security vulnerabilities
    "performance_review",   # Analyzes performance issues
    "test_coverage",        # Checks test coverage
    "report_generator",     # Synthesizes findings into structured report
]

# Tools shared across all sub-agents
tool_names = [
    "github_pr",
    "static_analysis",
    "security_scan",
    "deep_analyzer",
    "reporter",
    "bash",
    "done",
]

env_names = [
    "file_system",
]

memory_names = [
    "general_memory_system",
]

# -----------------TOOL CONFIG-----------------
github_pr_tool.update(require_grad=False)
static_analysis_tool.update(require_grad=False, timeout=120)
security_scan_tool.update(require_grad=False, timeout=120)
deep_analyzer_tool.update(
    model_name=model_name,
    base_dir="tool/deep_analyzer",
    require_grad=False
)
reporter_tool.update(
    model_name=model_name,
    base_dir="tool/reporter",
    require_grad=False
)
bash_tool.update(require_grad=False)

# -----------------MEMORY CONFIG-----------------
general_memory_system.update(
    base_dir="memory/general_memory_system",
    model_name=model_name,
    max_summaries=10,
    max_insights=10,
    require_grad=False,
)

# -----------------ENVIRONMENT CONFIG-----------------
file_system_environment.update(
    base_dir="environment/file_system",
    require_grad=False
)

# -----------------AGENT CONFIG-----------------
code_review_planner_agent.update(
    workdir=f"{workdir}/agent/code_review_planner",
    model_name=model_name,
    memory_name=memory_names[0],
    require_grad=True,
)

github_pr_agent.update(
    workdir=f"{workdir}/agent/github_pr",
    model_name=model_name,
    memory_name=memory_names[0],
    max_steps=10,  # Simple operations, fewer steps needed
    require_grad=False,
)

quality_review_agent.update(
    workdir=f"{workdir}/agent/quality_review",
    model_name=model_name,
    memory_name=memory_names[0],
    max_steps=15,
    require_grad=True,
)

security_review_agent.update(
    workdir=f"{workdir}/agent/security_review",
    model_name=model_name,
    memory_name=memory_names[0],
    max_steps=15,
    require_grad=True,
)

performance_review_agent.update(
    workdir=f"{workdir}/agent/performance_review",
    model_name=model_name,
    memory_name=memory_names[0],
    max_steps=15,
    require_grad=True,
)

test_coverage_agent.update(
    workdir=f"{workdir}/agent/test_coverage",
    model_name=model_name,
    memory_name=memory_names[0],
    max_steps=15,
    require_grad=True,
)

report_generator_agent.update(
    workdir=f"{workdir}/agent/report_generator",
    model_name=model_name,
    memory_name=memory_names[0],
    max_steps=10,
    require_grad=False,
)
