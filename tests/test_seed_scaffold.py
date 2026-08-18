"""Tests for the seed scaffold plan."""

from __future__ import annotations

from mission_compiler.seed_scaffold import build_seed_scaffold


def test_scaffold_with_seed_references_it():
    s = build_seed_scaffold(
        seed="/seed", project_dir="/p", name="n", ai_dir="/a"
    )
    assert s.seed_path == "/seed"
    actions = [i.action for i in s.items]
    assert "reference" in actions
    ref = next(i for i in s.items if i.action == "reference")
    assert ref.path == "/seed"


def test_scaffold_without_seed_has_no_reference():
    s = build_seed_scaffold(seed=None, project_dir="/p", name="n", ai_dir="/a")
    assert s.seed_path is None
    assert all(i.action != "reference" for i in s.items)


def test_scaffold_creates_package_tests_and_config():
    s = build_seed_scaffold(seed=None, project_dir="/p", name="n", ai_dir="/a")
    paths = [i.path for i in s.items]
    assert "/p/n/__init__.py" in paths
    assert "/p/tests/test_smoke.py" in paths
    assert "/p/pyproject.toml" in paths


def test_scaffold_creates_ai_artifacts():
    s = build_seed_scaffold(seed=None, project_dir="/p", name="n", ai_dir="/a")
    paths = [i.path for i in s.items]
    assert "/a/cycle-001-n-gate.md" in paths
    assert "/a/n-cycle-runner-prompt.md" in paths
    assert "/a/n-cycle-1-briefing.md" in paths


def test_scaffold_render_is_deterministic():
    a = build_seed_scaffold(seed="/s", project_dir="/p", name="n", ai_dir="/a")
    b = build_seed_scaffold(seed="/s", project_dir="/p", name="n", ai_dir="/a")
    assert a.render() == b.render()


def test_scaffold_render_mentions_read_only():
    s = build_seed_scaffold(seed="/s", project_dir="/p", name="n", ai_dir="/a")
    assert "read-only" in s.render()
