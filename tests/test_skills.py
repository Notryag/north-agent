from pathlib import Path

from app.config import AppConfig, PROJECT_ROOT
from app.runtime import get_skills, get_system_prompt
from app.skills import discover_skills, load_skill_body


def write_skill(
    tmp_path: Path,
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


def test_discover_skills_loads_frontmatter_only(tmp_path):
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
    assert discovered["research"].tools == ("web_search", "web_fetch", "write_report")
    assert not hasattr(discovered["research"], "prompt")


def test_load_skill_body_reads_main_markdown_body(tmp_path):
    write_skill(
        tmp_path,
        "research",
        frontmatter="name: research",
        prompt="Focus on traceable sources.",
    )
    skill = discover_skills(tmp_path)["research"]

    body = load_skill_body(skill)

    assert body == "Focus on traceable sources."


def test_runtime_returns_all_discovered_skills_by_default(tmp_path):
    write_skill(tmp_path, "research", frontmatter="name: research")
    write_skill(tmp_path, "writer", frontmatter="name: writer")

    config = AppConfig(
        model_name="openai:gpt-4o-mini",
        skills_dir=tmp_path,
    )

    skills = get_skills(config)

    assert [skill.name for skill in skills] == ["research", "writer"]


def test_runtime_filters_available_skills_when_requested(tmp_path):
    write_skill(tmp_path, "research", frontmatter="name: research")
    write_skill(tmp_path, "writer", frontmatter="name: writer")
    config = AppConfig(
        model_name="openai:gpt-4o-mini",
        skills_dir=tmp_path,
    )

    skills = get_skills(config, skill_names=("writer",))

    assert [skill.name for skill in skills] == ["writer"]


def test_system_prompt_injects_skill_catalog_not_body(tmp_path):
    write_skill(
        tmp_path,
        "research",
        frontmatter="""
name: research
description: Web research workflow
""",
        prompt="Detailed instructions that should not be injected directly.",
    )
    config = AppConfig(
        model_name="openai:gpt-4o-mini",
        system_prompt="Base prompt.",
        skills_dir=tmp_path,
    )

    prompt = get_system_prompt(config)

    assert "<skill_system>" in prompt
    assert "<available_skills>" in prompt
    assert "<name>research</name>" in prompt
    assert "<description>Web research workflow</description>" in prompt
    assert "<location>skill://research/SKILL.md</location>" in prompt
    assert "Detailed instructions that should not be injected directly." not in prompt


def test_project_default_skills_support_research_report_loop():
    skills = discover_skills(PROJECT_ROOT / "skills")

    assert [name for name in skills if name in {"research", "writer"}] == ["research", "writer"]
    assert skills["research"].tools == ("web_search", "web_fetch", "write_report", "present_files")
    assert skills["writer"].tools == ("write_report", "present_files")


def test_project_default_prompt_exposes_skill_catalog_not_bodies():
    config = AppConfig(
        model_name="openai:gpt-4o-mini",
        system_prompt="Base prompt.",
        skills_dir=PROJECT_ROOT / "skills",
    )

    prompt = get_system_prompt(config)

    assert "<name>research</name>" in prompt
    assert "<location>skill://research/SKILL.md</location>" in prompt
    assert "<name>writer</name>" in prompt
    assert "<location>skill://writer/SKILL.md</location>" in prompt
    assert "Use this skill when the user asks for web research" not in prompt
    assert "Use this skill when the user asks to draft" not in prompt
