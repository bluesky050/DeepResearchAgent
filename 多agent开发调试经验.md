# 多 Agent 系统开发实战经验总结

## 项目背景
基于 Autogenesis 框架开发多 Agent 协作的 GitHub PR 代码审查系统，包含 7 个专业 Agent（规划者 + 4 个审查专家 + 报告生成 + GitHub 操作），实现并行协作和自进化能力。

---

## 核心技术难点与解决方案

### 1. LLM 指令遵循不可靠问题 ⭐⭐⭐⭐⭐

**问题描述**：
- `github_pr` agent 被分配任务 "fetch PR metadata (get_pr_info)"
- 执行完 `get_pr_info` 后不调用 `done`，反而继续调用 `get_pr_files`、`get_pr_diff`
- 在 15 步内循环执行，从未完成任务
- Prompt 里明确写了 "STRICT 2-STEP WORKFLOW — NO EXCEPTIONS"、"IMMEDIATELY call done"，但模型完全忽略

**根本原因**：
- 使用免费模型（`gemini-2.0-flash-exp:free`）时，指令遵循能力差
- Agent 的 `agent_history` 包含整体任务上下文（"审查 PR，生成完整报告"）
- LLM 理解了"整体目标是 code review，需要所有 PR 数据"，于是主动越权多做事
- **Prompt 指令只是建议，不是强制约束**

**解决方案**：
1. **代码层面强制控制**：
   - 不能依赖 LLM 遵守 "执行一次就停止" 的约束
   - 在框架层面添加调用计数器、强制注入消息、或直接路由

2. **任务上下文隔离**：
   - 子 agent 的任务描述要完全屏蔽上层目标
   - 只告诉它 "做什么"，不告诉 "为什么做"
   - 遵循最小知识原则（类比软件设计）

3. **模型选择**：
   - 免费模型适合 RAG、文本摘要等容错性强的任务
   - Agent 任务需要严格格式遵守和精确行为控制，必须用高质量模型
   - 用廉价模型调试会把架构问题和模型问题混在一起，极难排查

**面试金句**：
> "Agent 的行为边界不能只靠 prompt 来约束。在生产级系统中，关键的流程控制必须在代码层面强制，而不能依赖 LLM 去遵守。Prompt 是建议，代码是保证。"

---

### 2. Agent 间数据传递的截断陷阱 ⭐⭐⭐⭐⭐

**问题描述**：
- `github_pr` agent 获取 PR diff 后，planner 收到的 `execution_history` 里只有摘要：
  ```
  "Generated diff for 1 files (total 1031 characters)"
  ```
- 实际 diff 内容（1031 字符）不见了
- Review agents 因为没有 diff 内容，无法完成代码审查

**根本原因**：
- `bus.py` 在构建 `execution_history` 时，对每个 agent 的结果做了 `result_text[:300]` 截断
- Diff 内容通常远超 300 字符，被截掉了
- 上下游 Agent 数据依赖图在设计阶段没有考虑数据量

**解决方案**：
1. **数据大小是一等公民**：
   - 代码 diff、文件内容这类大型数据，不能和普通结构化信息走同一条"摘要通道"

2. **专门设计数据传递机制**：
   - 外存文件传递：写到文件，传路径
   - 对特定字段跳过截断（在 `bus.py` 中特殊处理 `diff` 字段）

3. **在 Planner prompt 中明确指示**：
   - 如果 clone 失败，从 Round 1 的 `execution_history` 中提取 `extra.data.diff`
   - 把完整 diff 内容粘贴到 Round 2 的任务描述中

**面试金句**：
> "在多 Agent 系统设计中，数据大小是一等公民。上下游 Agent 的数据依赖图必须在设计阶段就考虑数据量，不能简单地把所有历史信息序列化成一个字符串。"

---

### 3. Prompt 缓存/版本管理的隐蔽陷阱 ⭐⭐⭐⭐

**问题描述**：
- 修改了 `src/prompt/template/github_pr.py` 的内容
- 运行时 agent 仍然使用旧 prompt
- 日志显示 `github_pr_system_prompt@1.0.0`，版本号没有变化

**根本原因**：
- 框架的 prompt 版本管理系统：**只有代码版本严格大于缓存版本时，才会覆盖缓存**
- 两边都是 `1.0.0`，所以缓存（`workdir/prompt/prompt.json`）永远被优先使用
- 代码里的修改根本没有生效

**解决方案**：
1. **修改代码后同步更新版本号**：
   ```python
   version = "1.0.1"  # 每次修改 prompt 都要递增
   ```

2. **开发阶段快捷机制**：
   - 清空缓存：`rmdir /s /q workdir\code_review_bus`
   - 或者添加 `--force-reload-prompts` 参数

3. **CI/CD 中自动化**：
   - Git commit hash 作为版本号
   - 或者文件内容 hash

**面试金句**：
> "任何有'代码版本 vs 持久化版本'设计的系统，修改代码后必须同步更新版本号。这个坑可能花掉几个小时才意识到，是典型的'改了没生效'问题。"

---

### 4. Agent 失败时的模糊错误信息陷阱 ⭐⭐⭐⭐

