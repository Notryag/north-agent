# Code Execution Boundary

## Status

Proposed. North Agent 当前不包含代码执行工具或 Sandbox 实现。

## 目标闭环

第一版代码执行只服务文件分析中无法可靠手工完成的计算任务：

```text
upload:// input
  -> 复制或挂载为只读输入
  -> 受限 Python 执行
  -> workspace:// 中间文件与结构化执行结果
  -> output:// 最终报告
  -> present_files 返回 Artifact
```

它不是通用远程终端，也不允许 Agent 直接操作宿主文件系统。

## 最小契约

Harness 未来只定义产品无关的执行协议：

```python
class CodeExecutor(Protocol):
    async def execute(self, request: CodeExecutionRequest) -> CodeExecutionResult: ...
```

`CodeExecutionRequest` 至少包含：

- Python 源码
- 显式声明的 `upload://` 或 `workspace://` 输入
- thread/run 标识
- 超时、输出大小等宿主批准的限制

`CodeExecutionResult` 至少包含：

- 退出状态与耗时
- 截断后的 stdout/stderr
- 结构化错误类型
- 新增或修改的 `workspace://` 文件
- 可供后续工具读取的结果摘要

代码执行不会自动把文件加入 Artifact。最终用户文件仍必须写入 `output://`，再通过
`present_files` 显式返回。

## 职责边界

North Harness 负责：

- 执行请求和结果的数据契约
- 将宿主提供的 `CodeExecutor` 装配成 Agent 工具
- 把执行开始、结束、失败和资源用量转换为 Runtime Event
- 保持 resource URI、thread 和 Artifact 语义一致

宿主应用或执行基础设施负责：

- 身份、租户、授权和审计策略
- 容器、microVM 或远程执行服务的隔离
- CPU、内存、进程数、磁盘、时间和输出限制
- 网络策略、镜像维护、依赖白名单和漏洞修复
- 密钥隔离、数据保留和任务清理

## 安全不变量

- 默认禁用网络。
- 不向执行环境注入模型、数据库或宿主服务密钥。
- `upload://` 输入只读；只允许写入本次 thread 的 workspace。
- 拒绝绝对路径、路径穿越、Symlink 逃逸和宿主目录挂载。
- 执行必须有硬超时、内存限制、进程限制和输出上限。
- 客户端取消或 Run 终止时，宿主必须终止对应执行任务。
- 日志默认不记录完整文件内容、源码中的秘密或无限 stdout/stderr。

仅用 Python 子进程加 `subprocess` 参数限制不构成安全 Sandbox。处理不可信代码时必须使用
独立隔离边界。

## 第一版暂不做

- 任意 Shell 或宿主命令执行
- 在线安装 PyPI、apt 或系统依赖
- 默认开放互联网访问
- 多语言 Runtime
- 长驻进程、Notebook Kernel 或交互终端
- 跨 thread 共享可写工作区
- 自动把所有生成文件暴露为 Artifact
- 在 North 仓库内建设完整 Sandbox 调度平台

## 实现前决策门槛

只有满足以下条件才进入实现：

1. 至少一个真实宿主任务证明纯文件工具无法完成。
2. 已选定宿主提供的隔离执行器，并验证取消和资源回收。
3. Request/Result 与 Runtime Event 契约经过宿主集成评审。
4. 有路径逃逸、超时、输出膨胀、网络和密钥隔离测试方案。
