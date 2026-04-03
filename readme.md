# DeerFlow Lite

这是一个已经落地的最小版 DeerFlow demo。

当前目标不是复刻完整 DeerFlow，而是保留最核心的骨架，让项目先跑起来：

- 环境变量驱动配置
- 最小 `AgentState`
- 统一的 agent factory
- 对外 `chat()` / `stream()` client
- 一个可直接执行的 CLI 入口

还没有实现的部分保留为后续扩展：

- tools
- middleware
- checkpointer
- 自定义 state 字段
- subagent

## 当前实现

项目现在已经不是设计草案，而是一个可以直接运行的最小应用。

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

这个版本默认：

- `tools=[]`
- `middleware=[]`
- `state` 只依赖 `messages`

所以复杂度很低，但外部使用方式已经固定下来，后面继续加功能时不需要推翻接口。

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
```

如果你使用 OpenRouter，例如 `stepfun/step-3.5-flash:free`，可以写成：

```env
OPENAI_API_KEY=your_openrouter_api_key
OPENAI_BASE_URL=https://openrouter.ai/api/v1
APP_MODEL_NAME=openai:stepfun/step-3.5-flash:free
APP_THINKING_ENABLED=false
APP_SYSTEM_PROMPT=You are a concise assistant.
APP_RECURSION_LIMIT=50
```

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
- 最小 `ThreadState`
- `build_agent()` 统一装配
- `AppClient.chat()`
- `AppClient.stream()`
- CLI 入口
- 基础 smoke tests

## 尚未实现的能力

当前还没有做：

- checkpointer 持久化
- tools 注入和示例工具
- middleware 链
- 扩展 state 字段
- 上传、sandbox、memory、title、todo
- subagent

## 下一步建议

如果继续往前走，推荐顺序是：

1. 加 `checkpointer`
   先支持真正多轮对话

2. 加 `tools`
   先接一个最简单的同步工具

3. 加一个基础 middleware
   比如 tool error handling

4. 扩展 `ThreadState`
   增加 `artifacts`、`title`、`thread_data`

5. 再考虑 sandbox / uploads / subagent

## 结论

这个仓库现在已经完成了“最小可运行骨架”阶段，不再需要把 `config`、`state`、`agent`、`client` 当作待设计项。

一句话版本：

> DeerFlow Lite = 一个薄 CLI + 一个薄 client + 一个薄 agent factory + 一个最小 state + 一组环境变量配置。
