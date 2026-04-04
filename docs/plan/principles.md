# Plan Principles

## 核心前提

> 架构总体方向不变，最终目标始终是简化版 DeerFlow；Web 调研只是当前阶段用于收敛实现的任务节点，不是产品分叉。

## 计划原则

每一步都应该同时满足：

1. 对当前阶段的 Web 调研任务有帮助
2. 对长期 DeerFlow runtime 方向有复用价值
3. 对目录结构的演进，应朝 `deer-flow` 的分层组织靠拢，而不是围绕临时任务随意长新模块

## 总目标

逐步形成一个轻量但方向正确的 DeerFlow runtime，具备这些核心能力：

- thread-based state
- tool-driven 多步执行
- artifact / 文件交付
- 可观察的事件流
- clarification / error recovery / loop protection
- 后续可扩展到文件分析、代码执行、报告生成、子代理协作

同时，工程结构逐步朝这些分层靠近：

- `client`
- `agent/runtime`
- `state`
- `models`
- `agents/middlewares`
- `tools`
- `threads`
- `outputs`
- `config`

## 当前阶段目标

当前阶段聚焦一个最容易形成闭环的验证任务：

> Web 调研 -> 信息整理 -> 输出 Markdown 报告 -> 返回 artifact

## 北极星闭环

```text
用户给出调研问题
  -> agent 调用 web_search
  -> agent 获取网页内容
  -> agent 归纳整理
  -> agent 写出 report.md
  -> agent 返回 artifact
```

如果某项改动无法帮助这个闭环更可靠地运行，优先级就应当下降。

## 判断一项工作该不该做

如果你不确定某个改动是否值得做，用下面四个问题筛选：

1. 这项改动是否帮助当前阶段的调研闭环跑通？
2. 这项改动是否对长期 DeerFlow runtime 方向有复用价值？
3. 这项改动是否会把项目带向一个与 DeerFlow 无关的分叉？
4. 这项改动是否符合最终目标目录结构，而不是临时把逻辑塞进错误位置？

通常第 1、2 条成立，第 3 条不成立，这项工作就值得做。
