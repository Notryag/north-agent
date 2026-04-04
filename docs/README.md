# Docs Guide

这个目录里的文档分工要明确，不然 AI 很容易在 `TODO`、`plan`、`architecture` 三份文件之间来回重复。

## 推荐阅读顺序

1. `docs/TODO.md`
2. `docs/LITE_EVOLUTION_PLAN.md`
3. `docs/LITE_ARCHITECTURE.md`

## 每份文档负责什么

### `docs/TODO.md`

负责：

- 当前可执行任务清单
- checkbox 状态
- 每个任务的关联文件
- 每个任务的完成标准

不负责：

- 长篇阶段论证
- 目录边界设计细节

### `docs/LITE_EVOLUTION_PLAN.md`

负责：

- 为什么当前阶段先做这些
- 各阶段先后顺序
- 优先级判断标准

不负责：

- checkbox 任务跟踪
- 已完成文件清单

### `docs/LITE_ARCHITECTURE.md`

负责：

- 模块职责
- 目标目录结构
- runtime 边界
- 哪类逻辑应该放到哪里

不负责：

- 近期待办列表
- 任务状态管理

## AI 更新规则

1. 做完具体任务后，先更新 `docs/TODO.md`
2. 如果任务优先级或阶段顺序变了，再更新 `docs/LITE_EVOLUTION_PLAN.md`
3. 如果模块归属、目录边界或状态职责变了，再更新 `docs/LITE_ARCHITECTURE.md`
4. 如果只是代码细节变化，不要把三份文档都改一遍
