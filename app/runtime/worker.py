from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .runs import RunManager, RunRecord, RunStatus
from .stream_bridge import StreamBridge


def run_agent(
    bridge: StreamBridge,
    run_manager: RunManager,
    record: RunRecord,
    *,
    agent_factory: Callable[[], Any],
    graph_input: dict[str, Any],
    config: Any,
    context: dict[str, Any] | None = None,
    stream_mode: str = "values",
) -> None:
    try:
        run_manager.set_status(record.run_id, RunStatus.running)
        bridge.publish(
            record.run_id,
            "metadata",
            {"run_id": record.run_id, "thread_id": record.thread_id},
        )
        agent = agent_factory()
        for chunk in agent.stream(graph_input, config=config, context=context, stream_mode=stream_mode):
            if record.abort_event.is_set():
                run_manager.set_status(record.run_id, RunStatus.interrupted)
                return
            bridge.publish(record.run_id, "values", chunk)

        if record.abort_event.is_set():
            run_manager.set_status(record.run_id, RunStatus.interrupted)
        else:
            run_manager.set_status(record.run_id, RunStatus.success)
    except Exception as exc:
        run_manager.set_status(record.run_id, RunStatus.error, error=str(exc))
        bridge.publish(
            record.run_id,
            "error",
            {"message": str(exc), "error_type": type(exc).__name__},
        )
    finally:
        bridge.publish_end(record.run_id)
