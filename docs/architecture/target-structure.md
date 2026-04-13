# Target Structure

## 最终目标目录结构

`deerflow-lite` 的目录结构应逐步朝 `deer-flow/backend/packages/harness/deerflow/` 的精简版靠拢。

```text
app/
├── __init__.py
├── agent.py
├── client.py
├── runtime.py
├── config.py
├── checkpointer.py
├── state.py
├── skills/
│   ├── __init__.py
│   └── loader.py
├── models/
│   ├── __init__.py
│   └── factory.py
├── agents/
│   ├── __init__.py
│   ├── lead/
│   └── middlewares/
├── tools/
│   ├── __init__.py
│   ├── registry.py
│   └── builtin/
├── threads/
│   ├── __init__.py
│   └── paths.py
├── outputs/
│   ├── __init__.py
│   └── writer.py
├── utils/
│   ├── __init__.py
│   └── text.py
└── cli.py
```

## 每个目录未来负责什么

### `app/models/`

- 模型工厂
- 模型 provider 适配
- thinking / provider 参数兼容

### `app/skills/`

- skill 发现与加载
- skill catalog 生成
- `SKILL.md` 正文按需读取入口

### `app/agents/`

- agent 相关实现
- 主 agent
- 更复杂的 prompt 组装或内部节点逻辑

### `app/agents/middlewares/`

- runtime middleware
- 每个 middleware 只解决一个问题

建议最终收敛：

- `tool_error.py`
- `loop_detection.py`
- `clarification.py`
- `thread_data.py`
- `uploads.py`

### `app/tools/`

- 工具定义
- 工具注册
- 按类型分目录

### `app/tools/builtin/`

- 与 runtime 强绑定的内置工具
- 例如 `ask_clarification`、`web_search`、`web_fetch`、`present_files`、`write_report`

### `app/threads/`

- thread 路径模型
- workspace / uploads / outputs 约定

### `app/outputs/`

- 输出文件生成
- `report.md` 等 artifact 写出辅助逻辑

### `app/utils/`

- 无状态、与业务边界弱耦合的辅助函数

## 目录结构演进原则

1. 若某项能力未来显然属于 `models/`、`tools/`、`agents/middlewares/`、`threads/`、`outputs/`，就不要继续塞回顶层文件
2. 当前阶段可以少量保留在单文件里，但一旦增长，就迁移到目标目录
3. 目录结构服务于 DeerFlow 总体方向，而不是当前临时任务
