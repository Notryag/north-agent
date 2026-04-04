# DeerFlow Lite TODO

这份 TODO 基于以下文档整理：

- `docs/LITE_EVOLUTION_PLAN.md`
- `docs/LITE_ARCHITECTURE.md`

目标是把当前 lite runtime 按既定阶段稳定推进，并明确区分已完成与待完成项。

## 当前阶段

当前 active TODO 只保留未完成项。

已完成的 Phase 0 / Phase 1 内容已归档到本文末尾，不再作为待办处理。

## 待完成

### 7. Add the first three high-value middlewares `pending`

优先顺序：

1. `ToolErrorHandlingMiddleware`
2. `LoopDetectionMiddleware`
3. `ClarificationMiddleware`

原因：

- 这是最小但收益最高的一组 runtime 保护

建议目录：

- `app/middlewares/`

### 8. Add a tiny tool layer `done`

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

### 9. Add thread-local file model `done`

完成情况：

- 已新增 `app/threads/paths.py`
- 已定义线程目录、workspace、uploads、outputs 路径模型
- 已提供目录创建入口

后续再加：

- `ThreadDataMiddleware`
- `UploadsMiddleware`

## Recommended next implementation batch

如果只做一轮高性价比改动，建议按这个批次推进：

1. 为工具调用补充真实 agent 级集成测试
2. 引入 `ThreadDataMiddleware`
3. 引入 `UploadsMiddleware`
4. 让 `present_files` 与线程输出目录联动
5. 视需要扩展 `artifacts` 写入流程

## 暂时不要做

- sandbox
- memory
- MCP
- vision
- title middleware
- todo middleware
- subagent
- 大而全工具注册系统

这些功能现在都会稀释主线。

## Exit criteria

进入下一阶段之前，至少满足：

- middleware 层有第一批实现
- tools 层有最小可用集合
- thread-local file model 有明确路径

满足这些条件后，再继续扩展 artifact、上传和更复杂的 runtime 行为。

## 已归档

### Phase 0

- Stabilize `AppClient.stream()` `done`
- Define a stable event contract `done`
- Strengthen baseline tests `done`

### Phase 1

- Add runtime assembly `done`
- Add a formal checkpointer module `done`
- Expand `ThreadState` minimally `done`

### 归档说明

这些项已经在当前代码库中完成，不再保留为 active TODO。后续如果需要回看实现细节，直接查看对应源码文件即可。
