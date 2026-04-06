test_coverage_agent = dict(
    workdir="workdir/code_review/test_coverage",
    name="test_coverage",
    type="ToolCallingAgent",
    description="Test coverage review specialist analyzing test completeness, missing test cases, edge cases, and test quality",
    model_name="openrouter/gemini-2.0-flash-exp:free",
    prompt_name="test_coverage",
    memory_name="general_memory_system",
    max_tools=10,
    max_steps=20,
    review_steps=5,
    log_max_length=1000,
    require_grad=True,
)
