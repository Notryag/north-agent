from __future__ import annotations

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model

from .config import AppConfig
from .runtime import (
    get_checkpointer as resolve_checkpointer,
    get_middlewares as resolve_middlewares,
    get_state_schema,
    get_tools as resolve_tools,
)


def create_chat_model(name: str, thinking_enabled: bool = False):
    """Create a chat model from a provider-prefixed or plain model name."""
    provider, separator, model_name = name.partition(":")
    kwargs = {"model": model_name, "model_provider": provider} if separator else {"model": name}

    # The flag stays in the public config surface even though the minimal app
    # does not apply provider-specific reasoning parameters yet.
    _ = thinking_enabled
    return init_chat_model(**kwargs)

def build_agent(
    config: AppConfig,
    *,
    tools: list | None = None,
    middlewares=None,
    checkpointer=None,
):
    model = create_chat_model(
        name=config.model_name,
        thinking_enabled=config.thinking_enabled,
    )

    return create_agent(
        model=model,
        tools=tools if tools is not None else resolve_tools(config),
        middleware=middlewares if middlewares is not None else resolve_middlewares(config),
        system_prompt=config.system_prompt,
        state_schema=get_state_schema(),
        checkpointer=checkpointer if checkpointer is not None else resolve_checkpointer(config),
    )
