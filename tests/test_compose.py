"""Tests for the top-level compose orchestrator."""

from __future__ import annotations

import pytest

from mission_compiler.compose import compose


def test_compose_setup_returns_all_five_sections():
    launch = compose(
        "Build the mission compiler.",
        cycles=12,
        repo="belarusian/mission-compiler",
        seed="/home/sasha/Research/four",
        spoke="project-setup",
    )
    assert launch.spoke == "project-setup"
    assert launch.goal
    assert launch.inner.argv
    assert launch.bounds.outer_wall > 0
    assert launch.seed_scaffold.items
    assert launch.launch_script.startswith("#!/bin/bash")
    assert launch.nohup_command.startswith("nohup")


def test_compose_cycle_uses_cycle_bounds():
    launch = compose(
        "Run cycle 3.",
        spoke="cycle-implementation",
        cycle=3,
    )
    assert launch.spoke == "cycle-implementation"
    assert launch.bounds.outer_wall == 3600
    assert launch.bounds.inner_max_steps == 90
    # inner command should target cycle 3
    assert "3" in launch.inner.argv


def test_compose_unknown_spoke_raises():
    with pytest.raises(ValueError, match="unknown spoke"):
        compose("m", spoke="nope")


def test_compose_is_deterministic():
    a = compose("Build it.", cycles=5, repo="o/r", seed="/s", spoke="project-setup")
    b = compose("Build it.", cycles=5, repo="o/r", seed="/s", spoke="project-setup")
    assert a.render() == b.render()
    assert a.launch_script == b.launch_script


def test_compose_render_has_all_section_headers():
    launch = compose("Build it.", spoke="project-setup")
    doc = launch.render()
    assert "[1] GOAL" in doc
    assert "[2] INNER SPOKE COMMAND" in doc
    assert "[3] BOUNDS" in doc
    assert "[4] SEED SCAFFOLD" in doc
    assert "[5] NOHUP LAUNCH SCRIPT" in doc


def test_compose_goal_carries_v3_deltas():
    launch = compose("Build it.", spoke="cycle-implementation")
    assert "Phase 0 PRE-FLIGHT" in launch.goal
    assert "Phase 5 ISSUE SWEEP" in launch.goal
    assert "BOUNDED POST-PLAN POLISH CLASS" in launch.goal
    assert "INCOMPLETE LOG NOTE" in launch.goal
