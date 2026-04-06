code_review_planner_agent = dict(
    workdir="workdir/code_review/planner",
    name="code_review_planner",
    type="PlanningAgent",
    description="Code review planning agent that coordinates specialized review agents for GitHub PR analysis",
    model_name="openrouter/gemini-2.0-flash-exp:free",
    prompt_name="code_review_planner",
    memory_name="general_memory_system",
    max_tools=10,
    max_steps=50,
    review_steps=5,
    log_max_length=1000,
    require_grad=True,
)
