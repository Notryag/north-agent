# AGENT Guide

这份文件给后续 AI 一个最小、稳定的工作入口。

默认先读这份文件，不要先把整个 `docs/` 目录读一遍。

## 当前主线

当前阶段的北极星闭环是：

> 文件输入 -> 文件发现 -> 文件读取 -> Markdown 报告 -> artifact 输出

上一阶段的 Web 调研闭环已经打通；当前实现优先服务文件分析闭环，并保持 Web 调研能力稳定。

## 最小阅读路径

1. 先读 `AGENT.md`
2. 再读 `docs/TODO.md` 中与你任务相关的部分
3. 直接看代码
4. 只有当任务涉及优先级或模块边界时，才补读 `docs/plan/` 或 `docs/architecture/`

## 当前代码现实

- 当前真正存在的 agent 装配文件是 `app/agent.py`
- 当前已经有 `app/tools/builtin/`、`app/outputs/`、`app/threads/`、`app/skills/`
- 当前已经有 `app/agents/middlewares/`
- 已完成任务已归档到 `docs/TODO_ARCHIVE.md`
- 不要假设 repo 里已经有完整 DeerFlow 目录结构

## 当前 prompt 现状

- 当前 runtime system prompt 来自 `app/config.py`
- 当前默认值是：`You are a helpful assistant.`
- `app/agent.py` 会把 `config.system_prompt` 传给 `create_agent(...)`
- 当前没有独立 prompt 文件；任务工作流主要通过本地 `skills/*/SKILL.md` 按需加载

## 当前最重要的 active work

优先看 `docs/TODO.md` 的这些任务：

- `T13` 端到端 smoke test
- `T15` 文件分析 skill 端到端说明
- `T16` 代码执行前置边界

## 文档分工

- `docs/TODO.md`
  当前任务、关联文件、完成标准

- `docs/TODO_ARCHIVE.md`
  已完成任务归档

- `docs/LITE_EVOLUTION_PLAN.md`
  计划索引，继续跳到 `docs/plan/`

- `docs/LITE_ARCHITECTURE.md`
  架构索引，继续跳到 `docs/architecture/`

## 工作规则

- 做任何需求前，先确认它放在当前项目架构里是否优雅：职责边界是否清楚、是否符合现有目录分工、是否会让 API / runtime / agent / tool 混在一起。若架构不优雅，先收敛方案再动代码。
- `TODO` 主体只关注当前待做事项
- 已完成事项移动到 `docs/TODO_ARCHIVE.md`
- 如果改动改变优先级，更新 `docs/plan/`
- 如果改动改变模块边界，更新 `docs/architecture/`
- 如果后续引入独立 prompt 文件或 prompt 目录，要先回写本文件
- 平常的小改动不要运行测试；默认做差异审查和必要的静态检查。只有共享 runtime 契约、持久化/并发/幂等、重要故障修复、较大功能切片完成、发布或部署批次等关键时刻，才运行最小受影响测试；全量和真实模型测试只用于高风险或发布级验证。
