from __future__ import annotations

from collections.abc import Callable
from typing import Any


async def invoke_agent_once(
    *,
    agent_factory: Callable[[], Any],
    graph_input: dict[str, Any],
    config: Any | None = None,
    context: dict[str, Any] | None = None,
) -> Any:
    """Invoke an agent once, preferring async execution when available.

    This helper is intentionally product-agnostic. Callers own persistence,
    authorization, cost controls, and conversion of the returned state into
    their domain-specific response format.
    """

    agent = agent_factory()
    ainvoke = getattr(agent, "ainvoke", None)
    if callable(ainvoke):
        return await ainvoke(graph_input, config=config, context=context)

    invoke = getattr(agent, "invoke", None)
    if callable(invoke):
        return invoke(graph_input, config=config, context=context)

    raise TypeError("Agent does not expose ainvoke or invoke")
