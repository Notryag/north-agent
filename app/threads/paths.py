from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..config import PROJECT_ROOT


@dataclass(frozen=True, slots=True)
class ThreadPaths:
    thread_id: str
    base_dir: Path = PROJECT_ROOT / ".deerflow"

    @property
    def threads_dir(self) -> Path:
        return self.base_dir / "threads"

    @property
    def thread_dir(self) -> Path:
        return self.threads_dir / self.thread_id

    @property
    def workspace_dir(self) -> Path:
        return self.thread_dir / "workspace"

    @property
    def uploads_dir(self) -> Path:
        return self.thread_dir / "uploads"

    @property
    def outputs_dir(self) -> Path:
        return self.thread_dir / "outputs"

    def ensure(self) -> "ThreadPaths":
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        return self
