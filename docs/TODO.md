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

### 8. Add a tiny tool layer `pending`

最小工具集建议：

1. `ask_clarification`
2. `present_files`
3. 一个简单验证工具
   - `get_time`
   - 或本地只读文件工具

建议目录：

- `app/tools/`
- `app/tools/builtin/`

### 9. Add thread-local file model `pending`

建议目录：

- `app/threads/paths.py`

后续再加：

- `ThreadDataMiddleware`
- `UploadsMiddleware`

## Recommended next implementation batch

如果只做一轮高性价比改动，建议按这个批次推进：

1. 添加 `app/middlewares/`
2. 添加第一组高价值 middleware
3. 添加 `app/tools/`
4. 添加最小工具集
5. 添加线程本地文件模型

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