**问题描述**：
- `github_pr` agent 达到 `max_steps` 后，返回通用信息：
  ```
  "The task has not been completed."
  ```
- 没有任何中间状态信息（已执行了哪些步骤、工具返回了什么、失败在哪一步）
- Planner 在 Round 3 直接判断 "github_pr 不可用"，跳过所有 PR 数据
- 生成了一份 "无法进行审查" 的空报告，整个 6 轮流程变成无效执行

**解决方案**：
1. **Agent 的 max_steps fallback 应该返回**：
   - 最后成功执行的工具结果
   - 或者至少携带 "已执行步骤数、最后动作、中间结果"

2. **优雅降级（Graceful Degradation）**：
   - 好的系统失败时应该 "优雅降级"，而不是 "全部丢弃"
   - 例如：部分审查结果 > 完全没有审查

3. **Planner 的容错设计**：
   - 检查每个 agent 的返回，区分 "完全失败" vs "部分成功"
   - 根据可用数据调整后续策略

**面试金句**：
> "系统失败时的错误信息设计和正常流程一样重要。优雅降级意味着即使部分组件失败，系统仍能提供有价值的输出。"

---

### 5. 多 Agent 系统的可观测性设计 ⭐⭐⭐⭐⭐

**问题描述**：
- "github_pr agent 不调用 done" 这一个现象，背后同时有：
  - LLM 指令遵循问题
  - Prompt 缓存未更新
  - 任务设计导致 agent 越权
  - 三个原因叠加，排查极为困难

**解决方案**：
1. **结构化日志（每步必须记录）**：
   - 收到的任务
   - LLM 生成的 ThinkOutput JSON
   - 执行的工具及其结果
   - 最终 done 时的 result

2. **分层日志**：
   - Bus 层：dispatch、gather、round 切换
   - Agent 层：thinking、actions、tool results
   - Tool 层：输入参数、API 调用、返回值

3. **可视化工具**：
   - Agent 调用链路图
   - 时间线视图（哪些 agent 并行执行）
   - 数据流图（哪些数据在 agent 间传递）

**面试金句**：
> "在多 Agent 系统中，'可观测性（Observability）'比单体系统更重要。没有结构化日志，调试等于盲人摸象。"

---

### 6. 跨平台开发的环境陷阱 ⭐⭐⭐

**Windows 特有问题**：

1. **Python 路径问题**：
   - Windows 上 `python` 命令可能指向 Microsoft Store 应用存根
   - 运行后返回 exit code 49（打开 Store 页面）而不是执行 Python
   - 必须使用完整虚拟环境路径：`venv\Scripts\python.exe`

2. **Emoji 编码问题**：
   - Rich 日志库使用 emoji 字符（🔄、✅、📄）
   - Windows 默认 GBK 编码环境下，这些字符无法编码
   - 导致 `UnicodeEncodeError: 'gbk' codec can't encode character`
   - 解决：设置 `PYTHONUTF8=1` 或 `PYTHONIOENCODING=utf-8`

3. **命令行差异**：
   - Windows 不支持 `\` 换行，命令必须写成一行
   - `rm -rf` → `rmdir /s /q`
   - 路径分隔符：`/` vs `\`

4. **.env 文件格式问题**：
   - 变量名前有多余空格（`  GITHUB_TOKEN=xxx`）导致 dotenv 无法解析
   - 始终检查 .env 文件是否有 leading whitespace

**面试金句**：
> "跨平台开发时，字符编码和命令路径是两个基础但易被忽视的陷阱。应该在 CI/CD 环境中显式设置环境变量。"

---

### 7. E2E 测试策略的成本陷阱 ⭐⭐⭐⭐

**问题描述**：
- 每次修复后直接运行完整的 6-round E2E 测试
- 单次运行生成 9MB+ 日志、消耗大量 LLM API tokens
- 每次运行需要等待几分钟
- 多次无效测试后，浪费了大量 token 仍然没有解决问题

**正确的调试策略（由内到外）**：
1. **单元测试**：Mock 掉 LLM，只测框架逻辑，验证每个 Agent 的独立行为
2. **局部集成测试**：验证两个 Agent 之间的数据流，例如 Planner → github_pr 的 dispatch
3. **E2E 测试**：只有在局部验证通过后才跑，使用小 PR（变更少、速度快）

**日志分析技巧**：
```bash
# 不要读整个日志，grep 关键词
grep "Round" code_review.log
grep "ERROR" code_review.log
grep "done" code_review.log
```

**面试金句**：
> "多 Agent 系统的 E2E 测试成本极高。正确的策略是：单元测试 → 局部集成测试 → E2E 测试。学会从大型日志文件中快速定位关键信息。"

---

### 8. 模型 API 兼容性问题 ⭐⭐⭐⭐

**问题描述**：
- 使用 `response_format` 参数进行结构化输出
- 免费模型报错：`This response_format type is unavailable now`
- 即使是 DeepSeek 这样的付费模型，检测逻辑本身也会触发 400 错误

**解决方案**：
1. **能力检测机制**：
   ```python
   async def _check_response_format_support(self) -> bool:
       try:
           test_resp = await model_manager(
               model=self.model_name,
               messages=[{"role": "user", "content": "test"}],
               response_format=ThinkOutput
           )
           return test_resp.success
       except:
           return False
   ```

2. **降级策略**：
   - 不支持 `response_format` 时，走 JSON 手动解析
   - 用正则表达式提取 JSON：
     ```python
     match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', text)
     ```

3. **强制禁用（临时方案）**：
   - 开发阶段直接返回 `False`，避免检测本身触发错误

**面试金句**：
> "在 Agent 系统中，模型能力检测和降级策略是必需的。不同模型的 API 兼容性差异很大，必须有 fallback 机制。"

---

### 9. 并行执行的设计与实现 ⭐⭐⭐⭐

**架构设计**：
```python
# Round 2: Planner 在同一个 dispatches 列表里写多个 agent
dispatches = [
    {"agent_name": "quality_review", "task": "..."},
    {"agent_name": "security_review", "task": "..."},
    {"agent_name": "performance_review", "task": "..."},
    {"agent_name": "test_coverage", "task": "..."},
]

