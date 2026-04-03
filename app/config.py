from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ENV_PATH = PROJECT_ROOT / ".env"


def load_environment(env_path: Path | None = None) -> None:
    """Load variables from the project .env file when it exists."""
    candidate = env_path or DEFAULT_ENV_PATH
    if candidate.exists():
        load_dotenv(candidate, override=False)


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    return int(value)


@dataclass(slots=True)
class AppConfig:
    model_name: str
    thinking_enabled: bool = False
    system_prompt: str = "You are a helpful assistant."
    recursion_limit: int = 50

    @classmethod
    def from_env(cls) -> "AppConfig":
        load_environment()
        return cls(
            model_name=os.getenv("APP_MODEL_NAME", "openai:gpt-4o-mini"),
            thinking_enabled=_get_bool("APP_THINKING_ENABLED", False),
            system_prompt=os.getenv("APP_SYSTEM_PROMPT", "You are a helpful assistant."),
            recursion_limit=_get_int("APP_RECURSION_LIMIT", 50),
        )

    def validate(self) -> None:
        provider, separator, _model_name = self.model_name.partition(":")
        if separator and provider == "openai" and not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY is not set. Add it to the project .env file before running the app.")
