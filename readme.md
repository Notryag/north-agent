# Minimal DeerFlow Design

本文给出一个“最简单、能跑、零工具、零 middleware、但保留扩展性”的 DeerFlow 最小设计。

目标不是复刻当前 DeerFlow 的全部能力，而是抽出最小骨架，让你先跑起来，再逐步加：

- tools
- middleware
- checkpointer
- 自定义 state
- 多 agent / subagent

## 1. 设计目标

约束条件：

1. 能跑
2. 代码尽量少
3. 默认没有工具
4. 默认没有 middleware
5. 后续扩展时不要推翻重写

因此最小方案只保留 4 个核心概念：

1. `Config`
   只描述模型和可选运行参数
2. `State`
   至少要有 `messages`
3. `Agent Factory`
   统一负责创建 agent
4. `Client`
   对外暴露 `chat()` / `stream()`

## 2. 最小架构

最小版本建议只保留三层：

```text
user
  -> MinimalDeerFlowClient
  -> build_agent(...)
  -> create_agent(...)
  -> model
  -> final answer
```

因为：

- 没有 tools，所以没有 `model -> tools -> model` 循环
- 没有 middleware，所以没有运行期拦截
- graph 依然是 LangChain / LangGraph 的 agent graph
- 后续一旦加 tools / middleware，不用改外部 client 形状

## 3. 最小目录结构

建议单独做一个极简包，目录可以是：

```text
minimal_deerflow/
├── __init__.py
├── config.py
├── state.py
├── agent.py
└── client.py
```

如果你想再少一点，甚至可以只做两个文件：

```text
minimal_deerflow/
├── agent.py
└── client.py
```

但为了扩展性，建议保留 `config.py` 和 `state.py`。

## 4. 推荐的最小代码设计

### 4.1 `config.py`

```python
from dataclasses import dataclass


@dataclass
class MinimalDeerFlowConfig:
    model_name: str
    thinking_enabled: bool = False
    system_prompt: str = "You are a helpful assistant."
    recursion_limit: int = 50
```

说明：

- 只保留最必要的配置
- 不耦合工具、middleware、存储
- 后续可以继续加：
  - `subagent_enabled`
  - `reasoning_effort`
  - `checkpointer`
  - `tools_provider`
  - `middleware_provider`

### 4.2 `state.py`

```python
from langchain.agents import AgentState


class MinimalThreadState(AgentState):
    """最小状态，直接继承 AgentState。"""

    pass
```

说明：

- 最小版本不扩展任何字段
- 因为 `AgentState` 已经包含核心的 `messages`
- 后续如果要加：
  - `title`
  - `artifacts`
  - `thread_data`
  - `todos`
  只需要在这里扩展，不影响 client API

### 4.3 `agent.py`

```python
from collections.abc import Sequence

from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware

from deerflow.models import create_chat_model

from .config import MinimalDeerFlowConfig
from .state import MinimalThreadState


def get_tools() -> list:
    """默认无工具，后续可在这里扩展。"""
    return []


def get_middlewares() -> Sequence[AgentMiddleware]:
    """默认无 middleware，后续可在这里扩展。"""
    return []


def build_agent(
    config: MinimalDeerFlowConfig,
    *,
    tools: list | None = None,
    middlewares: Sequence[AgentMiddleware] | None = None,
    checkpointer=None,
):
    model = create_chat_model(
        name=config.model_name,
        thinking_enabled=config.thinking_enabled,
    )

    return create_agent(
        model=model,
        tools=tools if tools is not None else get_tools(),
        middleware=middlewares if middlewares is not None else get_middlewares(),
        system_prompt=config.system_prompt,
        state_schema=MinimalThreadState,
        checkpointer=checkpointer,
    )
```

说明：

- 这就是最核心的可扩展点
- 当前默认：
  - `tools=[]`
  - `middleware=[]`
- 以后要扩展时有三种方式：
  1. 改 `get_tools()` / `get_middlewares()`
  2. 调 `build_agent(..., tools=..., middlewares=...)`
  3. 再往外封一层 provider / plugin registry

这能保证现在代码最少，同时以后不会卡死。

### 4.4 `client.py`

```python
import uuid
from collections.abc import Generator
from dataclasses import dataclass, field
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig

from .agent import build_agent
from .config import MinimalDeerFlowConfig


@dataclass
class StreamEvent:
    type: str
    data: dict[str, Any] = field(default_factory=dict)


class MinimalDeerFlowClient:
    def __init__(self, config: MinimalDeerFlowConfig, *, checkpointer=None):
        self.config = config
        self.checkpointer = checkpointer
        self._agent = None

    def _get_agent(self):
        if self._agent is None:
            self._agent = build_agent(self.config, checkpointer=self.checkpointer)
        return self._agent

    def _get_runnable_config(self, thread_id: str) -> RunnableConfig:
        return RunnableConfig(
            configurable={"thread_id": thread_id},
            recursion_limit=self.config.recursion_limit,
        )

    def stream(self, message: str, *, thread_id: str | None = None) -> Generator[StreamEvent, None, None]:
        if thread_id is None:
            thread_id = str(uuid.uuid4())

        agent = self._get_agent()
        config = self._get_runnable_config(thread_id)
        state = {"messages": [HumanMessage(content=message)]}

        for chunk in agent.stream(state, config=config, context={"thread_id": thread_id}, stream_mode="values"):
            messages = chunk.get("messages", [])
            for msg in messages:
                if isinstance(msg, AIMessage):
                    if isinstance(msg.content, str) and msg.content:
                        yield StreamEvent(
                            type="message",
                            data={"role": "ai", "content": msg.content},
                        )

            yield StreamEvent(type="values", data=chunk)

    def chat(self, message: str, *, thread_id: str | None = None) -> str:
        last_text = ""
        for event in self.stream(message, thread_id=thread_id):
            if event.type == "message":
                last_text = event.data["content"]
        return last_text
```

