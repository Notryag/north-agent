from __future__ import annotations

from collections.abc import Sequence

from north.agent import _supports_tool_binding

from .config import AppConfig
from .runtime import (
    get_checkpointer as resolve_checkpointer,
    get_middlewares as resolve_middlewares,
    get_skills as resolve_skills,
    get_state_schema,
    get_system_prompt as resolve_system_prompt,
    get_tools as resolve_tools,
)
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model


def create_chat_model(name: str, thinking_enabled: bool = False):
    """Create a chat model from a provider-prefixed or plain model name."""
    provider, separator, model_name = name.partition(":")
    if separator:
        kwargs = {"model": model_name, "model_provider": provider}
    else:
        # Treat bare model names as OpenAI-compatible by default so providers
        # behind OPENAI_BASE_URL (DashScope, OpenRouter-compatible gateways, etc.)
        # work without forcing a prefix in APP_MODEL_NAME.
        kwargs = {"model": name, "model_provider": "openai"}

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
    skills: Sequence[str] | None = None,
):
    model = create_chat_model(
        name=config.model_name,
        thinking_enabled=config.thinking_enabled,
    )
    resolved_skills = resolve_skills(config, skill_names=skills)
    resolved_tools = tools if tools is not None else resolve_tools(config, skills=resolved_skills)
    if not _supports_tool_binding(model):
        resolved_tools = []

    return create_agent(
        model=model,
        tools=resolved_tools,
        middleware=middlewares if middlewares is not None else resolve_middlewares(config),
        system_prompt=resolve_system_prompt(config, skills=resolved_skills),
        state_schema=get_state_schema(),
        checkpointer=checkpointer if checkpointer is not None else resolve_checkpointer(config),
    )
