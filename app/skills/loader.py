from __future__ import annotations

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


def _split_frontmatter(text: str, source: Path) -> tuple[dict[str, Any], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text.strip()

    closing_index: int | None = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            closing_index = index
            break
    if closing_index is None:
        raise ValueError(f"Unclosed frontmatter in {source}")

    metadata_lines = lines[1:closing_index]
    body = "\n".join(lines[closing_index + 1 :]).strip()
    return _parse_frontmatter(metadata_lines, source), body


def _parse_frontmatter(lines: list[str], source: Path) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    index = 0

    while index < len(lines):
        raw_line = lines[index]
        stripped = raw_line.strip()
        if not stripped:
            index += 1
            continue
        if ":" not in raw_line:
            raise ValueError(f"Invalid frontmatter line in {source}: {raw_line}")

        key, raw_value = raw_line.split(":", 1)
        key = key.strip()
        value = raw_value.strip()

        if not key:
            raise ValueError(f"Invalid frontmatter key in {source}: {raw_line}")

        if value:
            if value.startswith("[") and value.endswith("]"):
                inner = value[1:-1].strip()
                items = [item.strip().strip("'\"") for item in inner.split(",") if item.strip()]
                payload[key] = items
            else:
                payload[key] = value
            index += 1
            continue

        items: list[str] = []
        index += 1
        while index < len(lines):
            nested = lines[index]
            nested_stripped = nested.strip()
            if not nested_stripped:
                index += 1
                continue
            if nested_stripped.startswith("- "):
                item = nested_stripped[2:].strip()
                if not item:
                    raise ValueError(f"Invalid list item in {source}: {nested}")
                items.append(item)
                index += 1
                continue
            break
        payload[key] = items

    return payload


def _parse_tools(source: Path, payload: dict[str, Any]) -> tuple[str, ...] | None:
    if "tools" not in payload:
        return None

    raw_tools = payload["tools"]
    if not isinstance(raw_tools, list):
        raise ValueError(f"Invalid tools in {source}: expected a list of tool names.")

    tools: list[str] = []
    for item in raw_tools:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"Invalid tool entry in {source}: expected non-empty strings.")
        name = item.strip()
        if name not in tools:
            tools.append(name)
    return tuple(tools)


def load_skill_from_dir(root_dir: Path) -> SkillSpec:
    skill_file = root_dir / "SKILL.md"
    if not skill_file.exists():
        raise ValueError(f"Skill definition not found: {skill_file}")

    payload, prompt = _split_frontmatter(skill_file.read_text(encoding="utf-8"), skill_file)

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
        prompt=prompt,
        tools=_parse_tools(skill_file, payload),
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


def load_all_skills(skills_dir: Path) -> list[SkillSpec]:
    return list(discover_skills(skills_dir).values())


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
