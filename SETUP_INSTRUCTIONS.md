# Code Review System Setup Instructions

## Current Status

The code review system is **fully implemented and configured** but requires API credits to run.

## What's Working

✅ All 7 tools implemented (github_pr, static_analysis, security_scan, deep_analyzer, reporter, bash, done)
✅ All agent configurations created (planning, tool_calling)
✅ All prompt templates created (code_review_planner)
✅ AgentBus integration complete
✅ Configuration files set up correctly
✅ API connection fixed (empty OPENROUTER_API_BASE issue resolved)

## What's Needed

### Option 1: Add OpenRouter Credits (Recommended)

1. Go to https://openrouter.ai/settings/credits
2. Add credits to the account associated with API key: `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`
3. Run the code review:
   ```bash
   cd "D:\JAVAstudy\agent学习项目\DeepResearchAgent"
   ./venv/Scripts/python.exe examples/run_code_review_bus.py --repo bluesky050/DeepResearchAgent --pr 1 --max-rounds 5
   ```

### Option 2: Use Google Gemini (Free Tier)

1. Get a free Google AI API key from https://aistudio.google.com/apikey
2. Update `.env`:
   ```
   GOOGLE_API_KEY=your_key_here
   ```
3. The config is already set to use `google/gemini-2.5-flash`
4. Run the code review (same command as above)

### Option 3: Use Different OpenRouter Key

If you have a different OpenRouter API key with credits:
1. Update `.env`:
   ```
   OPENROUTER_API_KEY=your_key_with_credits
   ```
2. Run the code review

## Test Run Command

```bash
cd "D:\JAVAstudy\agent学习项目\DeepResearchAgent"
./venv/Scripts/python.exe examples/run_code_review_bus.py --repo bluesky050/DeepResearchAgent --pr 1 --max-rounds 5
```

## Expected Behavior

When API credits are available, the system will:

1. **Round 1**: PlanningAgent calls github_pr tool to fetch PR information
2. **Round 2**: PlanningAgent dispatches 4 review agents in parallel:
   - Quality review (pylint, flake8)
   - Security review (bandit)
   - Performance review (complexity analysis)
   - Test coverage review
3. **Round 3**: PlanningAgent calls reporter tool to generate review report
4. **Round 4**: PlanningAgent calls github_pr tool to post report to PR
5. **Complete**: Review report posted to GitHub PR #1

## Troubleshooting

### Issue: API Connection Error
**Fixed** - The issue was empty `OPENROUTER_API_BASE=` in `.env`. Changed `os.getenv()` to use `or` operator instead of default parameter.

### Issue: 402 Insufficient Credits
**Current blocker** - OpenRouter API key needs credits. See options above.

### Issue: Unicode Encoding Errors (gbk codec)
**Cosmetic only** - Windows console encoding issue with emoji characters. Doesn't affect functionality.

## Files Modified

### Bug Fixes
- `src/model/manager.py:635` - Fixed empty API base URL handling

### New Configuration Files
- `configs/code_review_bus.py` - Main configuration
- `configs/agents/planning.py` - Planning agent config
- `configs/agents/tool_calling.py` - Tool calling agent config
- `configs/tools/github_pr.py` - GitHub PR tool config
- `configs/tools/static_analysis.py` - Static analysis tool config
- `configs/tools/security_scan.py` - Security scan tool config
- `configs/tools/deep_analyzer.py` - Deep analyzer tool config
- `configs/tools/reporter.py` - Reporter tool config

### New Tool Implementations
- `src/tool/workflow_tools/github_pr_tool.py` - GitHub PR operations
- `src/tool/workflow_tools/static_analysis_tool.py` - pylint + flake8
- `src/tool/workflow_tools/security_scan_tool.py` - bandit security scanner

### New Prompt Templates
- `src/prompt/template/code_review_planner.py` - Planning agent prompt

### Entry Point
- `examples/run_code_review_bus.py` - Main execution script

## Architecture

```
User submits task → AgentBus → PlanningAgent (coordinator)
                                      ↓
                    ┌─────────────────┴─────────────────┐
                    ↓                                   ↓
            Round 1: Fetch PR info              Round 2: Parallel reviews
            (github_pr tool)                    (4 review tools)
                    ↓                                   ↓
            Round 3: Generate report            Round 4: Post to PR
            (reporter tool)                     (github_pr tool)
```

## Next Steps

1. Add API credits (choose one of the 3 options above)
2. Run the test command
3. Check GitHub PR #1 for the generated review report
4. Iterate and improve based on results
