from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


def load_environment(env_path: Path) -> None:
    """Load variables from an explicitly selected host environment file."""
    if env_path.exists():
        load_dotenv(env_path, override=False)


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


def _get_csv(name: str) -> tuple[str, ...]:
    value = os.getenv(name)
    if value is None:
        return ()
    items: list[str] = []
    for raw in value.split(","):
        item = raw.strip()
        if item and item not in items:
            items.append(item)
    return tuple(items)


@dataclass(slots=True)
class AppConfig:
    model_name: str
    model_headers: dict[str, str] = field(default_factory=dict)
    model_options: dict[str, object] = field(default_factory=dict)
    thinking_enabled: bool = False
    system_prompt: str = "You are a helpful assistant."
    recursion_limit: int = 50
    skills_dir: Path | None = None
    thread_base_dir: Path | None = None
    enabled_skills: tuple[str, ...] = ()
    summarization_enabled: bool = False
    summarization_model_name: str | None = None
    summarization_summary_prompt: str | None = None
    summarization_trigger_messages: int = 40
    summarization_keep_messages: int = 12

    @classmethod
    def from_env(
        cls,
        *,
        env_path: Path | None = None,
        skills_dir: Path | None = None,
        thread_base_dir: Path | None = None,
    ) -> "AppConfig":
        if env_path is not None:
            load_environment(env_path)
        configured_skills_dir = os.getenv("APP_SKILLS_DIR")
        configured_thread_base_dir = os.getenv("APP_THREAD_BASE_DIR")
        return cls(
            model_name=os.getenv("APP_MODEL_NAME", "openai:gpt-4o-mini"),
            thinking_enabled=_get_bool("APP_THINKING_ENABLED", False),
            system_prompt=os.getenv("APP_SYSTEM_PROMPT", "You are a helpful assistant."),
            recursion_limit=_get_int("APP_RECURSION_LIMIT", 50),
            skills_dir=Path(configured_skills_dir) if configured_skills_dir else skills_dir,
            thread_base_dir=(
                Path(configured_thread_base_dir)
                if configured_thread_base_dir
                else thread_base_dir
            ),
            enabled_skills=_get_csv("APP_SKILLS"),
            summarization_enabled=_get_bool("APP_SUMMARIZATION_ENABLED", False),
            summarization_model_name=os.getenv("APP_SUMMARIZATION_MODEL_NAME"),
            summarization_summary_prompt=os.getenv("APP_SUMMARIZATION_SUMMARY_PROMPT"),
            summarization_trigger_messages=_get_int("APP_SUMMARIZATION_TRIGGER_MESSAGES", 40),
            summarization_keep_messages=_get_int("APP_SUMMARIZATION_KEEP_MESSAGES", 12),
        )

    def validate(self) -> None:
        provider, separator, _model_name = self.model_name.partition(":")
        effective_provider = provider if separator else "openai"
        if effective_provider == "openai" and not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY is not set. Add it to the project .env file before running the app.")
        if _get_bool("LANGSMITH_TRACING", False) and not os.getenv("LANGSMITH_API_KEY"):
            raise RuntimeError("LANGSMITH_API_KEY is not set. Add it to the project .env file or disable LANGSMITH_TRACING.")
        if self.enabled_skills and self.skills_dir is None:
            raise RuntimeError("APP_SKILLS requires an explicit skills directory")
        if self.enabled_skills and self.skills_dir is not None and not self.skills_dir.exists():
            raise RuntimeError(
                f"APP_SKILLS requested {', '.join(self.enabled_skills)} but skills directory does not exist: {self.skills_dir}"
            )
