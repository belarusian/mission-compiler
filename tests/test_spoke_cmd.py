"""Tests for inner spoke command-line construction."""

from __future__ import annotations

from mission_compiler.spoke_cmd import (
    DEFAULT_CYCLE_SPOKE,
    DEFAULT_SETUP_SPOKE,
    build_cycle_command,
    build_setup_command,
)


def test_setup_command_has_all_args():
    cmd = build_setup_command(
        goal="g",
        name="mission-compiler",
        project_dir="/p",
        ai_dir="/a",
        cycles=12,
        repo="belarusian/mission-compiler",
        seed="/seed",
    )
    argv = cmd.argv
    assert argv[0] == "python3"
    assert argv[1] == DEFAULT_SETUP_SPOKE
    # --goal, --name, --project-dir, --ai-dir, --cycles, --repo, --seed
    for flag in ("--goal", "--name", "--project-dir", "--ai-dir", "--cycles", "--repo", "--seed"):
        assert flag in argv
    assert "12" in argv
    assert "belarusian/mission-compiler" in argv


def test_setup_command_omits_optional_args():
    cmd = build_setup_command(
        goal="g",
        name="n",
        project_dir="/p",
        ai_dir="/a",
        cycles=3,
        repo=None,
        seed=None,
    )
    assert "--repo" not in cmd.argv
    assert "--seed" not in cmd.argv


def test_cycle_command_has_all_args():
    cmd = build_cycle_command(
        runner_prompt="/a/rp.md",
        log="/a/log.md",
        project_dir="/p",
        cycle=5,
        max_steps=90,
        briefing="/a/brief.md",
        trajectories="/a/traj",
    )
    argv = cmd.argv
    assert argv[1] == DEFAULT_CYCLE_SPOKE
    for flag in ("--runner-prompt", "--log", "--briefing", "--project-dir", "--cycle", "--max-steps", "--trajectories"):
        assert flag in argv
    assert "5" in argv
    assert "90" in argv


def test_cycle_command_omits_optional_briefing():
    cmd = build_cycle_command(
        runner_prompt="/a/rp.md",
        log="/a/log.md",
        project_dir="/p",
        cycle=1,
        max_steps=90,
        briefing=None,
        trajectories=None,
    )
    assert "--briefing" not in cmd.argv
    assert "--trajectories" not in cmd.argv


def test_render_quotes_whitespace_tokens():
    cmd = build_setup_command(
        goal="a goal with spaces",
        name="n",
        project_dir="/p",
        ai_dir="/a",
        cycles=1,
        repo=None,
        seed=None,
    )
    rendered = cmd.render()
    assert '"a goal with spaces"' in rendered
    assert "python3" in rendered
