# DeerFlow Lite 架构说明

## 1. 定位

`deerflow-lite` 的总体方向不变，始终是朝着 **简化版 DeerFlow runtime** 演进。

这里要明确区分两层目标：

### 最终目标

逐步逼近 DeerFlow 的核心能力，而不是做一个一次性的 agent demo：

- thread-based runtime
- tool-driven 多步执行
- artifact / 文件输出
- 可观察的流式事件
- clarification / recovery / loop protection
- 后续可继续扩展到文件分析、代码执行、报告生成、子代理协作

### 当前阶段目标

为了避免架构继续发散，当前阶段选一个最容易形成闭环、又最能逼出 DeerFlow 核心能力的任务来推进实现。

当前选定的阶段性牵引任务是：

> Web 调研 -> 信息整理 -> 生成 Markdown 报告 -> artifact 输出

这个任务只是 **架构完善过程中的节点**，不是产品方向分叉，更不是最终边界。

## 2. 为什么当前阶段选 Web 调研

不是因为 DeerFlow 只做调研，而是因为它最适合作为当前阶段的验证任务：

1. 不需要先做上传文件链路
2. 不需要先做安全沙箱
3. 可以直接逼出工具调用、状态管理、报告输出、artifact 展示这些核心能力
4. 跑通之后，能平滑扩展到：
   - 学术综述
   - 技术可行性分析
   - 文件分析
   - 报告/PPT/脚本生成
   - 更复杂的多步骤工作流

所以 Web 调研是一个 **阶段性验证任务**，不是新方向。

## 3. 总体架构方向

目标架构保持不变：

```text
CLI / Python caller
  -> AppClient
  -> Runtime Assembly
  -> build_agent(...)
  -> LangChain / LangGraph agent graph
  -> state + tools + middleware + checkpointer
```

核心设计原则也不变：

> 对外 API 保持简单稳定，复杂度被收敛到 runtime 组装层和状态模型中。

## 4. 最终目标目录结构

为了避免 `deerflow-lite` 在演进中继续发散，**最终目标结构建议直接参考 `deer-flow` 的目录分层**，但只保留 lite 版当前阶段真正需要的部分。

也就是说，目录结构层面不另起炉灶，而是朝着 `deer-flow/backend/packages/harness/deerflow/` 的精简版靠拢。

参考来源主要是：

- `deer-flow/backend/CLAUDE.md`
- `deer-flow/backend/docs/ARCHITECTURE.md`

### `deer-flow` 中最值得对齐的分层

`deer-flow` 的核心 harness 目录大致是：

```text
packages/harness/deerflow/
├── agents/
├── sandbox/
├── subagents/
├── tools/
├── mcp/
├── models/
├── skills/
├── config/
├── community/
├── reflection/
├── utils/
└── client.py
```

对 `deerflow-lite` 来说，不需要一次性把这些都做完，但**最终目标应该在结构上与这套分层兼容**。

### `deerflow-lite` 建议的最终目标结构

```text
app/
├── __init__.py                  # 对外导出 lite runtime 入口
├── agent.py                     # 统一创建 agent，保留 build_agent 作为装配入口
├── client.py                    # chat / stream 对外入口
├── runtime.py                   # tools / middlewares / checkpointer / state schema 收敛点
├── config.py                    # lite 配置加载与校验
├── checkpointer.py              # 持久化状态的轻量封装
├── state.py                     # 共享 ThreadState
├── models/                      # 模型创建与 provider 适配
│   ├── __init__.py
│   └── factory.py
├── agents/                      # agent 相关实现
│   ├── __init__.py
│   ├── lead/                    # 主 agent
│   └── middlewares/             # middleware 组件
├── tools/                       # 工具体系
│   ├── __init__.py
│   ├── registry.py
│   ├── builtin/                 # 内置工具
│   └── web/                     # 当前阶段最关键的 web 调研工具
├── threads/                     # thread 路径、工作区、artifact 约定
│   ├── __init__.py
│   └── paths.py
├── outputs/                     # 报告生成、artifact 写出辅助逻辑
│   ├── __init__.py
│   └── writer.py
├── utils/                       # 纯工具函数
│   ├── __init__.py
│   └── text.py
└── cli.py                       # 命令行入口
```

这不是要求现在全部建出来，而是把它作为 **最终目标目录结构**。

## 5. 每个目录未来负责什么

下面这部分就是最终目标的职责定义。只要方向不变，后续实现都往这些职责上收敛。

### `app/agent.py`

作用：

