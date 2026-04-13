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
- 组装 skill
- 组装 middleware
- 组装 checkpointer
- 组装 state schema

### `app/skills/*`

- 从本地 skill 目录发现 skill 定义
- 读取 skill prompt
- 把 skill 转成 prompt 片段和工具约束

说明：

- skill 是 agent 装配层能力，不是 thread state
- skill 的选择属于 runtime scope，默认不写入 `ThreadState`
- 第一版只负责 prompt 和工具白名单，不承担 marketplace / sandbox / 远程安装职责

### `app/agent.py`

- 创建 model
- 调用 `create_agent(...)`

### `app/client.py`

- `chat()` / `stream()` 对外入口
- 标准化事件流
- `thread_id` 与 runnable config

说明：

- `thread_id` 在这里是 runtime scope，不是产品层对象
- 它的职责只是隔离一次持续任务的状态、checkpoint 和 artifact 路径
- 当前阶段不要围绕它继续发明更重的 thread 业务模型

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

### 当前最小状态更新约定

- `artifacts`
  当前唯一默认允许普通工具写入的共享字段。
  写入内容应是 thread 级 artifact 路径，而不是任意业务对象。

- `thread_data`
  当前由 runtime 预留。
  在没有专门工具契约之前，不应由普通工具随意写入。

- `uploaded_files`
  当前由 runtime / 输入接入层维护。
  工具可以读取，但不应直接改写。

- `title`
  当前不是主线能力，不作为普通工具输出目标。

### 关于 `outputs/`

- `outputs/` 只是 artifact 的物理落盘目录
- 它不是独立产品概念，也不是要扩展成通用文件系统抽象
- 当前保留它，只是为了让报告和后续 artifact 有稳定线程级落点

## 当前阶段不该做的事

- 提前引入完整 sandbox
- 提前引入 memory
- 提前引入 title / todo 等外围能力
- 提前引入过多工具
- 提前引入多子代理协作

这些能力都属于 DeerFlow 的后续阶段，不是当前阶段的主推进项。

## 当前阶段的架构策略

> 保持 DeerFlow 总体架构方向不变，用 Web 调研这个阶段性任务去验证和逼出最关键的 runtime 能力。
