# AGENT Guide

这份文件给后续 AI 一个最小、稳定的工作入口。

默认先读这份文件，不要先把整个 `docs/` 目录读一遍。

## 当前主线

当前阶段的北极星闭环是：

> Web 调研 -> 信息整理 -> Markdown 报告 -> artifact 输出

所有实现优先服务这个闭环。

## 最小阅读路径

1. 先读 `AGENT.md`
2. 再读 `docs/TODO.md` 中与你任务相关的部分
3. 直接看代码
4. 只有当任务涉及优先级或模块边界时，才补读 `docs/plan/` 或 `docs/architecture/`

## 当前代码现实

- 当前真正存在的 agent 装配文件是 `app/agent.py`
- 当前已经有 `app/tools/web/` 和 `app/outputs/`
- 当前还没有 `app/agents/` 目录
- `docs/TODO.md` 中的 `T8` 是未来重建 middleware 时才会创建 `app/agents/middlewares/`
- 不要假设 repo 里已经有完整 DeerFlow 目录结构

## 当前 prompt 现状

- 当前 runtime system prompt 来自 `app/config.py`
- 当前默认值是：`You are a helpful assistant.`
- `app/agent.py` 会把 `config.system_prompt` 传给 `create_agent(...)`
- 这说明：现在还没有独立的 prompt 文件，也还没有真正对齐 DeerFlow Lite 当前阶段目标的专用 prompt

## 当前最重要的 active work

优先看 `docs/TODO.md` 的这些任务：

- `T4` `present_files -> artifacts`
- `T5` `stream()` 事件协议
- `T6` 线程输出链路
- `T7` `ThreadState` 更新约定
- `T8` runtime middleware 重建

## 文档分工

- `docs/TODO.md`
  当前任务、关联文件、完成标准

- `docs/LITE_EVOLUTION_PLAN.md`
  计划索引，继续跳到 `docs/plan/`

- `docs/LITE_ARCHITECTURE.md`
  架构索引，继续跳到 `docs/architecture/`

## 工作规则

- `TODO` 主体只关注当前待做事项
- 已完成事项通常不保留在 `docs/TODO.md` 主体
- 如果改动改变优先级，更新 `docs/plan/`
- 如果改动改变模块边界，更新 `docs/architecture/`
- 如果后续引入独立 prompt 文件或 prompt 目录，要先回写本文件
