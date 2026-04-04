# DeerFlow Lite TODO

这份 TODO 的前提不变：

- 总体方向仍然是 DeerFlow
- 当前阶段用 Web 调研任务来收敛实现
- 任务节点不是分叉方向

## 当前阶段

当前 active TODO 只保留未完成项。

已完成的 Phase 0 / Phase 1 内容已归档到本文末尾，不再作为待办处理。

## 当前待完成

当前待办应优先服务这个阶段性闭环：

> Web 调研 -> 信息整理 -> Markdown 报告 -> artifact 输出

### 1. 补齐调研任务最小工具链 `pending`

优先顺序：

1. `web_search`
2. `web_fetch`
3. `write_report`
4. `present_files` 与 `artifacts` 联动

原因：

- 这是当前阶段最核心的任务闭环
- 这些能力后续也能直接服务 DeerFlow 的学术综述、技术分析、文件分析与报告生成

### 2. 修正第一批 runtime middleware 语义 `pending`

优先顺序：

1. `ToolErrorHandlingMiddleware`
2. `LoopDetectionMiddleware`
3. `ClarificationMiddleware`

原因：

- 这是最小但收益最高的一组 runtime 保护
- 但当前实现还更像 demo 语义，未完全对齐 DeerFlow 风格 runtime

建议目录：

- `app/middlewares/`

### 3. 完善 artifact 输出闭环 `pending`

重点：

1. `write_report` 生成输出文件
2. `present_files` 真正写入 `ThreadState.artifacts`
3. `stream()` 中能看到 artifact 相关状态变化

### 4. 完善流式事件协议 `pending`

目标：

- 不只看 AI 文本
- 能看到工具调用
- 能看到工具结果
- 能看到 state 摘要变化

### 5. 保持线程模型可继续扩展 `pending`

当前已有：

- `app/threads/paths.py`
- 最小 `ThreadState`
- checkpointer 接口

接下来要保证这些能力能自然支撑后续 DeerFlow 任务，而不是只服务当前 demo。

## 已完成

### 工具层基础骨架 `done`

最小工具集建议：

1. `ask_clarification`
2. `present_files`
3. 一个简单验证工具
   - `get_time`
   - 或本地只读文件工具

完成情况：

- 已新增 `app/tools/`
- 已新增 `app/tools/builtin/`
- 已接入 `ask_clarification`
- 已接入 `present_files`
- 已接入 `get_time`
- 已通过 `runtime.get_tools(...)` 接入 agent runtime

### 线程路径基础模型 `done`

完成情况：

- 已新增 `app/threads/paths.py`
- 已定义线程目录、workspace、uploads、outputs 路径模型
- 已提供目录创建入口

## 暂时不要做

- sandbox
- memory
- MCP
- vision
- title middleware
- todo middleware
- subagent
- 大而全工具注册系统

这些功能现在都会稀释主线，因为当前阶段的核心不是“做得更像完整 DeerFlow”，而是“围绕一个任务节点把 DeerFlow 核心 runtime 打通”。

## Exit criteria

进入下一阶段之前，至少满足：

- Web 调研闭环已经跑通
- artifact 输出已经打通
- runtime 保护能力达到最小可用

达到这些条件后，再继续扩展到更广义的 DeerFlow 任务。

## 已归档

### Phase 0

- Stabilize `AppClient.stream()` `done`
- Define a stable event contract `done`
- Strengthen baseline tests `done`

### Phase 1 / 基础 runtime 收敛

- Add runtime assembly `done`
- Add a formal checkpointer module `done`
- Expand `ThreadState` minimally `done`

### 归档说明

这些项已经在当前代码库中完成，不再保留为 active TODO。后续如果需要回看实现细节，直接查看对应源码文件即可。
