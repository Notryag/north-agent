from __future__ import annotations

import time
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from langchain_core.callbacks import AsyncCallbackHandler


@dataclass(frozen=True, slots=True)
class RuntimeEvent:
    event_type: str
    category: str
    content: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)


RuntimeEventSink = Callable[[RuntimeEvent], Awaitable[None]]


class RuntimeJournal(AsyncCallbackHandler):
    """Translate LangChain callbacks into product-neutral runtime events."""

    def __init__(self, sink: RuntimeEventSink) -> None:
        self._sink = sink
        self._model_started_at: dict[str, float] = {}
        self._model_call_indexes: dict[str, int] = {}
        self._tool_started_at: dict[str, float] = {}
        self._tool_names: dict[str, str] = {}
        self._model_call_index = 0

    async def on_chat_model_start(
        self,
        serialized: dict[str, Any],
        messages: list[list[Any]],
        *,
        run_id: UUID,
        tags: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        del serialized, messages, kwargs
        call_id = str(run_id)
        self._model_started_at[call_id] = time.monotonic()
        self._model_call_index += 1
        self._model_call_indexes[call_id] = self._model_call_index
        await self._emit(
            "model.started",
            "model",
            metadata={
                "call_id": call_id,
                "call_index": self._model_call_index,
                "caller": _identify_caller(tags),
            },
        )

    async def on_llm_end(
        self,
        response: Any,
        *,
        run_id: UUID,
        tags: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        del kwargs
        call_id = str(run_id)
        started_at = self._model_started_at.pop(call_id, None)
        call_index = self._model_call_indexes.pop(call_id, None)
        latency_ms = int((time.monotonic() - started_at) * 1000) if started_at else None
        for message in _response_messages(response):
            usage = getattr(message, "usage_metadata", None)
            await self._emit(
                "model.completed",
                "model",
                content=_serialize_value(message),
                metadata={
                    "call_id": call_id,
                    "call_index": call_index,
                    "caller": _identify_caller(tags),
                    "latency_ms": latency_ms,
                    "usage": dict(usage) if isinstance(usage, Mapping) else {},
                },
            )

    async def on_llm_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        del kwargs
        call_id = str(run_id)
        self._model_started_at.pop(call_id, None)
        call_index = self._model_call_indexes.pop(call_id, None)
        await self._emit(
            "model.error",
            "error",
            content=str(error),
            metadata={
                "call_id": call_id,
                "call_index": call_index,
                "error_type": type(error).__name__,
            },
        )

    async def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        inputs: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        del kwargs
        call_id = str(run_id)
        tool_name = str((serialized or {}).get("name") or "unknown")
        self._tool_started_at[call_id] = time.monotonic()
        self._tool_names[call_id] = tool_name
        await self._emit(
            "tool.started",
            "tool",
            content=_serialize_value(inputs) if inputs is not None else input_str,
            metadata={
                "call_id": call_id,
                "tool_name": tool_name,
            },
        )

    async def on_tool_end(self, output: Any, *, run_id: UUID, **kwargs: Any) -> None:
        del kwargs
        call_id = str(run_id)
        started_at = self._tool_started_at.pop(call_id, None)
        tool_name = self._tool_names.pop(call_id, "unknown")
        await self._emit(
            "tool.completed",
            "tool",
            content=_serialize_value(output),
            metadata={
                "call_id": call_id,
                "tool_name": tool_name,
                "latency_ms": int((time.monotonic() - started_at) * 1000)
                if started_at
                else None,
            },
        )

    async def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        del kwargs
        call_id = str(run_id)
        started_at = self._tool_started_at.pop(call_id, None)
        tool_name = self._tool_names.pop(call_id, "unknown")
        await self._emit(
            "tool.error",
            "error",
            content=str(error),
            metadata={
                "call_id": call_id,
                "tool_name": tool_name,
                "error_type": type(error).__name__,
                "latency_ms": int((time.monotonic() - started_at) * 1000)
                if started_at
                else None,
            },
        )

    async def _emit(
        self,
        event_type: str,
        category: str,
        *,
        content: Any = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        await self._sink(
            RuntimeEvent(
                event_type=event_type,
                category=category,
                content=content,
                metadata=metadata or {},
            )
        )


def _identify_caller(tags: list[str] | None) -> str:
    for tag in tags or []:
        if tag == "lead_agent" or tag.startswith(("subagent:", "middleware:")):
            return tag
    return "unknown"


def _response_messages(response: Any) -> list[Any]:
    messages: list[Any] = []
    for generation in getattr(response, "generations", []) or []:
        for item in generation:
            message = getattr(item, "message", None)
            if message is not None:
                messages.append(message)
    return messages


def _serialize_value(value: Any) -> Any:
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return model_dump(mode="json")
    if isinstance(value, Mapping):
        return {str(key): _serialize_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize_value(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)
