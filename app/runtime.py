from __future__ import annotations

from collections.abc import Sequence

from langchain.agents.middleware import AgentMiddleware

from .agents.middlewares import get_default_middlewares
from .checkpointer import get_default_checkpointer
from .config import AppConfig
from .skills import SkillSpec, compose_system_prompt, filter_tools_by_skills, load_skills
from .state import ThreadState
from .tools import get_builtin_tools


def get_skills(config: AppConfig, *, skill_names: Sequence[str] | None = None) -> list[SkillSpec]:
    """Resolve runtime skills from config or an explicit selection."""
    names = tuple(skill_names) if skill_names is not None else config.enabled_skills
    return load_skills(config.skills_dir, names)


def get_tools(
    config: AppConfig,
    *,
    skills: Sequence[SkillSpec] | None = None,
    skill_names: Sequence[str] | None = None,
) -> list:
    """Resolve runtime tools for the given config."""
    resolved_skills = list(skills) if skills is not None else get_skills(config, skill_names=skill_names)
    return filter_tools_by_skills(get_builtin_tools(), resolved_skills)


def get_system_prompt(
    config: AppConfig,
    *,
    skills: Sequence[SkillSpec] | None = None,
    skill_names: Sequence[str] | None = None,
) -> str:
    """Resolve the final system prompt after skill composition."""
    resolved_skills = list(skills) if skills is not None else get_skills(config, skill_names=skill_names)
    return compose_system_prompt(config.system_prompt, resolved_skills)


def get_middlewares(config: AppConfig) -> Sequence[AgentMiddleware]:
    """Resolve runtime middlewares for the given config."""
    _ = config
    return get_default_middlewares()


def get_checkpointer(config: AppConfig):
    """Resolve the default checkpointer for the given config."""
    _ = config
    return get_default_checkpointer()


def get_state_schema():
    """Resolve the shared state schema for the lite runtime.

    ``ThreadState`` intentionally stays narrow in this phase so tools only need
    one stable write surface: ``artifacts``.
    """
    return ThreadState
