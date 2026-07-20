from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Callable, Sequence
from typing import Any

from .events import RuntimeEventSink
from .runs import RunManager, RunRecord
from .stream_bridge import MemoryStreamBridge, StreamBridge, StreamEvent
from .worker import RunExecutor, RunLifecycleHooks, StreamObserver


class RuntimeService:
    """In-process orchestration facade built on the same async RunExecutor."""

    def __init__(
        self,
        *,
        run_manager: RunManager | None = None,
        stream_bridge: StreamBridge | None = None,
    ) -> None:
        self.run_manager = run_manager or RunManager()
        self.stream_bridge = stream_bridge or MemoryStreamBridge()
        self.executor = RunExecutor(self.stream_bridge, self.run_manager)

    async def start_run(
        self,
        *,
        thread_id: str,
        agent_factory: Callable[[], Any],
        graph_input: dict[str, Any],
        config: Any | None = None,
        context: dict[str, Any] | None = None,
        event_sink: RuntimeEventSink | None = None,
        stream_observer: StreamObserver | None = None,
        lifecycle_hooks: RunLifecycleHooks | None = None,
        stream_modes: Sequence[str] = ("values", "messages"),
        publish_modes: Sequence[str] = ("messages",),
        multitask_strategy: str = "reject",
    ) -> RunRecord:
        record = self.run_manager.create_or_reject(
            thread_id=thread_id,
            multitask_strategy=multitask_strategy,
        )
        task = asyncio.create_task(
            self.executor.execute(
                record,
                agent_factory=agent_factory,
                graph_input=graph_input,
                config=config,
                context=context,
                event_sink=event_sink,
                stream_observer=stream_observer,
                lifecycle_hooks=lifecycle_hooks,
                stream_modes=stream_modes,
                publish_modes=publish_modes,
            )
        )
        self.run_manager.set_task(record.run_id, task)
        return record

    def stream_run(
        self,
        run_id: str,
        *,
        last_event_id: str | None = None,
        heartbeat_interval: float = 15.0,
    ) -> AsyncIterator[StreamEvent]:
        return self.stream_bridge.subscribe(
            run_id,
            last_event_id=last_event_id,
            heartbeat_interval=heartbeat_interval,
        )

    def cancel_run(self, run_id: str) -> bool:
        return self.run_manager.cancel(run_id)
