# Architecture Overview

## 定位

`deerflow-lite` 的总体方向不变，始终是朝着简化版 DeerFlow runtime 演进。

这里要区分两层目标：

- 最终目标：
  逐步逼近 DeerFlow 的核心能力，而不是做一个一次性的 agent demo

- 当前阶段目标：
  用一个最容易形成闭环、又最能逼出 DeerFlow 核心能力的任务推进实现

当前选定的阶段性牵引任务是：

> Web 调研 -> 信息整理 -> 生成 Markdown 报告 -> artifact 输出

这个任务只是架构完善过程中的节点，不是产品方向分叉，更不是最终边界。

## 为什么当前阶段选 Web 调研

1. 不需要先做上传文件链路
2. 不需要先做安全沙箱
3. 可以直接逼出工具调用、状态管理、报告输出、artifact 展示这些核心能力
4. 跑通之后，能平滑扩展到学术综述、技术分析、文件分析、报告生成和更复杂工作流

## 总体架构方向

```text
CLI / Python caller
  -> app.cli / main.py
  -> north.client.AppClient
  -> north.runtime
  -> north.agent.build_agent(...)
  -> LangChain / LangGraph agent graph
  -> state + tools + middleware + checkpointer
```

核心设计原则：

> 对外 API 保持简单稳定，复杂度被收敛到 runtime 组装层和状态模型中。

## 当前阶段真正要逼出来的核心能力

### 工具驱动的多步执行

- 搜索
- 抓取
- 提炼
- 生成报告
- 返回 artifact

### 线程状态

同一个 `thread_id` 要能承载持续执行过程，而不是一次调用就结束。

### 流式可观测性

`AppClient.stream()` 最终应承担统一事件协议：

- `ai`
- `tool`
- `values`
- `end`
- `error`

### 运行时保护

当前阶段最值得保留的 middleware 方向依然是：

1. `ToolErrorHandlingMiddleware`
2. `LoopDetectionMiddleware`
3. `ClarificationMiddleware`

但当前 demo 实现不应继续作为默认 runtime 行为存在，需要围绕真实工具执行语义重建后再默认启用。

## 当前阶段的任务闭环

```text
用户给调研问题
  -> agent 调用 web_search
  -> agent 调用 web_fetch / 页面读取
  -> agent 整理信息
  -> agent 写出 report.md
  -> agent 通过 present_files 返回 artifact
```
