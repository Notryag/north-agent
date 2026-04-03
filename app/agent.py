from __future__ import annotations

from collections.abc import Sequence

from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware
from langchain.chat_models import init_chat_model

from .config import AppConfig
from .state import ThreadState


def create_chat_model(name: str, thinking_enabled: bool = False):
    """Create a chat model from a provider-prefixed or plain model name."""
    provider, separator, model_name = name.partition(":")
    kwargs = {"model": model_name, "model_provider": provider} if separator else {"model": name}

    # The flag stays in the public config surface even though the minimal app
    # does not apply provider-specific reasoning parameters yet.
    _ = thinking_enabled
    return init_chat_model(**kwargs)


def get_tools() -> list:
    """Return the default tool set for the minimal runtime."""
    return []


def get_middlewares() -> Sequence[AgentMiddleware]:
    """Return the default middleware chain for the minimal runtime."""
    return []


def build_agent(
    config: AppConfig,
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
        state_schema=ThreadState,
        checkpointer=checkpointer,
    )
