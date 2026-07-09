import time

from north.runtime import MemoryStreamBridge, RunConflictError, RunManager, RuntimeService
from north.runtime.runs import RunStatus
from north.runtime.worker import run_agent


def test_run_manager_rejects_active_run_for_same_thread():
    manager = RunManager()
    first = manager.create_or_reject(thread_id="thread-1")

    assert first.status == RunStatus.pending

    try:
        manager.create_or_reject(thread_id="thread-1")
        assert False, "Expected active run conflict"
    except RunConflictError:
        pass


def test_run_manager_interrupt_cancels_old_run():
    manager = RunManager()
    first = manager.create_or_reject(thread_id="thread-1")
    second = manager.create_or_reject(thread_id="thread-1", multitask_strategy="interrupt")

    assert first.abort_event.is_set()
    assert first.status == RunStatus.interrupted
    assert second.status == RunStatus.pending


def test_memory_stream_bridge_publish_subscribe_end():
    bridge = MemoryStreamBridge()
    bridge.publish("run-1", "values", {"ok": True})
    bridge.publish_end("run-1")

    events = list(bridge.subscribe("run-1"))

    assert [(event.event, event.data) for event in events] == [
        ("values", {"ok": True}),
        ("end", None),
    ]


def test_run_agent_publishes_metadata_values_and_end_on_success():
    class StubAgent:
        def stream(self, graph_input, config=None, context=None, stream_mode=None):
            yield {"messages": [], "value": graph_input["value"]}

    manager = RunManager()
    bridge = MemoryStreamBridge()
    record = manager.create(thread_id="thread-1", run_id="run-1")

    run_agent(
        bridge,
        manager,
        record,
        agent_factory=lambda: StubAgent(),
        graph_input={"value": 1},
        config={},
    )

    events = list(bridge.subscribe("run-1"))

    assert manager.get("run-1").status == RunStatus.success
    assert [event.event for event in events] == ["metadata", "values", "end"]
    assert events[0].data == {"run_id": "run-1", "thread_id": "thread-1"}


def test_run_agent_marks_error_and_publishes_error_event():
    class FailingAgent:
        def stream(self, graph_input, config=None, context=None, stream_mode=None):
            raise ValueError("boom")
            yield graph_input

    manager = RunManager()
    bridge = MemoryStreamBridge()
    record = manager.create(thread_id="thread-1", run_id="run-1")

    run_agent(
        bridge,
        manager,
        record,
        agent_factory=lambda: FailingAgent(),
        graph_input={},
        config={},
    )

    events = list(bridge.subscribe("run-1"))

    assert manager.get("run-1").status == RunStatus.error
    assert [event.event for event in events] == ["metadata", "error", "end"]
    assert events[1].data == {"message": "boom", "error_type": "ValueError"}


def test_runtime_service_streams_background_run():
    class StubAgent:
        def stream(self, graph_input, config=None, context=None, stream_mode=None):
            yield {"messages": [], "answer": "ok"}

    service = RuntimeService()
    record = service.start_run(
        thread_id="thread-1",
        agent_factory=lambda: StubAgent(),
        graph_input={},
        config={},
    )

    events = list(service.stream_run(record.run_id))

    assert [event.event for event in events] == ["metadata", "values", "end"]
    assert service.run_manager.get(record.run_id).status == RunStatus.success


def test_runtime_service_cancel_marks_run_interrupted():
    class SlowAgent:
        def stream(self, graph_input, config=None, context=None, stream_mode=None):
            for index in range(100):
                time.sleep(0.01)
                yield {"messages": [], "index": index}

    service = RuntimeService()
    record = service.start_run(
        thread_id="thread-1",
        agent_factory=lambda: SlowAgent(),
        graph_input={},
        config={},
    )

    assert service.cancel_run(record.run_id)
    events = list(service.stream_run(record.run_id))

    assert events[-1].event == "end"
    assert service.run_manager.get(record.run_id).status == RunStatus.interrupted
