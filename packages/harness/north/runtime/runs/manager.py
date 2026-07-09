from __future__ import annotations

import threading
import uuid

from .schemas import DisconnectMode, RunRecord, RunStatus


ACTIVE_STATUSES = {RunStatus.pending, RunStatus.running}


class RunConflictError(RuntimeError):
    def __init__(self, thread_id: str):
        super().__init__(f"Thread already has an active run: {thread_id}")
        self.thread_id = thread_id


class RunManager:
    def __init__(self):
        self._lock = threading.RLock()
        self._runs: dict[str, RunRecord] = {}

    def create(
        self,
        *,
        thread_id: str,
        run_id: str | None = None,
        assistant_id: str | None = None,
        on_disconnect: DisconnectMode = DisconnectMode.continue_,
        multitask_strategy: str = "reject",
        metadata: dict | None = None,
        kwargs: dict | None = None,
    ) -> RunRecord:
        with self._lock:
            record = RunRecord(
                run_id=run_id or str(uuid.uuid4()),
                thread_id=thread_id,
                assistant_id=assistant_id,
                status=RunStatus.pending,
                on_disconnect=on_disconnect,
                multitask_strategy=multitask_strategy,
                metadata=dict(metadata or {}),
                kwargs=dict(kwargs or {}),
            )
            self._runs[record.run_id] = record
            return record

    def create_or_reject(
        self,
        *,
        thread_id: str,
        multitask_strategy: str = "reject",
        **kwargs,
    ) -> RunRecord:
        with self._lock:
            active = self.active_for_thread(thread_id)
            if active is not None:
                if multitask_strategy == "interrupt":
                    self.cancel(active.run_id)
                else:
                    raise RunConflictError(thread_id)
            return self.create(thread_id=thread_id, multitask_strategy=multitask_strategy, **kwargs)

    def get(self, run_id: str) -> RunRecord | None:
        with self._lock:
            return self._runs.get(run_id)

    def list_by_thread(self, thread_id: str) -> list[RunRecord]:
        with self._lock:
            return [record for record in self._runs.values() if record.thread_id == thread_id]

    def active_for_thread(self, thread_id: str) -> RunRecord | None:
        with self._lock:
            for record in self._runs.values():
                if record.thread_id == thread_id and record.status in ACTIVE_STATUSES:
                    return record
            return None

    def set_task(self, run_id: str, task: threading.Thread) -> None:
        with self._lock:
            record = self._require(run_id)
            record.task = task

    def set_status(self, run_id: str, status: RunStatus, *, error: str | None = None) -> None:
        with self._lock:
            record = self._require(run_id)
            record.status = status
            record.error = error

    def cancel(self, run_id: str, *, action: str = "interrupt") -> bool:
        with self._lock:
            record = self._runs.get(run_id)
            if record is None:
                return False
            record.abort_action = action
            record.abort_event.set()
            if record.status in ACTIVE_STATUSES:
                record.status = RunStatus.interrupted
            return True

    def cleanup(self, run_id: str) -> None:
        with self._lock:
            self._runs.pop(run_id, None)

    def _require(self, run_id: str) -> RunRecord:
        record = self._runs.get(run_id)
        if record is None:
            raise KeyError(f"Unknown run_id: {run_id}")
        return record
