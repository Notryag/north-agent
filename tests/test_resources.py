from pathlib import Path

import pytest

from app.resources import parse_resource_uri, resolve_resource_uri


def test_parse_resource_uri_normalizes_skill_default_file():
    resource = parse_resource_uri("skill://research")

    assert resource.scheme == "skill"
    assert resource.value == "research/SKILL.md"


def test_resolve_resource_uri_maps_domains_to_thread_paths(tmp_path: Path):
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    skill_path = resolve_resource_uri(
        "skill://research/SKILL.md",
        thread_id="thread-1",
        skills_dir=skills_dir,
        thread_base_dir=tmp_path / ".deerflow",
    )
    upload_path = resolve_resource_uri(
        "upload://paper.pdf",
        thread_id="thread-1",
        skills_dir=skills_dir,
        thread_base_dir=tmp_path / ".deerflow",
    )
    workspace_path = resolve_resource_uri(
        "workspace://notes/chunk-1.md",
        thread_id="thread-1",
        skills_dir=skills_dir,
        thread_base_dir=tmp_path / ".deerflow",
    )
    output_path = resolve_resource_uri(
        "output://report.md",
        thread_id="thread-1",
        skills_dir=skills_dir,
        thread_base_dir=tmp_path / ".deerflow",
    )
    memory_path = resolve_resource_uri(
        "memory://entities/openai.json",
        thread_id="thread-1",
        skills_dir=skills_dir,
        thread_base_dir=tmp_path / ".deerflow",
    )

    assert skill_path == skills_dir / "research" / "SKILL.md"
    assert upload_path == tmp_path / ".deerflow" / "threads" / "thread-1" / "uploads" / "paper.pdf"
    assert workspace_path == tmp_path / ".deerflow" / "threads" / "thread-1" / "workspace" / "notes" / "chunk-1.md"
    assert output_path == tmp_path / ".deerflow" / "threads" / "thread-1" / "outputs" / "report.md"
    assert memory_path == tmp_path / ".deerflow" / "threads" / "thread-1" / "memory" / "entities" / "openai.json"


def test_resolve_resource_uri_rejects_escape_attempts(tmp_path: Path):
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    with pytest.raises(ValueError, match="must not escape"):
        parse_resource_uri("workspace://../secret.txt")
