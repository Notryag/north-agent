from __future__ import annotations

from typing import Any


def serialize(obj: Any, *, mode: str = "") -> Any:
    _ = mode
    if isinstance(obj, dict):
        return {key: serialize(value, mode=mode) for key, value in obj.items() if not str(key).startswith("__pregel_")}
    if isinstance(obj, (list, tuple)):
        return [serialize(item, mode=mode) for item in obj]
    if hasattr(obj, "model_dump"):
        return serialize(obj.model_dump(), mode=mode)
    return obj


def serialize_channel_values(channel_values: dict[str, Any]) -> dict[str, Any]:
    return serialize(channel_values, mode="values")


def serialize_lc_object(obj: Any) -> Any:
    return serialize(obj)


def serialize_messages_tuple(obj: Any) -> Any:
    return serialize(obj, mode="messages")
