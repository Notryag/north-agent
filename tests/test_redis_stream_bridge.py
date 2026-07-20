import asyncio

from north.runtime import END_SENTINEL, RedisStreamBridge


class FakeRedis:
    def __init__(self):
        self.entries = []
        self.expirations = []
        self.sequence = 0

    async def xadd(self, key, fields, **kwargs):
        self.sequence += 1
        event_id = f"{self.sequence}-0".encode()
        self.entries.append((key, event_id, fields, kwargs))
        return event_id

    async def expire(self, key, seconds):
        self.expirations.append((key, seconds))

    async def xread(self, streams, **kwargs):
        del kwargs
        key, cursor = next(iter(streams.items()))
        cursor_number = int(cursor.split("-", 1)[0])
        entries = [
            (event_id, {name.encode(): value.encode() for name, value in fields.items()})
            for candidate_key, event_id, fields, _ in self.entries
            if candidate_key == key and int(event_id.split(b"-", 1)[0]) > cursor_number
        ]
        return [(key.encode(), entries)] if entries else []

    async def xrange(self, key, **kwargs):
        del kwargs
        return [
            (event_id, fields)
            for candidate_key, event_id, fields, _ in self.entries
            if candidate_key == key
        ][:1]

    async def xrevrange(self, key, **kwargs):
        del kwargs
        return [
            (event_id, fields)
            for candidate_key, event_id, fields, _ in reversed(self.entries)
            if candidate_key == key
        ][:1]

    async def delete(self, key):
        self.entries = [entry for entry in self.entries if entry[0] != key]


def test_redis_stream_bridge_replays_canonical_events_and_end():
    asyncio.run(_assert_redis_stream_bridge())


async def _assert_redis_stream_bridge():
    redis = FakeRedis()
    bridge = RedisStreamBridge(redis, key_prefix="test:runs")
    await bridge.publish("run-1", "messages-tuple", [{"type": "AIMessageChunk"}, {}])
    await bridge.publish("run-1", "run_completed", {"content": "完成"})
    await bridge.publish_end("run-1")

    events = [
        event
        async for event in bridge.subscribe("run-1", last_event_id="1-0")
    ]

    assert [event.event for event in events] == ["run_completed", END_SENTINEL.event]
    assert events[0].id == "2-0"
    assert events[0].data == {"content": "完成"}
    assert redis.expirations[-1] == ("test:runs:run-1", 86400)


def test_redis_stream_bridge_reports_trimmed_replay_gap():
    asyncio.run(_assert_trimmed_replay_gap())


async def _assert_trimmed_replay_gap():
    redis = FakeRedis()
    bridge = RedisStreamBridge(redis, key_prefix="test:runs")
    for index in range(3):
        await bridge.publish("run-1", "values", {"index": index})
    redis.entries.pop(0)
    await bridge.publish_end("run-1")

    events = [
        event
        async for event in bridge.subscribe("run-1", last_event_id="1-0")
    ]

    assert events[0].event == "__replay_gap__"
    assert events[0].data == {
        "first_available_event_id": "2-0",
        "last_available_event_id": "4-0",
    }
    assert [event.data for event in events[1:-1]] == [{"index": 1}, {"index": 2}]


def test_redis_stream_bridge_resets_foreign_future_cursor():
    asyncio.run(_assert_future_cursor_reset())


async def _assert_future_cursor_reset():
    redis = FakeRedis()
    bridge = RedisStreamBridge(redis, key_prefix="test:runs")
    await bridge.publish("run-1", "run_completed", {"content": "完成"})
    await bridge.publish_end("run-1")

    events = [
        event
        async for event in bridge.subscribe("run-1", last_event_id="999999-0")
    ]

    assert events[0].event == "__replay_gap__"
    assert events[1].event == "run_completed"
    assert events[-1] is END_SENTINEL


def test_redis_stream_bridge_reports_gap_for_expired_stream():
    asyncio.run(_assert_expired_stream_gap())


async def _assert_expired_stream_gap():
    bridge = RedisStreamBridge(FakeRedis(), key_prefix="test:runs")
    subscription = bridge.subscribe("run-1", last_event_id="10-0", heartbeat_interval=0.001)

    event = await anext(subscription)
    await subscription.aclose()

    assert event.event == "__replay_gap__"
    assert event.data == {
        "first_available_event_id": None,
        "last_available_event_id": None,
    }
