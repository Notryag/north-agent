from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class StreamEvent:
    id: str
    event: str
    data: Any = None


class StreamBridge(Protocol):
    def publish(self, run_id: str, event: str, data: Any) -> None: ...

    def publish_end(self, run_id: str) -> None: ...

    def subscribe(self, run_id: str, *, timeout: float | None = None): ...

    def cleanup(self, run_id: str) -> None: ...
