from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any

from redis.asyncio import Redis

from .base import (
    END_SENTINEL,
    HEARTBEAT_SENTINEL,
    REPLAY_GAP_EVENT,
    StreamBridge,
    StreamEvent,
)

_END_EVENT = "__end__"


class RedisStreamBridge(StreamBridge):
    """Cross-process replayable bridge backed by Redis Streams."""

    supports_cross_process = True

    def __init__(
        self,
        client: Any | None = None,
        *,
        redis_url: str | None = None,
        key_prefix: str = "north:run-stream",
        max_events: int = 1000,
        ttl_seconds: int = 86400,
    ) -> None:
        if client is None and redis_url is None:
            raise ValueError("client or redis_url is required")
        self._owns_client = client is None
        self._client = client or Redis.from_url(redis_url, decode_responses=False)
        self._key_prefix = key_prefix.rstrip(":")
        self._max_events = max(1, max_events)
        self._ttl_seconds = max(1, ttl_seconds)

    async def publish(
        self,
        run_id: str,
        event: str,
        data: Any,
        *,
        namespace: tuple[str, ...] = (),
    ) -> None:
        key = self._key(run_id)
        await self._client.xadd(
            key,
            {
                "event": event,
                "data": json.dumps(data, ensure_ascii=False, default=str),
                "namespace": json.dumps(namespace, ensure_ascii=False),
            },
            maxlen=self._max_events,
            approximate=True,
        )
        await self._client.expire(key, self._ttl_seconds)

    async def publish_end(self, run_id: str) -> None:
        await self.publish(run_id, _END_EVENT, None)

    async def subscribe(
        self,
        run_id: str,
        *,
        last_event_id: str | None = None,
        heartbeat_interval: float = 15.0,
    ) -> AsyncIterator[StreamEvent]:
        cursor = last_event_id or "0-0"
        block_ms = max(1, int(heartbeat_interval * 1000))
        if last_event_id is not None:
            key = self._key(run_id)
            first_entries = await self._client.xrange(
                key,
                min="-",
                max="+",
                count=1,
            )
            last_entries = await self._client.xrevrange(
                key,
                max="+",
                min="-",
                count=1,
            )
            if first_entries and last_entries:
                first_event_id = _text(first_entries[0][0])
                last_available_event_id = _text(last_entries[0][0])
                requested_id = _redis_id(last_event_id)
                if not (
                    _redis_id(first_event_id)
                    <= requested_id
                    <= _redis_id(last_available_event_id)
                ):
                    yield StreamEvent(
                        id="",
                        event=REPLAY_GAP_EVENT,
                        data={
                            "first_available_event_id": first_event_id,
                            "last_available_event_id": last_available_event_id,
                        },
                    )
                    cursor = "0-0"
            elif not first_entries:
                yield StreamEvent(
                    id="",
                    event=REPLAY_GAP_EVENT,
                    data={
                        "first_available_event_id": None,
                        "last_available_event_id": None,
                    },
                )
                cursor = "0-0"
        while True:
            batches = await self._client.xread(
                {self._key(run_id): cursor},
                count=100,
                block=block_ms,
            )
            if not batches:
                yield HEARTBEAT_SENTINEL
                continue
            for _, entries in batches:
                for raw_id, fields in entries:
                    event_id = _text(raw_id)
                    event_name = _text(_field(fields, "event"))
                    cursor = event_id
                    if event_name == _END_EVENT:
                        yield END_SENTINEL
                        return
                    raw_data = _text(_field(fields, "data"))
                    yield StreamEvent(
                        id=event_id,
                        event=event_name,
                        data=json.loads(raw_data),
                        namespace=tuple(
                            json.loads(_text(_field(fields, "namespace")))
                        ),
                    )

    async def cleanup(self, run_id: str, *, delay: float = 0) -> None:
        if delay > 0:
            await asyncio.sleep(delay)
        await self._client.delete(self._key(run_id))

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    def _key(self, run_id: str) -> str:
        return f"{self._key_prefix}:{run_id}"


def _field(fields: dict[Any, Any], name: str) -> Any:
    return fields.get(name, fields.get(name.encode()))


def _text(value: Any) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return str(value)


def _redis_id(value: str) -> tuple[int, int]:
    milliseconds, sequence = value.split("-", 1)
    return int(milliseconds), int(sequence)
