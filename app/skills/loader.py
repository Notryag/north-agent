from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class SkillSpec:
    name: str
    root_dir: Path
    description: str = ""
    prompt: str = ""
    tools: tuple[str, ...] | None = None


def _read_skill_prompt(root_dir: Path, payload: dict[str, Any]) -> str:
    prompt_file = payload.get("prompt_file", "prompt.md")
    if prompt_file is None:
        return ""
    if not isinstance(prompt_file, str):
        raise ValueError(f"Invalid prompt_file in {root_dir / 'skill.json'}: expected string or null.")

    prompt_path = root_dir / prompt_file
    if not prompt_path.exists():
        if prompt_file == "prompt.md":
            return ""
        raise ValueError(f"Skill prompt file does not exist: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8").strip()


def _parse_tools(root_dir: Path, payload: dict[str, Any]) -> tuple[str, ...] | None:
    if "tools" not in payload:
        return None

    raw_tools = payload["tools"]
    if not isinstance(raw_tools, list):
        raise ValueError(f"Invalid tools in {root_dir / 'skill.json'}: expected a list of tool names.")

    tools: list[str] = []
    for item in raw_tools:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"Invalid tool entry in {root_dir / 'skill.json'}: expected non-empty strings.")
        name = item.strip()
        if name not in tools:
            tools.append(name)
    return tuple(tools)


def load_skill_from_dir(root_dir: Path) -> SkillSpec:
    skill_file = root_dir / "skill.json"
    if not skill_file.exists():
        raise ValueError(f"Skill definition not found: {skill_file}")

    payload = json.loads(skill_file.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid skill definition in {skill_file}: expected a JSON object.")

    raw_name = payload.get("name", root_dir.name)
    if not isinstance(raw_name, str) or not raw_name.strip():
        raise ValueError(f"Invalid skill name in {skill_file}.")

    raw_description = payload.get("description", "")
    if not isinstance(raw_description, str):
        raise ValueError(f"Invalid skill description in {skill_file}: expected a string.")

    return SkillSpec(
        name=raw_name.strip(),
        root_dir=root_dir,
        description=raw_description.strip(),
        prompt=_read_skill_prompt(root_dir, payload),
        tools=_parse_tools(root_dir, payload),
    )


def discover_skills(skills_dir: Path) -> dict[str, SkillSpec]:
    if not skills_dir.exists():
        return {}

    discovered: dict[str, SkillSpec] = {}
    for candidate in sorted(skills_dir.iterdir(), key=lambda path: path.name):
        if not candidate.is_dir():
            continue
        skill = load_skill_from_dir(candidate)
        if skill.name in discovered:
            raise ValueError(f"Duplicate skill name discovered: {skill.name}")
        discovered[skill.name] = skill
    return discovered


def load_skills(skills_dir: Path, names: tuple[str, ...] | list[str]) -> list[SkillSpec]:
    normalized_names: list[str] = []
    for raw_name in names:
        name = raw_name.strip()
        if name and name not in normalized_names:
            normalized_names.append(name)

    if not normalized_names:
        return []

    discovered = discover_skills(skills_dir)
    missing = [name for name in normalized_names if name not in discovered]
    if missing:
        raise ValueError(f"Unknown skills: {', '.join(missing)}")

    return [discovered[name] for name in normalized_names]


def compose_system_prompt(base_prompt: str, skills: list[SkillSpec]) -> str:
    sections = [base_prompt.strip()]
    for skill in skills:
        if not skill.prompt:
            continue
        sections.append(f"[skill:{skill.name}]\n{skill.prompt}")
    return "\n\n".join(section for section in sections if section)


def filter_tools_by_skills(all_tools: list, skills: list[SkillSpec]) -> list:
    constrained_names = [skill.tools for skill in skills if skill.tools is not None]
    if not constrained_names:
        return list(all_tools)

    allowed_names = {name for names in constrained_names for name in names}
    available_names = {tool.name for tool in all_tools}
    unknown_names = sorted(name for name in allowed_names if name not in available_names)
    if unknown_names:
        raise ValueError(f"Skill requested unknown tools: {', '.join(unknown_names)}")

    return [tool for tool in all_tools if tool.name in allowed_names]
