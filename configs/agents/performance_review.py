performance_review_agent = dict(
    workdir="workdir/code_review/performance_review",
    name="performance_review",
    type="ToolCallingAgent",
    description="Performance review specialist analyzing algorithm complexity, inefficient loops, memory usage, and optimization opportunities",
    model_name="openrouter/gemini-2.0-flash-exp:free",
    prompt_name="performance_review",
    memory_name="general_memory_system",
    max_tools=10,
    max_steps=20,
    review_steps=5,
    log_max_length=1000,
    require_grad=True,
)
