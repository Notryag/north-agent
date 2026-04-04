# DeerFlow Lite 演进计划

## 1. 计划原则

本计划建立在一个前提上：

> 架构总体方向不变，最终目标始终是简化版 DeerFlow；Web 调研只是当前阶段用于收敛实现的任务节点，不是产品分叉。

因此，计划中的每一步都应该同时满足两件事：

1. 对当前阶段的 Web 调研任务有帮助
2. 对长期 DeerFlow runtime 方向有复用价值

补充一条：

3. 对目录结构的演进，要尽量朝 `deer-flow` 的分层组织靠拢，而不是围绕临时任务随意长新模块

## 2. 总目标与阶段目标

### 最终目标

逐步形成一个轻量但方向正确的 DeerFlow runtime，具备这些核心能力：

- thread-based state
- tool-driven 多步执行
- artifact / 文件交付
- 可观察的事件流
- clarification / error recovery / loop protection
- 后续可扩展到文件分析、代码执行、报告生成、子代理协作

同时，工程结构也逐步朝 `deer-flow` 的核心分层靠近：

- `client`
- `agent/runtime`
- `state`
- `models`
- `agents/middlewares`
- `tools`
- `threads`
- `outputs`
- `config`

### 当前阶段目标

当前阶段聚焦一个最容易形成闭环的验证任务：

> Web 调研 -> 信息整理 -> 输出 Markdown 报告 -> 返回 artifact

这个任务只是一段推进路径，不改变总体目标。

## 3. 当前阶段的北极星闭环

当前阶段所有实现都围绕这个闭环推进：

```text
用户给出调研问题
  -> agent 调用 web_search
  -> agent 获取网页内容
  -> agent 归纳整理
  -> agent 写出 report.md
  -> agent 返回 artifact
```

如果某项改动无法帮助这个闭环更可靠地运行，优先级就应当下降。

## 4. 演进阶段

### Phase A：稳住当前 runtime 骨架

目标：

- 保证现有 client / runtime / state 结构稳定
- 明确哪些能力是真正为 DeerFlow 方向服务

重点：

1. 保持 `AppClient.chat()` / `AppClient.stream()` 稳定
2. 保持 `build_agent(...)` 是统一装配点
3. 保持 `runtime.py` 是工具 / middleware / checkpointer 的收敛点
4. 保持目录结构的演进朝最终目标分层靠拢

完成标准：

- 不再围绕“再加一个抽象层”发散
- 所有后续能力都从任务闭环出发

### Phase B：完成调研任务最小工具链

目标：

打通 Web 调研任务的最小工具闭环。

需要补齐：

1. `web_search`
2. `web_fetch` 或等价页面读取工具
3. `write_report`
4. `present_files` 真正联动 `artifacts`

完成标准：

- 用户输入调研问题
- agent 能调用搜索类工具
- 最终能生成 `report.md`
- `ThreadState.artifacts` 中有输出文件

### Phase C：把 runtime 保护做对

目标：

让这个系统从“能跑”变成“能持续跑”。

说明：

- demo 版 middleware 不应继续留在默认 runtime 中
- 只有在语义真正围绕工具失败、tool loop、clarification 恢复设计后，才应重新默认启用

要点：

1. `ToolErrorHandlingMiddleware`
   应真正围绕工具执行失败设计
2. `LoopDetectionMiddleware`
   应优先关注 tool call 循环，而不是单纯文本重复
3. `ClarificationMiddleware`
   应服务于任务中断与恢复，而不只是简单输入长度判断

完成标准：

- 工具失败不会整轮崩溃
- 重复工具循环可被截断
- 缺信息时能清晰地停下来等用户补充

### Phase D：完善 artifact 与线程上下文

目标：

让“生成报告文件”成为真正的一等能力。

要点：

1. 强化 `ThreadState`
   - `artifacts`
   - `thread_data`
   - `uploaded_files`
2. 让 `present_files` 写入状态，而不是只返回文本
3. 让线程路径模型和实际 runtime 接上

完成标准：

- 输出文件有稳定位置
- `stream()` / `chat()` 可携带 artifact 信息
- 后续文件分析、PPT 生成有可复用基础

### Phase E：从 Web 调研扩展到 DeerFlow 通用能力

这一步才开始往 DeerFlow 更完整的能力靠近：

1. 学术文献综述
2. 技术可行性分析
3. 文件分析
4. 报告 / 脚本 / PPT 生成
5. 更复杂的工作流
6. 必要时再考虑 sandbox、subagent、memory

这一步是扩展，不是重开新方向。

## 5. 目录结构演进原则

在实现顺序上，目录结构也要作为目标的一部分来约束代码增长。

原则如下：

1. 若某项能力未来显然属于 `models/`、`tools/`、`agents/middlewares/`、`threads/`、`outputs/`，就不要继续塞回顶层文件
2. 当前阶段可以先少量保留在单文件里，但一旦某类逻辑开始增长，就要迁移到其目标目录
3. 目录结构服务于 DeerFlow 总体方向，而不是当前临时任务

例如：

- `web_search` / `web_fetch` 应该进入 `app/tools/web/`
- `write_report` 应该进入 `app/tools/builtin/` 或 `app/outputs/`
- middleware 应该逐步收敛到 `app/agents/middlewares/`
- 模型创建应逐步迁移到 `app/models/`

## 6. 当前阶段最值得做的能力

围绕当前任务节点，建议优先级如下：

### 第一优先级

- `web_search`
- `web_fetch`
- `write_report`
- `present_files -> artifacts`

### 第二优先级

- tool error recovery
- tool loop protection
- clarification for missing info

### 第三优先级

- 线程路径与输出目录接入
- 更清晰的流式事件

### 暂缓

- sandbox
- memory
- title
- todo
- subagent
- 大而全工具体系

## 7. 判断一项工作该不该做的标准

后续如果你不确定某个改动该不该做，就用下面这三个问题筛选：

1. 这项改动是否帮助当前阶段的调研闭环跑通？
2. 这项改动是否对长期 DeerFlow runtime 方向有复用价值？
3. 这项改动是否会把项目带向一个与 DeerFlow 无关的分叉？
4. 这项改动是否符合最终目标目录结构，而不是临时把逻辑塞进错误位置？

如果第 1、2 条都成立，第 3 条不成立，就值得做。

## 8. 近期推荐改动批次

如果只做一轮最有价值的推进，建议按这个批次：

1. 引入 `web_search`
2. 引入 `web_fetch`
3. 新增 `write_report`
4. 改造 `present_files`，使其真正写入 `artifacts`
5. 让 `stream()` 输出工具事件
6. 修正 middleware，使其更贴近 DeerFlow runtime 语义

这一批做完，项目就会明显从“通用 agent demo”变成“DeerFlow 风格 runtime”。

## 9. 退出当前阶段的标准

当前阶段完成，不是指“调研功能做完”，而是指：

1. DeerFlow 总体架构方向仍然清晰
2. Web 调研闭环已跑通
3. artifact 输出已打通
4. tool/runtime 保护已形成基础能力
5. 下一阶段已经可以自然扩到文件分析、代码执行、报告生成等 DeerFlow 典型任务

## 10. 结论

这份计划的核心不是“把 lite 做成调研系统”，而是：

> 用调研这个最容易闭环的任务节点，去稳步逼近 DeerFlow 的核心 runtime。

后续实现始终要记住：

- 总方向不变
- 架构不分叉
- 当前任务只是推进节点
