# Roadmap

## 已完成基础

North Agent 已完成以下最小能力：

1. Agent 装配、同步聊天、流式事件和独立 Run 生命周期
2. 工具错误恢复、循环保护和结构化澄清
3. Web 搜索、页面读取、Markdown 报告和 Artifact 闭环
4. 文件上传、发现、读取、报告生成和 Artifact 闭环
5. Skill catalog 与正文按需加载
6. Memory、SQLite、PostgreSQL Checkpointer
7. Runtime Event、Token 用量归一化和上下文摘要
8. Harness/App 分层、公开 API 和宿主路径注入

这些能力应通过真实宿主集成继续验证，不再以增加抽象层作为独立目标。

## 当前阶段

当前没有预设功能开发任务。新工作应从真实宿主应用暴露的问题进入，并优先属于以下类型：

- 公开 Runtime 契约的缺陷或缺口
- 持久化、取消、并发和可观测性的真实故障
- Web 调研或文件分析闭环中的可复现失败
- 已有能力在 Dayboard 等宿主中的集成问题

## 代码执行决策门槛

代码执行用于补足文件分析中的受限计算能力，不是构建通用终端。实现前必须：

1. 至少一个真实宿主任务证明纯文件工具无法完成
2. 选定由宿主提供的隔离执行器
3. 评审 `CodeExecutionRequest`、`CodeExecutionResult` 和 Runtime Event 契约
4. 验证取消、超时、路径隔离、网络隔离、密钥隔离和资源回收
5. 明确输入 Resource URI、workspace 中间结果和 output Artifact 的生命周期

条件满足后，第一版只实现显式输入、受限 Python 和受控输出。详细边界见
`docs/architecture/code-execution-boundary.md`。

## 暂缓能力

- 完整 Sandbox 平台
- 长期 Memory 产品模型
- MCP 接入面
- Vision
- Title/Todo Middleware
- Subagent
- 大而全工具注册系统

这些能力只有在宿主任务能够证明收益，并且现有 Runtime 边界无法优雅支持时才进入 Active TODO。

## 演进原则

1. 从可验证的任务闭环推动 Runtime，而不是从参考项目复制功能清单
2. 保持 `app -> north` 单向依赖，不恢复双实现或兼容层
3. Harness 定义产品无关契约；宿主拥有身份、权限、数据、计费和基础设施
4. 新增顶层 API、持久化协议或执行能力前，先更新对应架构边界
5. 测试投入随风险增长；真实模型和全量测试只用于高风险或发布批次
