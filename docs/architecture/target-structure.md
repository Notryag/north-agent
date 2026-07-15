# Target Structure

## 最终目标目录结构

`north-agent` 的目录结构应逐步朝 `deer-flow/backend/packages/harness/` 的分层方向靠拢：

- `packages/harness/` 放可复用 harness 包
- `app/` 只放当前仓库自己的 CLI / API / 默认配置注入
- 依赖方向必须始终保持 `app -> harness`
- 任何兼容层都只是迁移过程中的短期产物，目标是最终删除

当前选定的 harness 包名为 `north`。

```text
packages/
└── harness/
    ├── pyproject.toml
    └── north/
        ├── __init__.py
        ├── agent.py
        ├── client.py
        ├── config.py
        ├── checkpointer.py
        ├── resources.py
        ├── state.py
        ├── runtime/
        │   ├── __init__.py
        │   ├── service.py
        │   ├── worker.py
        │   ├── serialization.py
        │   ├── runs/
        │   └── stream_bridge/
        ├── skills/
        │   ├── __init__.py
        │   └── loader.py
        ├── agents/
        │   ├── __init__.py
        │   └── middlewares/
        ├── tools/
        │   ├── __init__.py
        │   ├── registry.py
        │   └── builtin/
        ├── threads/
        │   ├── __init__.py
        │   └── paths.py
        └── outputs/
            ├── __init__.py
            └── writer.py
app/
├── __init__.py
├── __main__.py
├── cli.py
├── api/
└── defaults/
skills/
tests/
```

## Harness 与 App 的职责

### `packages/harness/north/`

- 可复用 agent harness
- runtime service / stream / run lifecycle
- state schema
- tools / middlewares / skill loading
- thread / artifact / resource contract
- 可被其他宿主项目复用的 client 和 agent factory
- 不应依赖当前仓库固定的 `skills/`、`.deerflow/`、`.env` 路径

### `app/`

- 当前仓库宿主层
- CLI / API / 未来前后端装配
- 当前仓库默认 `skills_dir`、`thread_base_dir`、`env_path` 注入
- 不承载可复用 runtime 核心实现

## 目录结构演进原则

1. 若某项能力可在其他宿主项目复用，就优先放进 `packages/harness/north/`
2. 若某项能力只属于当前仓库的入口、部署、默认路径或 UI/API glue，就留在 `app/`
3. 兼容层可以暂时存在，但必须标记为迁移中产物，不得长期作为正式架构
4. 每次迁移都应减少一部分 `app -> app` 旧实现依赖，逐步改成 `app -> north`
5. 当某一条链迁移完成后，应删除对应兼容层，而不是长期双轨维护
