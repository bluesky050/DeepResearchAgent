quality_review_agent = dict(
    workdir="workdir/code_review/quality_review",
    name="quality_review",
    type="ToolCallingAgent",
    description="Code quality review specialist analyzing code style, complexity, maintainability, and best practices",
    model_name="openrouter/gemini-2.0-flash-exp:free",
    prompt_name="quality_review",
    memory_name="general_memory_system",
    max_tools=10,
    max_steps=20,
    review_steps=5,
    log_max_length=1000,
    require_grad=True,
)