- 保留统一的 `build_agent(...)` 入口
- 调用模型工厂、runtime 组装结果、`create_agent(...)`

它对应 `deer-flow` 里主 agent 装配入口的角色，但 lite 版先保持单文件即可。

### `app/client.py`

作用：

- 作为嵌入式 client 入口
- 暴露 `chat()` / `stream()`
- 统一事件协议

它对应 `deer-flow` 里的 [client.py](D:/workspace/github/deer-flow/backend/packages/harness/deerflow/client.py)。

### `app/runtime.py`

作用：

- 收敛 runtime 组装逻辑
- 决定当前有哪些 tools
- 决定当前有哪些 middlewares
- 决定 state schema / checkpointer

这是 `deerflow-lite` 当前最关键的战略模块。

### `app/config.py`

作用：

- 环境变量加载
- 运行参数校验
- 控制 lite runtime 配置

它对应 `deer-flow` 里的 `config/` 子系统，但 lite 版先维持单文件。

### `app/checkpointer.py`

作用：

- 提供 lite 版默认 checkpointer
- 后续可扩展 sqlite / 更持久的方案

它对应 `deer-flow` 里 `agents/checkpointer/` 的简化版本。

### `app/state.py`

作用：

- 定义 `ThreadState`
- 承载 thread 级共享状态

它对应 `deer-flow` 里的 `agents/thread_state.py`。

### `app/models/`

作用：

- 模型工厂
- 模型 provider 适配
- thinking / provider 参数兼容

这部分对应 `deer-flow` 里的 `models/`。

当前如果模型逻辑还很小，可以先留在 `agent.py`，但最终应该独立成目录。

### `app/agents/`

作用：

- 放 agent 相关实现
- 后续如果有 `lead agent`、更复杂的 prompt 组装、agent 内部节点逻辑，都收在这里

这部分对应 `deer-flow` 里的 `agents/`。

#### `app/agents/middlewares/`

作用：

- 放运行时中间件
- 每个 middleware 只解决一个问题

建议最终收敛这些：

- `tool_error.py`
- `loop_detection.py`
- `clarification.py`
- `thread_data.py`
- `uploads.py`

这直接对应 `deer-flow` 的 `agents/middlewares/`。

### `app/tools/`

作用：

- 定义工具
- 工具注册
- 按类型分目录

这部分对应 `deer-flow` 里的 `tools/`。

#### `app/tools/builtin/`

作用：

- 放最基础、与 runtime 强绑定的内置工具

例如：

- `ask_clarification`
- `present_files`
- `write_report`

#### `app/tools/web/`

作用：

- 放当前阶段最关键的 Web 调研工具

例如：

- `web_search`
- `web_fetch`

这个目录在当前阶段尤其重要，因为它是“阶段性任务节点”的核心。

### `app/threads/`

作用：

- 定义 thread 路径模型
- 管理 workspace / uploads / outputs 的约定

它对应 `deer-flow` 里 `ThreadDataMiddleware + paths/sandbox user-data 路径模型` 的 lite 化版本。

### `app/outputs/`

作用：

- 专门负责输出文件生成
- 统一 `report.md` 等 artifact 的写出逻辑

这是 `deerflow-lite` 当前阶段最应该明确出来的一层，因为“报告输出”是当前任务节点的最终交付物。

### `app/utils/`

作用：

- 放无状态、与业务边界弱耦合的辅助函数
- 避免把纯文本处理或通用逻辑混进 runtime 核心模块

### `app/cli.py`

作用：

- 保持一个很薄的命令行入口
- 不承担核心 runtime 逻辑

## 6. 为什么把目录结构也作为最终目标是更好的

是的，这样更好，原因有三个：

1. **减少跑偏**
   你现在的主要问题不是“代码太少”，而是实现很容易围绕某个阶段任务临时长歪。把目录结构本身作为目标，可以防止阶段性任务把项目带偏。

2. **把“阶段任务”和“总体方向”分开**
   Web 调研只是当前节点，但目录结构仍然按照 DeerFlow 的大方向组织。这样做可以保证：
   - 当前任务能推进
   - 将来切到文件分析、代码执行、artifact 工作流时不需要重组工程

3. **更容易判断该不该新增模块**
   以后每次想加代码时，你可以先问：
   - 这个能力应该落到哪个最终目标目录里？
   - 它是临时逻辑，还是 DeerFlow 方向上的长期模块？

如果回答不清楚，就说明这项改动大概率不该现在做。

## 7. 当前代码的正确定位

