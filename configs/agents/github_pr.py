github_pr_agent = dict(
    workdir="workdir/code_review/github_pr",
    name="github_pr",
    type="ToolCallingAgent",
    description="GitHub PR operations agent for fetching PR info, files, diffs, cloning branches, and posting reviews",
    model_name="openrouter/gemini-2.0-flash-exp:free",
    prompt_name="tool_calling",
    memory_name="general_memory_system",
    max_tools=5,
    max_steps=10,
    review_steps=3,
    log_max_length=1000,
    require_grad=False,
)
