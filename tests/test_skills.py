import pytest

from app.config import AppConfig
from app.runtime import get_skills, get_system_prompt, get_tools
from app.skills import discover_skills


def write_skill(
    tmp_path,
    dir_name: str,
    *,
    frontmatter: str = "",
    prompt: str = "",
):
    skill_dir = tmp_path / dir_name
    skill_dir.mkdir()
    body = frontmatter.strip()
    content_parts = []
    if body:
        content_parts.append("---")
        content_parts.append(body)
        content_parts.append("---")
    if prompt:
        content_parts.append(prompt.strip())
    (skill_dir / "SKILL.md").write_text("\n".join(content_parts).strip() + "\n", encoding="utf-8")
    return skill_dir


def test_discover_skills_loads_frontmatter_and_prompt(tmp_path):
    write_skill(
        tmp_path,
        "research",
        frontmatter="""
name: research
description: Web research workflow
tools:
  - web_search
  - web_fetch
  - write_report
""",
        prompt="Focus on traceable sources.",
    )

    discovered = discover_skills(tmp_path)

    assert list(discovered) == ["research"]
    assert discovered["research"].description == "Web research workflow"
    assert discovered["research"].prompt == "Focus on traceable sources."
    assert discovered["research"].tools == ("web_search", "web_fetch", "write_report")


def test_runtime_composes_prompt_and_filters_tools(tmp_path):
    write_skill(
        tmp_path,
        "research",
        frontmatter="""
name: research
tools:
  - web_search
  - web_fetch
  - write_report
""",
        prompt="Cite pages before drafting the report.",
    )

    config = AppConfig(
        model_name="openai:gpt-4o-mini",
        system_prompt="Base prompt.",
        skills_dir=tmp_path,
        enabled_skills=("research",),
    )

    skills = get_skills(config)
    prompt = get_system_prompt(config, skills=skills)
    tools = get_tools(config, skills=skills)

    assert "[skill:research]" in prompt
    assert "Cite pages before drafting the report." in prompt
    assert [tool.name for tool in tools] == ["web_search", "web_fetch", "write_report"]


def test_get_system_prompt_loads_all_discovered_skills_by_default(tmp_path):
    write_skill(
        tmp_path,
        "research",
        frontmatter="name: research",
        prompt="Research prompt.",
    )
    write_skill(
        tmp_path,
        "writer",
        frontmatter="name: writer",
        prompt="Writer prompt.",
    )

    config = AppConfig(
        model_name="openai:gpt-4o-mini",
        system_prompt="Base prompt.",
        skills_dir=tmp_path,
        enabled_skills=("research",),
    )

    prompt = get_system_prompt(config)

    assert "[skill:research]" in prompt
    assert "[skill:writer]" in prompt


def test_runtime_keeps_full_toolset_for_prompt_only_skill(tmp_path):
    write_skill(
        tmp_path,
        "writer",
        frontmatter="name: writer",
        prompt="Prefer concise markdown sections.",
    )

    config = AppConfig(
        model_name="openai:gpt-4o-mini",
        skills_dir=tmp_path,
        enabled_skills=("writer",),
    )

    tools = get_tools(config)

    assert [tool.name for tool in tools] == [
        "ask_clarification",
        "web_search",
        "web_fetch",
        "write_report",
        "present_files",
    ]


def test_runtime_rejects_unknown_tool_requested_by_skill(tmp_path):
    write_skill(
        tmp_path,
        "broken",
        frontmatter="""
name: broken
tools:
  - missing_tool
""",
        prompt="This should fail.",
    )
    config = AppConfig(
        model_name="openai:gpt-4o-mini",
        skills_dir=tmp_path,
        enabled_skills=("broken",),
    )

    with pytest.raises(ValueError, match="missing_tool"):
        get_tools(config)
