from __future__ import annotations

import itertools
import queue
import threading
from typing import Any, Iterator

from .base import StreamEvent


class MemoryStreamBridge:
    def __init__(self):
        self._lock = threading.RLock()
        self._queues: dict[str, queue.Queue[StreamEvent]] = {}
        self._ids = itertools.count(1)

    def publish(self, run_id: str, event: str, data: Any) -> None:
        self._queue_for(run_id).put(StreamEvent(id=str(next(self._ids)), event=event, data=data))

    def publish_end(self, run_id: str) -> None:
        self.publish(run_id, "end", None)

    def subscribe(self, run_id: str, *, timeout: float | None = None) -> Iterator[StreamEvent]:
        stream_queue = self._queue_for(run_id)
        while True:
            entry = stream_queue.get(timeout=timeout)
            yield entry
            if entry.event == "end":
                return

    def cleanup(self, run_id: str) -> None:
        with self._lock:
            self._queues.pop(run_id, None)

    def _queue_for(self, run_id: str) -> queue.Queue[StreamEvent]:
        with self._lock:
            if run_id not in self._queues:
                self._queues[run_id] = queue.Queue()
            return self._queues[run_id]
