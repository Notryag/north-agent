from __future__ import annotations

from pathlib import Path

from langchain.tools import ToolRuntime


def resolve_thread_id(thread_id: str | None, runtime: ToolRuntime | None) -> str:
    if thread_id:
        return thread_id
    if runtime is not None and isinstance(runtime.context, dict):
        value = runtime.context.get("thread_id")
        if isinstance(value, str) and value:
            return value
    if runtime is not None:
        configurable = runtime.config.get("configurable", {})
        if isinstance(configurable, dict):
            value = configurable.get("thread_id")
            if isinstance(value, str) and value:
                return value
    return "default"


def resolve_runtime_path(name: str, runtime: ToolRuntime | None) -> Path:
    if runtime is not None and isinstance(runtime.context, dict):
        value = runtime.context.get(name)
        if isinstance(value, (str, Path)) and value:
            return Path(value).expanduser().resolve()
    raise RuntimeError(f"Runtime context is missing required path: {name}")
