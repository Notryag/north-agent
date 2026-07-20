from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass, field

from .base import (
    END_SENTINEL,
    HEARTBEAT_SENTINEL,
    REPLAY_GAP_EVENT,
    StreamBridge,
    StreamEvent,
)


@dataclass(slots=True)
class _RunStream:
    events: list[StreamEvent] = field(default_factory=list)
    condition: asyncio.Condition = field(default_factory=asyncio.Condition)
    ended: bool = False
    start_offset: int = 0


class MemoryStreamBridge(StreamBridge):
    """Replayable in-process event log for development and tests."""

    def __init__(self, *, max_events: int = 256) -> None:
        self._max_events = max(1, max_events)
        self._streams: dict[str, _RunStream] = {}
        self._sequences: dict[str, int] = {}

    def _stream(self, run_id: str) -> _RunStream:
        if run_id not in self._streams:
            self._streams[run_id] = _RunStream()
            self._sequences[run_id] = 0
        return self._streams[run_id]

    async def publish(
        self,
        run_id: str,
        event: str,
        data: object,
        *,
        namespace: tuple[str, ...] = (),
    ) -> None:
        stream = self._stream(run_id)
        sequence = self._sequences[run_id]
        self._sequences[run_id] = sequence + 1
        entry = StreamEvent(
            id=f"0-{sequence}",
            event=event,
            data=data,
            namespace=namespace,
        )
        async with stream.condition:
            stream.events.append(entry)
            if len(stream.events) > self._max_events:
                overflow = len(stream.events) - self._max_events
                del stream.events[:overflow]
                stream.start_offset += overflow
            stream.condition.notify_all()

    async def publish_end(self, run_id: str) -> None:
        stream = self._stream(run_id)
        async with stream.condition:
            stream.ended = True
            stream.condition.notify_all()

    async def subscribe(
        self,
        run_id: str,
        *,
        last_event_id: str | None = None,
        heartbeat_interval: float = 15.0,
    ) -> AsyncIterator[StreamEvent]:
        stream = self._stream(run_id)
        next_offset, replay_gap = self._start_offset(stream, last_event_id)
        if replay_gap:
            yield StreamEvent(
                id="",
                event=REPLAY_GAP_EVENT,
                data={
                    "first_available_event_id": (
                        stream.events[0].id if stream.events else None
                    ),
                    "last_available_event_id": (
                        stream.events[-1].id if stream.events else None
                    ),
                },
            )
        while True:
            async with stream.condition:
                if next_offset < stream.start_offset:
                    next_offset = stream.start_offset
                local_index = next_offset - stream.start_offset
                if 0 <= local_index < len(stream.events):
                    entry = stream.events[local_index]
                    next_offset += 1
                elif stream.ended:
                    entry = END_SENTINEL
                else:
                    try:
                        await asyncio.wait_for(
                            stream.condition.wait(),
                            timeout=heartbeat_interval,
                        )
                    except TimeoutError:
                        entry = HEARTBEAT_SENTINEL
                    else:
                        continue
            yield entry
            if entry is END_SENTINEL:
                return

    async def cleanup(self, run_id: str, *, delay: float = 0) -> None:
        if delay > 0:
            await asyncio.sleep(delay)
        self._streams.pop(run_id, None)
        self._sequences.pop(run_id, None)

    async def close(self) -> None:
        self._streams.clear()
        self._sequences.clear()

    @staticmethod
    def _start_offset(
        stream: _RunStream,
        last_event_id: str | None,
    ) -> tuple[int, bool]:
        if last_event_id is None:
            return stream.start_offset, False
        for index, event in enumerate(stream.events):
            if event.id == last_event_id:
                return stream.start_offset + index + 1, False
        return stream.start_offset, True
