"""Tests for GOAL composition (v3 deltas inline)."""

from __future__ import annotations

from mission_compiler.goal import compose_goal


def _goal(**kw) -> str:
    base = dict(
        spoke="cycle-implementation",
        cycles=12,
        repo="belarusian/mission-compiler",
        seed="/home/sasha/Research/four",
        project_dir="/home/sasha/AI/mission-compiler/proj",
        ai_dir="/home/sasha/AI/mission-compiler/ai",
        name="mission-compiler",
    )
    base.update(kw)
    return compose_goal("Build the mission compiler.", **base)


def test_goal_contains_mission():
    assert "Build the mission compiler." in _goal()


def test_goal_contains_all_v3_deltas():
    g = _goal()
    assert "Phase 0 PRE-FLIGHT" in g
    assert "Phase 5 ISSUE SWEEP" in g
    assert "BOUNDED POST-PLAN POLISH CLASS" in g
    assert "INCOMPLETE LOG NOTE" in g


def test_goal_includes_repo_and_seed():
    g = _goal()
    assert "belarusian/mission-compiler" in g
    assert "/home/sasha/Research/four" in g


def test_goal_omits_repo_when_none():
    g = _goal(repo=None)
    assert "GitHub repo:" not in g


def test_goal_omits_seed_when_none():
    g = _goal(seed=None)
    assert "Seed (read-only" not in g


def test_goal_is_deterministic():
    assert _goal() == _goal()


def test_goal_strips_mission_whitespace():
    g = compose_goal(
        "  padded mission  ",
        spoke="project-setup",
        cycles=1,
        repo=None,
        seed=None,
        project_dir="p",
        ai_dir="a",
        name="n",
    )
    assert "Mission: padded mission" in g
