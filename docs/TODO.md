# DeerFlow Lite TODO

这份文件只做一件事：

> 维护当前阶段可直接执行的任务清单。

已完成事项归档到 [TODO_ARCHIVE](D:/workspace/github/deerflow-lite/docs/TODO_ARCHIVE.md)。

如果需要看阶段原因、优先级来源、长期演进顺序，请看 `docs/LITE_EVOLUTION_PLAN.md`。

如果需要看模块职责、目录边界、未来目标结构，请看 `docs/LITE_ARCHITECTURE.md`。

## 快速索引

- 做端到端验证：
  看 `T13`

- 做文件分析闭环：
  看 `T13`、`T15`

- 做代码执行准备：
  看 `T16`

- 查已完成历史：
  看 `docs/TODO_ARCHIVE.md`

## 使用规则

- `[ ]` 未完成，属于当前或近期应做任务
- `[x]` 已完成，一般不保留在本文件主体，完成后移动到归档
- `[-]` 明确暂缓，不属于当前阶段主线

每个任务都应尽量包含：

1. 目标
2. 关联文件
3. 完成标准

后续 AI 更新本文件时，按这几个规则处理：

1. 完成代码后，优先回写本文件中的 checkbox 状态
2. 如果实际改动文件与 TODO 中列出的文件不同，要同步修正“关联文件”
3. 完成项应移动到 `docs/TODO_ARCHIVE.md`
4. 如果改动改变了阶段顺序，更新 `docs/LITE_EVOLUTION_PLAN.md`
5. 如果改动改变了模块边界，更新 `docs/LITE_ARCHITECTURE.md`

默认不需要完整阅读 `docs/LITE_EVOLUTION_PLAN.md` 和 `docs/LITE_ARCHITECTURE.md`。

只有当任务涉及优先级调整或模块边界变化时，才需要补读。

## 当前阶段目标

上一阶段已经打通：

> Web 调研 -> 信息整理 -> Markdown 报告 -> artifact 输出

当前阶段开始围绕这个基础自然扩展：

> 文件输入 -> 文件发现 -> 文件读取 -> Markdown 报告 -> artifact 输出

并在架构上同步推进：

> 按 DeerFlow 的 `Harness/App` 分层收敛当前仓库，把可复用 runtime 核心迁入 `packages/harness/north`，逐步删掉旧兼容层

## Active TODO

### P0 Harness/App 架构收敛

- [ ] H1. 固化 `packages/harness/north` 的公开边界
  目标：
  明确 `north` 的稳定公开接口，只把真正可复用的 harness 能力放进包里。
  关联文件：
  `packages/harness/pyproject.toml`
  `packages/harness/north/__init__.py`
  `docs/architecture/target-structure.md`
  完成标准：
  `north` 公开入口清晰；`app` 不再承担可复用核心实现定义。

- [ ] H2. 去掉 `north` 对当前仓库固定路径的隐式依赖
  目标：
  让 `north` 不再把仓库根、skills 目录、thread 目录当成内部常量假设。
  关联文件：
  `packages/harness/north/config.py`
  `packages/harness/north/threads/*`
  `packages/harness/north/resources.py`
  `packages/harness/north/tools/builtin/*`
  完成标准：
  `north` 的路径相关能力由显式配置或 runtime context 注入；宿主项目负责给默认值。

- [ ] H3. 分链迁移并删除兼容层
  目标：
  按链路迁移 `config/resources/skills/threads/outputs`、`runtime/checkpointer/tools`、`agent/client`，每完成一条链就删除对应 `app` 兼容层。
  关联文件：
  `app/`
  `packages/harness/north/`
  `tests/`
  完成标准：
  兼容层数量单调减少；不保留长期双实现；全量测试持续通过。

### P3 文件分析闭环

- [ ] T13. 加端到端 smoke test
  目标：
  用一条测试证明当前用户入口能跑通上传、文件发现、文件读取、报告写出、artifact 暴露。
  关联文件：
  `tests/test_app.py`
  `tests/test_cli.py`
  `app/client.py`
  `app/cli.py`
  `app/tools/builtin/list_files.py`
  `app/tools/builtin/read_file.py`
  `app/tools/builtin/write_report.py`
  `app/tools/builtin/present_files.py`
  完成标准：
  测试覆盖 `files=` 上传；agent 侧能看到 `upload://...`；最终报告进入 outputs；`ChatResponse.artifacts` 或 CLI 输出能看到 artifact。

- [ ] T15. 收敛文件分析 skill 的端到端说明
  目标：
  让 `file-analysis` skill 更明确地指导模型先发现文件、再读取相关文件、最后按需写报告。
  关联文件：
  `skills/file-analysis/SKILL.md`
  `skills/README.md`
  `readme.md`
  `tests/test_skills.py`
  完成标准：
  skill 说明覆盖上传文件、线程文件、报告输出三类路径；默认 prompt 仍只暴露 skill catalog，不注入正文。

### P4 代码执行准备

- [ ] T16. 定义代码执行前置边界
  目标：
  在真正引入执行能力前，先明确最小输入、输出、artifact、风险边界，避免直接做泛化 sandbox。
  关联文件：
  `docs/TODO.md`
  `docs/plan/roadmap.md`
  `docs/architecture/runtime-boundaries.md`
  完成标准：
  文档明确代码执行能力的最小闭环、暂不做事项、与 `workspace://` / `output://` 的关系。

## Parked

- [-] S1. sandbox
  原因：
  代码执行边界尚未定义清楚，当前不直接引入完整 sandbox。

- [-] S2. memory
  原因：
  当前还没有形成值得持久化的长期任务流。

- [-] S3. MCP
  原因：
  现在优先做内建最小工具链，不引入额外接入面。

- [-] S4. vision
  原因：
  当前闭环不依赖图像理解。

- [-] S5. title middleware / todo middleware
  原因：
  属于外围能力，不是当前主线。

- [-] S6. subagent
  原因：
  当前代码规模与任务复杂度还不足以证明其必要性。

- [-] S7. 大而全工具注册系统
  原因：
  现在应先让最小工具链跑通，而不是提前泛化。
