from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .events import RuntimeEventSink, RuntimeJournal
from .serialization import serialize_lc_object


@dataclass(frozen=True, slots=True)
class RuntimeStreamEvent:
    """One product-neutral chunk emitted by an agent graph stream."""

    mode: str
    data: Any
    namespace: tuple[str, ...] = ()


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
    resolved_config = with_runtime_journal(config, event_sink)
    ainvoke = getattr(agent, "ainvoke", None)
    if callable(ainvoke):
        return await ainvoke(graph_input, config=resolved_config, context=context)

    invoke = getattr(agent, "invoke", None)
    if callable(invoke):
        return invoke(graph_input, config=resolved_config, context=context)

    raise TypeError("Agent does not expose ainvoke or invoke")


def normalize_stream_chunk(
    chunk: Any,
    requested_modes: tuple[str, ...],
) -> RuntimeStreamEvent:
    namespace: tuple[str, ...] = ()
    mode: str
    data: Any

    if (
        isinstance(chunk, tuple)
        and len(chunk) == 3
        and isinstance(chunk[1], str)
        and chunk[1] in requested_modes
    ):
        raw_namespace, mode, data = chunk
        if isinstance(raw_namespace, tuple):
            namespace = tuple(str(part) for part in raw_namespace)
        elif isinstance(raw_namespace, str) and raw_namespace:
            namespace = (raw_namespace,)
    elif (
        isinstance(chunk, tuple)
        and len(chunk) == 2
        and isinstance(chunk[0], str)
        and chunk[0] in requested_modes
    ):
        mode, data = chunk
    elif len(requested_modes) == 1:
        mode = requested_modes[0]
        data = chunk
    else:
        raise ValueError("Agent returned an unrecognized multi-mode stream chunk")

    return RuntimeStreamEvent(
        mode=mode,
        data=serialize_lc_object(data),
        namespace=namespace,
    )


def with_runtime_journal(config: Any | None, event_sink: RuntimeEventSink | None) -> Any | None:
    if event_sink is None:
        return config
    if config is not None and not isinstance(config, dict):
        raise TypeError("event_sink requires config to be a dict or None")
    resolved = dict(config or {})
    callbacks = list(resolved.get("callbacks") or [])
    callbacks.append(RuntimeJournal(event_sink))
    resolved["callbacks"] = callbacks
    return resolved
