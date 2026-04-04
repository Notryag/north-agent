# Roadmap

## 演进阶段

### Phase A

目标：

- 保证现有 client / runtime / state 结构稳定
- 明确哪些能力是真正为 DeerFlow 方向服务

完成标准：

- 不再围绕“再加一个抽象层”发散
- 所有后续能力都从任务闭环出发

### Phase B

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

### Phase C

目标：

让这个系统从“能跑”变成“能持续跑”。

说明：

- demo 版 middleware 不应继续留在默认 runtime 中
- 只有在语义真正围绕工具失败、tool loop、clarification 恢复设计后，才应重新默认启用

完成标准：

- 工具失败不会整轮崩溃
- 重复工具循环可被截断
- 缺信息时能清晰地停下来等用户补充

### Phase D

目标：

让“生成报告文件”成为真正的一等能力。

完成标准：

- 输出文件有稳定位置
- `stream()` / `chat()` 可携带 artifact 信息
- 后续文件分析、PPT 生成有可复用基础

### Phase E

这一步才开始往 DeerFlow 更完整的能力靠近：

1. 学术文献综述
2. 技术可行性分析
3. 文件分析
4. 报告 / 脚本 / PPT 生成
5. 更复杂的工作流
6. 必要时再考虑 sandbox、subagent、memory

## 当前优先级

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

## 近期推荐改动批次

1. 引入 `web_search`
2. 引入 `web_fetch`
3. 新增 `write_report`
4. 改造 `present_files`，使其真正写入 `artifacts`
5. 让 `stream()` 输出工具事件
6. 修正 middleware，使其更贴近 DeerFlow runtime 语义

## 退出当前阶段的标准

1. DeerFlow 总体架构方向仍然清晰
2. Web 调研闭环已跑通
3. artifact 输出已打通
4. tool/runtime 保护已形成基础能力
5. 下一阶段已经可以自然扩到文件分析、代码执行、报告生成等 DeerFlow 典型任务