# Bus 使用 asyncio.gather 并行执行
raw_responses = await asyncio.gather(
    *[self._call_agent(m.recipients[0], m, ctx=ctx) for m in sub_messages]
)
```

**关键点**：
- 并行是在**同一轮 dispatch 里的**
- 如果 planner 把 agents 分散到不同 round，就是串行的
- 取决于 planner 的决策逻辑，不是自动的

**性能提升**：
- 4 个审查 agent 并行执行，延迟减少约 70%

**面试金句**：
> "多 Agent 系统的并行执行不是自动的，取决于 Planner 的调度策略。使用 asyncio.gather 实现真正的并发，关键在于 Planner 在同一轮 dispatch 中返回多个 agent。"

---

### 10. 免费/廉价 LLM 在 Agentic 任务中的适用性 ⭐⭐⭐

**实验结果**：

| 模型 | 指令遵循 | 结构化输出 | 成本 | 适用场景 |
|------|---------|-----------|------|---------|
| gemini-2.0-flash-exp:free | 差 | 不支持 | 免费 | RAG、文本摘要 |
| deepseek-chat | 好 | 部分支持 | 低 | Agent 开发调试 |
| gpt-4o | 优秀 | 完全支持 | 高 | 生产环境 |
| claude-3.5-sonnet | 优秀 | 完全支持 | 中 | 平衡选择 |

**教训**：
- 免费模型适合做容错性强的任务
- Agent 任务需要严格格式遵守和精确行为控制
- 用廉价模型调试 Agent 行为问题，会把架构问题和模型问题混在一起

**面试金句**：
> "在开发 Agent 系统时，应该用高质量模型来验证架构设计的正确性，再考虑降低成本。用廉价模型调试会浪费更多时间。"

---

## 项目亮点总结（简历/面试用）

### 技术架构
- **7 个专业 Agent 协同工作**：规划者 + 4 个审查专家 + 报告生成 + GitHub 操作
- **AgentBus 消息路由**：Session 隔离、多轮规划、并行调度
- **LLM 驱动的动态调度**：PlannerAgent 根据 PR 特征决定调用哪些审查 Agent

### 工程化设计
- **并行执行**：4 个审查 Agent 通过 asyncio.gather 并发，延迟减少 70%
- **鲁棒性设计**：Clone 失败自动降级到 diff 分析，工具不可用时 fallback 到 LLM 分析
- **可观测性**：结构化日志、Agent 调用链路追踪
- **自进化能力**：ReflectionOptimizer 根据历史反馈持续改进审查规则

### 性能指标
- **执行时间**：典型 PR 审查 ~1-2 分钟
- **API 成本**：使用 DeepSeek，单次审查 $0.01-0.05
- **审查维度**：50+ 质量/安全/性能/测试覆盖标准

### 核心能力
- 多 Agent 系统架构设计
- LLM 应用工程化（prompt 工程、模型选择、成本优化）
- 异步编程和并发控制（asyncio）
- 复杂系统调试和问题定位
- 跨平台开发和环境适配

---

## 一句话总结各问题

| # | 问题 | 核心教训 |
|---|------|---------|
| 1 | LLM 不遵守指令 | Prompt 是建议，代码层面才是保证 |
| 2 | 数据传递被截断 | 数据大小是一等公民，大对象要专门设计传递机制 |
| 3 | Prompt 缓存未更新 | 修改 prompt 后必须更新版本号或清缓存 |
| 4 | 失败信息不透明 | max_steps fallback 要携带中间结果，而非通用错误 |
| 5 | 调试困难 | 可观测性比单体系统更重要，结构化日志是必需品 |
| 6 | 跨平台环境问题 | 编码和路径是基础但易忽视的陷阱 |
| 7 | E2E 测试成本高 | 分层测试：单元 → 集成 → E2E |
| 8 | API 兼容性差异 | 模型能力检测 + 降级策略是必需的 |
| 9 | 并行不是自动的 | 并行取决于 Planner 同一轮 dispatch 多少个 agent |
| 10 | 廉价模型调试困难 | 先用好模型验证架构，再降成本 |
