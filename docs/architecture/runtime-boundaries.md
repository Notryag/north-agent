# Runtime Boundaries

## 当前代码的正确定位

当前代码已经有了正确骨架：

- `app/config.py`
- `app/state.py`
- `app/agent.py`
- `app/runtime.py`
- `app/client.py`
- `app/checkpointer.py`

问题不在于“缺更多模块”，而在于：

- 哪些能力是真正推动 DeerFlow 方向的
- 哪些只是看起来像 DeerFlow，但没有形成任务闭环

## 不变的模块边界

### `app/config.py`

- 环境变量加载
- runtime 配置
- 参数校验

### `app/state.py`

- 共享状态 schema
- 未来 reducer 扩展入口

### `app/runtime.py`

- 组装工具
- 组装 middleware
- 组装 checkpointer
- 组装 state schema

### `app/agent.py`

- 创建 model
- 调用 `create_agent(...)`

### `app/client.py`

- `chat()` / `stream()` 对外入口
- 标准化事件流
- `thread_id` 与 runnable config

### `app/tools/*`

- 工具定义
- 工具注册

### `app/agents/middlewares/*`

- 运行时行为控制

## 当前最小状态模型方向

```python
class ThreadState(AgentState):
    title: str | None
    artifacts: list[str]
    thread_data: dict | None
    uploaded_files: list[dict] | None
```

其中：

- `artifacts` 对当前阶段尤其重要
- `thread_data` 是未来文件 / 工作区能力的基础

## 当前阶段不该做的事

- 提前引入完整 sandbox
- 提前引入 memory
- 提前引入 title / todo 等外围能力
- 提前引入过多工具
- 提前引入多子代理协作

这些能力都属于 DeerFlow 的后续阶段，不是当前阶段的主推进项。

## 当前阶段的架构策略

> 保持 DeerFlow 总体架构方向不变，用 Web 调研这个阶段性任务去验证和逼出最关键的 runtime 能力。
