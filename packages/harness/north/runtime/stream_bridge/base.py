from __future__ import annotations

import abc
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class StreamEvent:
    id: str
    event: str
    data: Any = None
    namespace: tuple[str, ...] = ()


HEARTBEAT_SENTINEL = StreamEvent(id="", event="__heartbeat__")
END_SENTINEL = StreamEvent(id="", event="__end__")
REPLAY_GAP_EVENT = "__replay_gap__"


class StreamBridge(abc.ABC):
    """Async producer/consumer boundary between Run workers and gateways."""

    supports_cross_process: bool = False

    @abc.abstractmethod
    async def publish(
        self,
        run_id: str,
        event: str,
        data: Any,
        *,
        namespace: tuple[str, ...] = (),
    ) -> None: ...

    @abc.abstractmethod
    async def publish_end(self, run_id: str) -> None: ...

    @abc.abstractmethod
    def subscribe(
        self,
        run_id: str,
        *,
        last_event_id: str | None = None,
        heartbeat_interval: float = 15.0,
    ) -> AsyncIterator[StreamEvent]: ...

    @abc.abstractmethod
    async def cleanup(self, run_id: str, *, delay: float = 0) -> None: ...

    async def close(self) -> None:
        return None