当前代码已经有了正确骨架：

- `app/config.py`
- `app/state.py`
- `app/agent.py`
- `app/runtime.py`
- `app/client.py`
- `app/checkpointer.py`

这说明项目已经不是空白设计，而是进入了 **围绕真实任务收敛 runtime 能力** 的阶段。

问题不在于“缺更多模块”，而在于：

- 哪些能力是真正推动 DeerFlow 方向的
- 哪些只是看起来像 DeerFlow，但没有形成任务闭环

## 8. 当前阶段真正要逼出来的核心能力

围绕 Web 调研这个阶段性任务，当前最值得推进的是：

### 5.1 工具驱动的多步执行

不是单轮问答，而是：

- 搜索
- 抓取
- 提炼
- 生成报告
- 返回 artifact

### 5.2 线程状态

同一个 `thread_id` 要能承载持续执行过程，而不是一次调用就结束。

当前最小状态模型方向仍然成立：

```python
class ThreadState(AgentState):
    title: str | None
    artifacts: list[str]
    thread_data: dict | None
    uploaded_files: list[dict] | None
```

其中：

- `artifacts` 对当前阶段尤其重要
- `thread_data` 是未来文件/工作区能力的基础

### 5.3 流式可观测性

`AppClient.stream()` 不能只是输出 AI 文本。

它最终应承担统一事件协议：

- `ai`
- `tool`
- `values`
- `end`
- `error`

这样它既能服务 CLI，也能服务后续 UI。

### 5.4 运行时保护

当前阶段最值得保留的 middleware 方向依然是：

1. `ToolErrorHandlingMiddleware`
2. `LoopDetectionMiddleware`
3. `ClarificationMiddleware`

但当前 demo 实现不应继续作为默认 runtime 行为存在。

它们是 DeerFlow 风格 runtime 的第一层保护壳，但需要围绕真实工具执行语义重建后再默认启用。

## 9. 当前阶段的任务闭环

当前阶段不改总体方向，只是先围绕这个闭环推进：

```text
用户给调研问题
  -> agent 调用 web_search
  -> agent 调用 web_fetch / 页面读取
  -> agent 整理信息
  -> agent 写出 report.md
  -> agent 通过 present_files 返回 artifact
```

这个闭环一旦跑通，后续扩展路径仍然指向 DeerFlow：

- Web 调研
  -> 学术综述
- Web 调研
  -> 技术可行性分析
- Web 调研
  -> 文件分析
- Web 调研
  -> 报告 / PPT / 脚本生成
- Web 调研
  -> 多子任务工作流

所以它不是分叉，而是通往总体目标的一段路。

## 10. 不变的模块边界

总体模块边界不因为当前阶段任务改变：

### `app/config.py`

负责：

- 环境变量加载
- runtime 配置
- 参数校验

### `app/state.py`

负责：

- 共享状态 schema
- 未来 reducer 扩展入口

### `app/runtime.py`

负责：

- 组装工具
- 组装 middleware
- 组装 checkpointer
- 组装 state schema

这是整个 lite runtime 的战略模块。

### `app/agent.py`

负责：

- 创建 model
- 调用 `create_agent(...)`

### `app/client.py`

负责：

- `chat()` / `stream()` 对外入口
- 标准化事件流
- `thread_id` 与 runnable config

### `app/tools/*`

负责：

- 工具定义
- 工具注册

### `app/agents/middlewares/*`

负责：

- 运行时行为控制

## 11. 当前阶段不该做的事

因为总体方向不变，所以现在仍然要避免这些会稀释主线的工作：

- 提前引入完整 sandbox
- 提前引入 memory
- 提前引入 title / todo 等外围能力
- 提前引入过多工具
- 提前引入多子代理协作

这些能力都属于 DeerFlow 的后续阶段，不是当前阶段的主推进项。

## 12. 当前阶段最有价值的收敛方式

如果只用一句话描述现在的架构策略，应该是：

> 保持 DeerFlow 总体架构方向不变，用 Web 调研这个阶段性任务去验证和逼出最关键的 runtime 能力。

## 13. 结论

`deerflow-lite` 不是在从 DeerFlow 分叉成一个“调研系统”。

更准确地说：

- DeerFlow 是总体目标
- runtime 架构方向不变
- Web 调研只是当前阶段最合适的落地节点

因此，后续所有实现判断标准都应该是：

> 这项改动，是不是在帮助 `deerflow-lite` 更接近 DeerFlow 的核心 runtime，而不只是让当前 demo 多一个功能。
