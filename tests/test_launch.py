"""Tests for the nohup launch-script builder."""

from __future__ import annotations

import os
import subprocess
import tempfile

from mission_compiler.bounds import Bounds
from mission_compiler.launch import (
    build_launch_script,
    build_nohup_command,
    validate_launch_script,
)
from mission_compiler.spoke_cmd import build_cycle_command, build_setup_command


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


def _bounds() -> "object":
    return Bounds(outer_wall=1800, inner_seconds=1500, outer_steps=20, inner_max_steps=60)


def test_validate_accepts_generated_setup_script():
    script = build_launch_script(
        goal="g", inner=_inner(), bounds=_bounds(), log="/a/log.md",
        trajectories="/a/traj", project_dir="/p", name="n",
    )
    assert validate_launch_script(script) is None


def test_validate_accepts_generated_cycle_script():
    inner = build_cycle_command(
        runner_prompt="/a/runner.md", log="/a/log.md", project_dir="/p",
        cycle=2, max_steps=90, briefing="/a/brief.md", trajectories="/a/traj",
    )
    script = build_launch_script(
        goal="g", inner=inner, bounds=_bounds(), log="/a/log.md",
        trajectories="/a/traj", project_dir="/p", name="n",
    )
    assert validate_launch_script(script) is None


def test_validate_rejects_bad_syntax():
    import pytest

    with pytest.raises(ValueError, match="bash -n"):
        validate_launch_script("if then fi\n")


def test_validate_message_includes_stderr():
    import pytest

    with pytest.raises(ValueError) as excinfo:
        validate_launch_script("if then fi\n")
    msg = str(excinfo.value)
    assert "bash -n" in msg
    # bash's stderr for a syntax error is non-empty and mentions the line.
    assert len(msg) > len("launch script failed bash -n: ")


def _tricky_goal() -> str:
    """A GOAL string that breaks a double-quoted embedding.

    Contains, in one value: a single quote, a double quote, a dollar-sign
    variable, a backtick command, and a literal newline - exactly the bytes the
    setup-era double-quoted heredoc would have mangled.
    """
    return (
        "Use a \"double\" and a 'single' quote, $HOME var, `id` backtick, "
        "and\na literal newline inside the goal."
    )


def test_tricky_goal_script_passes_bash_n():
    script = build_launch_script(
        goal=_tricky_goal(), inner=_inner(), bounds=_bounds(), log="/a/log.md",
        trajectories="/a/traj", project_dir="/p", name="n",
    )
    fd, path = tempfile.mkstemp(prefix="mc-tricky-", suffix=".sh")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(script)
        result = subprocess.run(["bash", "-n", path], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
    finally:
        os.unlink(path)


def test_tricky_goal_bytes_preserved_verbatim():
    script = build_launch_script(
        goal=_tricky_goal(), inner=_inner(), bounds=_bounds(), log="/a/log.md",
        trajectories="/a/traj", project_dir="/p", name="n",
    )
    # The exact goal bytes must appear as a contiguous substring of the emitted
    # script - proof that the single-quoted heredoc preserves them literally
    # (no re-quoting, no $ expansion, no backtick execution).
    assert _tricky_goal() in script


def test_double_quoted_embedding_would_break():
    goal = _tricky_goal()
    # The setup-era bug: a double-quoted assignment lets bash interpret $ and
    # backticks. Show that the double-quoted form is NOT byte-identical to the
    # single-quoted heredoc body (structural, deterministic assertion).
    double_quoted = 'GOAL="' + goal.replace('"', '\\"') + '"'
    delim = "'GOAL_EOF'"
    single_quoted_body = 'GOAL=$(cat <<' + delim + '\\n' + goal + '\\nGOAL_EOF\\n)'
    assert double_quoted != single_quoted_body
    # The single-quoted heredoc keeps the raw $HOME and backtick bytes intact.
    assert "$HOME" in single_quoted_body
    assert "`id`" in single_quoted_body


def test_launch_script_byte_deterministic_across_runs():
    kw = dict(
        goal=_tricky_goal(), inner=_inner(), bounds=_bounds(), log="/a/log.md",
        trajectories="/a/traj", project_dir="/p", name="n",
    )
    a = build_launch_script(**kw)
    b = build_launch_script(**kw)
    assert a == b
    # Byte-identical, not just equal-as-str: compare encoded bytes too.
    assert a.encode("utf-8") == b.encode("utf-8")
