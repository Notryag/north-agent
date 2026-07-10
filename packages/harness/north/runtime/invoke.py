from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .events import RuntimeEventSink, RuntimeJournal


async def invoke_agent_once(
    *,
    agent_factory: Callable[[], Any],
    graph_input: dict[str, Any],
    config: Any | None = None,
    context: dict[str, Any] | None = None,
    event_sink: RuntimeEventSink | None = None,
) -> Any:
    """Invoke an agent once, preferring async execution when available.

    This helper is intentionally product-agnostic. Callers own persistence,
    authorization, cost controls, and conversion of the returned state into
    their domain-specific response format.
    """

    agent = agent_factory()
    resolved_config = _with_runtime_journal(config, event_sink)
    ainvoke = getattr(agent, "ainvoke", None)
    if callable(ainvoke):
        return await ainvoke(graph_input, config=resolved_config, context=context)

    invoke = getattr(agent, "invoke", None)
    if callable(invoke):
        return invoke(graph_input, config=resolved_config, context=context)

    raise TypeError("Agent does not expose ainvoke or invoke")


def _with_runtime_journal(config: Any | None, event_sink: RuntimeEventSink | None) -> Any | None:
    if event_sink is None:
        return config
    if config is not None and not isinstance(config, dict):
        raise TypeError("event_sink requires config to be a dict or None")
    resolved = dict(config or {})
    callbacks = list(resolved.get("callbacks") or [])
    callbacks.append(RuntimeJournal(event_sink))
    resolved["callbacks"] = callbacks
    return resolved
