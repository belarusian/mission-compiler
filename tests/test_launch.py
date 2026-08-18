"""Tests for the nohup launch-script builder."""

from __future__ import annotations

from mission_compiler.bounds import Bounds
from mission_compiler.launch import build_launch_script, build_nohup_command
from mission_compiler.spoke_cmd import build_setup_command


def _inner() -> "object":
    return build_setup_command(
        goal="g",
        name="n",
        project_dir="/p",
        ai_dir="/a",
        cycles=1,
        repo=None,
        seed=None,
    )


def test_launch_script_has_shebang_and_pipefail():
    b = Bounds(outer_wall=1800, inner_seconds=1500, outer_steps=20, inner_max_steps=60)
    script = build_launch_script(
        goal="g", inner=_inner(), bounds=b, log="/a/log.md",
        trajectories="/a/traj", project_dir="/p", name="n",
    )
    assert script.startswith("#!/bin/bash")
    assert "set -uo pipefail" in script


def test_launch_script_uses_perl_alarm_with_outer_wall():
    b = Bounds(outer_wall=1800, inner_seconds=1500, outer_steps=20, inner_max_steps=60)
    script = build_launch_script(
        goal="g", inner=_inner(), bounds=b, log="/a/log.md",
        trajectories="/a/traj", project_dir="/p", name="n",
    )
    assert "perl -e 'alarm shift; exec @ARGV' 1800" in script


def test_launch_script_passes_inner_seconds_and_outer_steps():
    b = Bounds(outer_wall=1800, inner_seconds=1500, outer_steps=20, inner_max_steps=60)
    script = build_launch_script(
        goal="g", inner=_inner(), bounds=b, log="/a/log.md",
        trajectories="/a/traj", project_dir="/p", name="n",
    )
    assert "--inner-seconds 1500" in script
    assert "--outer-steps 20" in script


def test_launch_script_is_deterministic():
    b = Bounds(outer_wall=1800, inner_seconds=1500, outer_steps=20, inner_max_steps=60)
    kw = dict(goal="g", inner=_inner(), bounds=b, log="/a/log.md",
              trajectories="/a/traj", project_dir="/p", name="n")
    assert build_launch_script(**kw) == build_launch_script(**kw)


def test_nohup_command_backgrounds():
    cmd = build_nohup_command("/p/launch-n.sh")
    assert cmd.startswith("nohup bash /p/launch-n.sh")
    assert cmd.endswith("&")
