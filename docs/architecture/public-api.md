# Public API

`north.__all__` 是 harness 的稳定顶层接口。宿主应用应优先从 `north` 导入这些名称，
并固定 Git commit 或发布版本。

## 宿主入口

- `AppConfig`：模型、Skill、线程存储和摘要配置
- `build_agent`：装配 LangChain/LangGraph Agent
- `invoke_agent_once`：执行一次产品无关的 Agent 调用
- `RunExecutor`：唯一的生产 `agent.astream` 执行循环，直接向 `StreamBridge` 发布标准
  graph chunks，并在 end sentinel 前等待宿主生命周期钩子完成
- `RuntimeExecutionResult`：Run 的类型化完成结果，保留原始 graph values，并显式携带可选
  `ClarificationRequest`；宿主不应反向解析 `thread_data`
- `ClarificationRequest`：产品无关的澄清问题、响应类型和可选项契约
- `StreamBridge` / `MemoryStreamBridge` / `RedisStreamBridge`：异步发布、可回放订阅、
  heartbeat、end 和清理语义
- `RuntimeStreamEvent`：产品无关的标准化 graph chunk
- `AppClient`、`ChatResponse`、`StreamEvent`：聊天和流式客户端契约

## 持久化与上下文

- `CheckpointerConfig`、`make_checkpointer`：管理 Checkpointer 生命周期
- `NorthSummarizationMiddleware`、`CompactionEvent`、`CompactionHook`：上下文压缩与宿主归档 Hook

## 可观测性

- `RuntimeEvent`、`RuntimeEventSink`、`RuntimeJournal`：模型与工具调用事件
- `TokenUsage`、`RuntimeUsageAccumulator`、`normalize_token_usage`：Token 用量归一化与汇总

`RuntimeStreamEvent` 是展示和状态流契约，`RuntimeEvent` 是 callback 可观测性契约。宿主不应
把两者合并成一个持久化或 UI 协议。

## 非公开装配接口

`north.runtime.get_*`、`north.tools.get_builtin_tools`、默认 Checkpointer 和具体资源路径实现
属于 harness 内部装配细节。仓库内测试可以直接覆盖这些模块，但宿主不应依赖其长期兼容性。

需要扩展具体工具时，宿主应把工具列表传给 `build_agent`，而不是修改或依赖默认工具注册表。
