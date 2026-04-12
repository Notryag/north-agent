# DeerFlow Lite

这是一个正在演进中的简化版 DeerFlow runtime。

需要特别说明两点：

1. **最终目标不变**
   项目最终仍然是朝 DeerFlow 的核心方向推进，而不是做一个独立的调研系统。
2. **当前阶段有一个收敛任务**
   当前阶段优先围绕 `Web 调研 -> Markdown 报告 -> artifact 输出` 这个任务闭环推进，用它来逼出 DeerFlow 最关键的 runtime 能力。

也就是说：

- DeerFlow 是总体方向
- Web 调研只是当前阶段的推进节点，不是分叉

## 当前实现

项目已经不是纯设计草案，而是一个可运行的 lite runtime 骨架。

核心结构：

```text
app/
├── __init__.py
├── __main__.py
├── agent.py
├── cli.py
├── client.py
├── config.py
└── state.py
main.py
.env
.env.example
tests/
```

其中：

- `app/config.py`
  负责从项目根目录 `.env` 加载配置
- `app/state.py`
  定义最小 `ThreadState`
- `app/agent.py`
  统一创建 LangChain agent
- `app/client.py`
  暴露 `AppClient.chat()` 和 `AppClient.stream()`
- `app/cli.py`
  提供命令行入口
- `main.py`
  提供最直接的运行方式

## 最小架构

当前运行链路是：

```text
user
  -> main.py / python -m app
  -> AppClient
  -> build_agent(...)
  -> create_agent(...)
  -> model
  -> final answer
```

当前版本的重点不是“功能已经完整”，而是：

- 对外接口已经稳定
- runtime 组装点已经形成
- 后续可以围绕阶段任务持续补能力，而不需要推翻架构

## 配置方式

项目使用环境变量配置，默认从根目录 `.env` 读取。

示例见 [.env.example](./.env.example)：

```env
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
APP_MODEL_NAME=openai:gpt-4o-mini
APP_THINKING_ENABLED=false
APP_SYSTEM_PROMPT=You are a concise assistant.
APP_RECURSION_LIMIT=50
LANGSMITH_TRACING=false
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_PROJECT=deerflow-lite
```

如果你使用 OpenRouter，例如 `stepfun/step-3.5-flash:free`，可以写成：

```env
OPENAI_API_KEY=your_openrouter_api_key
OPENAI_BASE_URL=https://openrouter.ai/api/v1
APP_MODEL_NAME=openai:stepfun/step-3.5-flash:free
APP_THINKING_ENABLED=false
APP_SYSTEM_PROMPT=You are a concise assistant.
APP_RECURSION_LIMIT=50
LANGSMITH_TRACING=false
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_PROJECT=deerflow-lite
```

## LangSmith

`LangSmith` 主要用来做三类事情：

- 观测 agent / chain / tool 的完整调用链
- 调试每一步输入输出、报错和耗时
- 做 prompt / workflow 的评估与回归对比

这个项目可以直接加，而且接法很轻。当前依赖栈里已经带上了 `langsmith`，不需要额外改 runtime 才能开始记录 trace；只要在 `.env` 打开 LangSmith 环境变量，LangChain / LangGraph 就会自动上报。

最小配置示例：

```env
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_PROJECT=deerflow-lite
```

然后正常运行：

```powershell
uv run -m app "hi"
```

如果你不想开 tracing，就保持 `LANGSMITH_TRACING=false` 或者不配这些变量。

## 安装依赖

```powershell
python -m pip install -e .[dev]
```

## 运行方式

最直接的命令是：

```powershell
python main.py "用一句话解释什么是 DeerFlow"
```

也可以通过模块入口运行：

```powershell
python -m app "用一句话解释什么是 DeerFlow"
```

如果要看流式输出：

```powershell
python -m app --stream "用一句话解释什么是 DeerFlow"
```

如果要查看帮助：

```powershell
python -m app --help
```

## 代码示例

```python
from app.client import AppClient
from app.config import AppConfig


config = AppConfig.from_env()
config.validate()

client = AppClient(config)

response = client.chat("用一句话解释什么是 DeerFlow")
print(response)
```

## 已实现的能力

当前已经有：

- 基于 `.env` 的配置加载
- 统一的 `build_agent()` 装配点
- `AppClient.chat()`
- `AppClient.stream()`
- `runtime.py` 统一解析 tools / middlewares / checkpointer
- 最小 `ThreadState`
- 基础 checkpointer 接口
- 最小工具注册骨架
- 线程路径模型
- CLI 入口
- 基础测试

## 当前阶段真正缺少的能力

如果把当前阶段任务定义为“Web 调研 -> Markdown 报告 -> artifact 输出”，现在最缺的不是更多抽象，而是这些闭环能力：

- `web_search`
- `web_fetch`
- `write_report`
- `present_files` 与 `artifacts` 真正联动
- 围绕真实工具语义重建 runtime middleware
- 更完整的 stream 事件

## 下一步建议

建议不要再继续泛化抽象，而是围绕当前阶段任务闭环推进：

1. 引入 `web_search`
2. 引入 `web_fetch`
3. 新增 `write_report`
4. 让 `present_files` 真正写入 `artifacts`
5. 让 `stream()` 能清晰输出工具调用与工具结果
6. 把当前 middleware 调整得更贴近 DeerFlow runtime 语义

等这个闭环稳定后，再往 DeerFlow 的更完整能力扩展：

- 学术综述
- 技术可行性分析
- 文件分析
- 报告 / PPT / 脚本生成
- 更复杂的工作流
- 最后再考虑 sandbox / subagent / memory

## 结论

一句话总结当前状态：

> DeerFlow Lite 的总体方向始终是 DeerFlow，本阶段只是先用 Web 调研这个最容易闭环的任务，去推动 runtime 真正长成 DeerFlow 风格的系统。
