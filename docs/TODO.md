# DeerFlow Lite TODO

这份文件只做一件事：

> 维护当前阶段可直接执行的任务清单。

如果需要看阶段原因、优先级来源、长期演进顺序，请看 `docs/LITE_EVOLUTION_PLAN.md`。

如果需要看模块职责、目录边界、未来目标结构，请看 `docs/LITE_ARCHITECTURE.md`。

## 使用规则

- `[ ]` 未完成，属于当前或近期应做任务
- `[x]` 已完成，可以保留在本文件中作为最近完成记录
- `[-]` 明确暂缓，不属于当前阶段主线

每个任务都应尽量包含：

1. 目标
2. 关联文件
3. 完成标准

后续 AI 更新本文件时，按这几个规则处理：

1. 完成代码后，优先回写本文件中的 checkbox 状态
2. 如果实际改动文件与 TODO 中列出的文件不同，要同步修正“关联文件”
3. 如果改动改变了阶段顺序，更新 `docs/LITE_EVOLUTION_PLAN.md`
4. 如果改动改变了模块边界，更新 `docs/LITE_ARCHITECTURE.md`

## 当前北极星闭环

当前阶段所有 active TODO 都应服务这个闭环：

> Web 调研 -> 信息整理 -> Markdown 报告 -> artifact 输出

如果某个任务不能直接帮助这个闭环跑通，优先级应下降。

## Active TODO

### P0 主线闭环

- [ ] T1. 新增 `web_search` 最小工具
  目标：
  为调研任务提供最小可用的搜索入口，作为后续 `web_fetch` 的上游。
  关联文件：
  `app/tools/web/__init__.py`
  `app/tools/web/search.py`
  `app/tools/registry.py`
  `app/runtime.py`
  `tests/test_tools.py`
  完成标准：
  tool 已接入默认 runtime；返回结果可供后续页面抓取使用；有最小测试覆盖。

- [ ] T2. 新增 `web_fetch` 页面读取工具
  目标：
  让 agent 能基于搜索结果继续读取网页正文，而不是停在搜索摘要。
  关联文件：
  `app/tools/web/__init__.py`
  `app/tools/web/fetch.py`
  `app/tools/registry.py`
  `app/runtime.py`
  `tests/test_tools.py`
  完成标准：
  tool 已接入默认 runtime；输入输出格式稳定；可以和 `web_search` 串起来。

- [ ] T3. 新增 `write_report`
  目标：
  把最终整理结果写成稳定输出文件，而不是只返回一段文本。
  关联文件：
  `app/tools/builtin/write_report.py`
  `app/tools/builtin/__init__.py`
  `app/tools/registry.py`
  `app/outputs/__init__.py`
  `app/outputs/writer.py`
  `app/threads/paths.py`
  `tests/test_tools.py`
  完成标准：
  能写出 `report.md`；输出路径稳定；工具返回值可继续交给 `present_files`。

- [ ] T4. 改造 `present_files`，真正联动 `artifacts`
  目标：
  让 artifact 成为线程状态的一等数据，而不是只是给模型看的字符串。
  关联文件：
  `app/tools/builtin/present_files.py`
  `app/state.py`
  `app/client.py`
  `app/runtime.py`
  `tests/test_tools.py`
  `tests/test_app.py`
  完成标准：
  `ThreadState.artifacts` 被更新；`chat()` / `stream()` 都能拿到 artifact 结果；工具输出不再只是一段展示文本。

- [ ] T5. 扩展 `AppClient.stream()` 事件协议
  目标：
  让流式输出不仅有 AI 文本，还能看到工具与状态变化。
  关联文件：
  `app/client.py`
  `app/state.py`
  `tests/test_app.py`
  完成标准：
  至少覆盖 `ai`、`tool`、`values`、`end`、`error`；artifact 相关状态变化对调用方可见。

### P1 支撑闭环

- [ ] T6. 把线程路径模型真正接入输出链路
  目标：
  让 `ThreadPaths` 不只是静态路径定义，而是实际参与报告写出与 artifact 存放。
  关联文件：
  `app/threads/paths.py`
  `app/tools/builtin/present_files.py`
  `app/tools/builtin/write_report.py`
  `app/state.py`
  `tests/test_threads.py`
  完成标准：
  报告文件和 artifact 有稳定 thread 级位置；路径约定被测试覆盖。

- [ ] T7. 明确 `ThreadState` 的最小更新约定
  目标：
  让后续 AI 清楚哪些字段是 runtime 主写、哪些字段是工具写入。
  关联文件：
  `app/state.py`
  `app/client.py`
  `app/runtime.py`
  `docs/LITE_ARCHITECTURE.md`
  完成标准：
  `artifacts`、`thread_data`、`uploaded_files` 的职责和更新来源有明确文档或代码约束。

- [ ] T8. 以 DeerFlow 语义重建第一批 middleware
  目标：
  在不回退到 demo 语义的前提下，重建最小 runtime 保护层。
  关联文件：
  `app/agents/__init__.py`
  `app/agents/middlewares/__init__.py`
  `app/agents/middlewares/tool_error.py`
  `app/agents/middlewares/loop_detection.py`
  `app/agents/middlewares/clarification.py`
  `app/runtime.py`
  `tests/test_middlewares.py`
  完成标准：
  行为围绕真实工具失败、tool loop、clarification 恢复设计；确认语义成立后再默认启用。

## Recent Done

- [x] D1. 统一 runtime 装配入口
  关联文件：
  `app/agent.py`
  `app/runtime.py`
  `app/checkpointer.py`
  `app/state.py`

- [x] D2. 建立最小 builtin tools 骨架
  关联文件：
  `app/tools/__init__.py`
  `app/tools/registry.py`
  `app/tools/builtin/__init__.py`
  `app/tools/builtin/clarification.py`
  `app/tools/builtin/present_files.py`
  `tests/test_tools.py`

- [x] D3. 建立线程路径基础模型
  关联文件：
  `app/threads/__init__.py`
  `app/threads/paths.py`
  `tests/test_threads.py`

- [x] D4. 稳住 `AppClient.chat()` / `AppClient.stream()`
  关联文件：
  `app/client.py`
  `tests/test_app.py`

- [x] D5. 移除 demo 语义的默认 middleware 与占位工具
  关联文件：
  `app/runtime.py`
  `app/tools/registry.py`
  `app/__init__.py`
  `tests/test_tools.py`

## Parked

- [-] S1. sandbox
  原因：
  当前阶段核心不是执行隔离，而是先打通调研闭环。

- [-] S2. memory
  原因：
  当前阶段还没有形成值得持久化的长期任务流。

- [-] S3. MCP
  原因：
  现在优先做内建最小工具链，不引入额外接入面。

- [-] S4. vision
  原因：
  当前闭环不依赖图像理解。

- [-] S5. title middleware / todo middleware
  原因：
  属于外围能力，不是当前主线。

- [-] S6. subagent
  原因：
  当前代码规模与任务复杂度还不足以证明其必要性。

- [-] S7. 大而全工具注册系统
  原因：
  现在应先让最小工具链跑通，而不是提前泛化。

## 当前阶段退出标准

- [ ] Web 调研闭环已经跑通
- [ ] artifact 输出已经打通
- [ ] runtime 保护能力达到最小可用
- [ ] 下一阶段可以自然扩到文件分析、代码执行、报告生成
