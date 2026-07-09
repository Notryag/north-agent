from __future__ import annotations

import threading
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class RunStatus(StrEnum):
    pending = "pending"
    running = "running"
    success = "success"
    error = "error"
    interrupted = "interrupted"


class DisconnectMode(StrEnum):
    cancel = "cancel"
    continue_ = "continue"


@dataclass(slots=True)
class RunRecord:
    run_id: str
    thread_id: str
    status: RunStatus
    assistant_id: str | None = None
    on_disconnect: DisconnectMode = DisconnectMode.continue_
    multitask_strategy: str = "reject"
    metadata: dict[str, Any] = field(default_factory=dict)
    kwargs: dict[str, Any] = field(default_factory=dict)
    task: threading.Thread | None = None
    abort_event: threading.Event = field(default_factory=threading.Event)
    abort_action: str = "interrupt"
    error: str | None = None
