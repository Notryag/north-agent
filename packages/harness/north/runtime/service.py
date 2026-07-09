from __future__ import annotations

import threading
from collections.abc import Callable, Iterator
from typing import Any

from .runs import RunManager, RunRecord
from .stream_bridge import MemoryStreamBridge, StreamBridge, StreamEvent
from .worker import run_agent


class RuntimeService:
    def __init__(
        self,
        *,
        run_manager: RunManager | None = None,
        stream_bridge: StreamBridge | None = None,
    ):
        self.run_manager = run_manager or RunManager()
        self.stream_bridge = stream_bridge or MemoryStreamBridge()

    def start_run(
        self,
        *,
        thread_id: str,
        agent_factory: Callable[[], Any],
        graph_input: dict[str, Any],
        config: Any,
        context: dict[str, Any] | None = None,
        stream_mode: str = "values",
        multitask_strategy: str = "reject",
    ) -> RunRecord:
        record = self.run_manager.create_or_reject(
            thread_id=thread_id,
            multitask_strategy=multitask_strategy,
        )
        task = threading.Thread(
            target=run_agent,
            kwargs={
                "bridge": self.stream_bridge,
                "run_manager": self.run_manager,
                "record": record,
                "agent_factory": agent_factory,
                "graph_input": graph_input,
                "config": config,
                "context": context,
                "stream_mode": stream_mode,
            },
            daemon=True,
        )
        self.run_manager.set_task(record.run_id, task)
        task.start()
        return record

    def stream_run(self, run_id: str) -> Iterator[StreamEvent]:
        yield from self.stream_bridge.subscribe(run_id)

    def cancel_run(self, run_id: str) -> bool:
        return self.run_manager.cancel(run_id)