说明：

- 这是最小 client
- 仍然保留 DeerFlow 风格的：
  - `chat()`
  - `stream()`
  - `thread_id`
  - `RunnableConfig`
- 所以以后往上长，不需要改用户使用方式

## 5. 最小可运行示例

```python
from minimal_deerflow.client import MinimalDeerFlowClient
from minimal_deerflow.config import MinimalDeerFlowConfig


config = MinimalDeerFlowConfig(
    model_name="openai:gpt-4o-mini",
    system_prompt="You are a concise assistant.",
)

client = MinimalDeerFlowClient(config)

response = client.chat("用一句话解释什么是 DeerFlow")
print(response)
```

## 6. 为什么这个方案最适合“先跑起来”

### 6.1 保留了未来 DeerFlow 的主要生长点

虽然现在什么都没有，但这几个扩展位都还在：

- `state_schema`
- `checkpointer`
- `tools`
- `middlewares`
- `RunnableConfig`
- `thread_id`

所以以后逐步升级时不会出现“接口推翻重写”。

### 6.2 当前复杂度极低

最小实现里真正必要的只有：

1. 一个 config
2. 一个 state
3. 一个 `build_agent()`
4. 一个 client

这已经足够支撑：

- 单轮问答
- 流式响应
- 可选线程 id
- 可选未来多轮上下文

### 6.3 不提前引入 DeerFlow 特有工程复杂度

最小版先不做：

- sandbox
- 文件上传
- artifacts
- memory
- title
- todo
- clarification
- subagent

这些功能都可以作为第二阶段叠加进去。

## 7. 后续扩展顺序建议

如果从这个最小版逐步长成完整 DeerFlow，建议顺序是：

1. 加 checkpointer
   先支持真正多轮对话

2. 加 tools
   先加最简单的同步工具

3. 加一个基础 middleware
   比如 tool error handling

4. 扩展 `State`
   增加 `artifacts`、`title`、`thread_data`

5. 加 uploads / sandbox
   这时才进入 DeerFlow 的工程化阶段

6. 加 subagent
   这是更高阶能力，没必要在最小版里提前设计过多

## 8. 一个更稳的扩展版接口

如果你担心以后 `get_tools()` / `get_middlewares()` 不够灵活，可以把它们改成 provider 风格，但仍然保持极简：

```python
from collections.abc import Sequence
from langchain.agents.middleware import AgentMiddleware


class MinimalRuntimeProvider:
    def get_tools(self) -> list:
        return []

    def get_middlewares(self) -> Sequence[AgentMiddleware]:
        return []
```

然后在 `build_agent()` 中注入：

```python
def build_agent(config, provider=None, checkpointer=None):
    provider = provider or MinimalRuntimeProvider()
    ...
    return create_agent(
        model=model,
        tools=provider.get_tools(),
        middleware=provider.get_middlewares(),
        ...
    )
```

这样未来可以很自然地长成：

- `DefaultRuntimeProvider`
- `SandboxRuntimeProvider`
- `ResearchRuntimeProvider`
- `CodingRuntimeProvider`

但第一版不一定要上这个抽象。

## 9. 我的建议

如果你的目标真的是“最简单最简单，能跑就行”，那就按下面这个标准收敛：

### 第一版必须有

- `MinimalDeerFlowConfig`
- `MinimalThreadState`
- `build_agent()`
- `MinimalDeerFlowClient.chat()`
- `MinimalDeerFlowClient.stream()`

### 第一版不要有

- tool registry
- middleware chain builder
- sandbox
- 上传文件
- memory
- title
- subagent
- 自定义事件协议

### 第一版预留但不启用

- `checkpointer`
- `tools`
- `middlewares`
- 自定义 state 字段

## 10. 最终结论

最小 DeerFlow 不需要先实现“DeerFlow 的全部特性”，只需要保留 DeerFlow 最重要的骨架：

1. `client` 作为统一入口
2. `build_agent()` 作为统一装配点
3. `state_schema` 作为共享状态入口
4. `tools` / `middlewares` 作为未来扩展槽位

一句话版本：

> 最小 DeerFlow = 一个薄 client + 一个薄 agent factory + 一个最小 state + 一个最小 config，默认 tools/middleware 全空，但函数签名里把扩展口留出来。

如果你要继续往前走，下一步最值得做的不是加更多抽象，而是把这份设计直接落成一个 `minimal_deerflow` demo 包，控制在 100 行到 150 行核心代码内。
