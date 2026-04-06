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

use_local_proxy = True
version = "1.0.0"
model_name = "openrouter/gemini-2.0-flash-exp:free"

# Agents on the bus: planner + specialized review agents
agent_names = [
    "code_review_planner",  # Planning agent (coordinator)
    "github_pr",            # GitHub operations
    "quality_review",       # Code quality analysis
    "security_review",      # Security vulnerability detection
    "performance_review",   # Performance analysis
    "test_coverage",        # Test coverage analysis
    "report_generator",     # Report generation
]

# Tools available to sub-agents
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
    require_grad=True,  # Enable optimization for planner
)

github_pr_agent.update(
    workdir=f"{workdir}/agent/github_pr",
    model_name=model_name,
    memory_name=memory_names[0],
    require_grad=False,
)

quality_review_agent.update(
    workdir=f"{workdir}/agent/quality_review",
    model_name=model_name,
    memory_name=memory_names[0],
    require_grad=True,  # Enable optimization
)

security_review_agent.update(
    workdir=f"{workdir}/agent/security_review",
    model_name=model_name,
    memory_name=memory_names[0],
    require_grad=True,  # Enable optimization
)

performance_review_agent.update(
    workdir=f"{workdir}/agent/performance_review",
    model_name=model_name,
    memory_name=memory_names[0],
    require_grad=True,  # Enable optimization
)

test_coverage_agent.update(
    workdir=f"{workdir}/agent/test_coverage",
    model_name=model_name,
    memory_name=memory_names[0],
    require_grad=True,  # Enable optimization
)

report_generator_agent.update(
    workdir=f"{workdir}/agent/report_generator",
    model_name=model_name,
    memory_name=memory_names[0],
    require_grad=False,
)
