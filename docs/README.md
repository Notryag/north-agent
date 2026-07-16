# Docs Guide

默认不要把 `docs/` 全部读一遍。

先看这份索引，再按任务类型跳转。

## 当前状态

> Web 调研 -> 信息整理 -> Markdown 报告 -> artifact 输出
>
> 文件输入 -> 文件发现 -> 文件读取 -> Markdown 报告 -> artifact 输出

两个最小闭环均已完成。当前任务由真实宿主问题驱动。

## 最小阅读路径

1. 先读 `docs/README.md`
2. 再读 `docs/TODO.md` 中相关任务
3. 直接看代码
4. 只有必要时才补读其他文档

## 什么时候看哪份

- 做具体功能或修 bug：
  看 `docs/TODO.md`

- 判断优先级、阶段顺序、该不该做：
  看 `docs/LITE_EVOLUTION_PLAN.md`

- 判断代码该放哪、模块边界怎么收：
  看 `docs/LITE_ARCHITECTURE.md`

## 文档职责

- `docs/TODO.md`
  当前可执行任务、checkbox 状态、关联文件、完成标准

- `docs/TODO_ARCHIVE.md`
  已完成任务归档

- `docs/LITE_EVOLUTION_PLAN.md`
  计划索引，继续跳到 `docs/plan/`

- `docs/LITE_ARCHITECTURE.md`
  架构索引，继续跳到 `docs/architecture/`

## AI 更新规则

1. 完成具体任务后，先更新 `docs/TODO.md`
2. 已完成任务从 `docs/TODO.md` 移到 `docs/TODO_ARCHIVE.md`
3. 阶段顺序或优先级变了，再更新 `docs/LITE_EVOLUTION_PLAN.md`
4. 模块归属或目录边界变了，再更新 `docs/LITE_ARCHITECTURE.md`
5. 不要因为一次代码改动，把所有文档全部重写
