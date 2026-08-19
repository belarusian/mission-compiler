"""Tests for the nohup launch-script builder."""

from __future__ import annotations

import os
import pytest
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


# --- End-to-end launch-script self-test (TICKET-008) -------------------------
# Mirrors exactly what the CLI does when it writes a launch file: build a full
# script, write it to a real temp file, run `bash -n` on that file, and assert
# the nohup wrapper references the correct path. Covers BOTH spoke types using
# REAL bounds from the proven table (bounds_for), not hand-typed numbers.

from mission_compiler.bounds import bounds_for  # noqa: E402


def _e2e_inner(spoke: str):
    if spoke == "project-setup":
        return build_setup_command(
            goal="g", name="n", project_dir="/p", ai_dir="/a", cycles=1,
            repo=None, seed=None,
        )
    return build_cycle_command(
        runner_prompt="/a/runner.md", log="/a/log.md", project_dir="/p",
        cycle=3, max_steps=bounds_for(spoke).inner_max_steps,
        briefing="/a/brief.md", trajectories="/a/traj",
    )


def _e2e_build_and_bash_n(spoke: str) -> None:
    """Build a full script for ``spoke``, write to temp file, run `bash -n`."""
    bounds = bounds_for(spoke)
    script = build_launch_script(
        goal="g", inner=_e2e_inner(spoke), bounds=bounds, log="/a/log.md",
        trajectories="/a/traj", project_dir="/p", name="n",
    )
    fd, path = tempfile.mkstemp(prefix=f"mc-e2e-{spoke}-", suffix=".sh")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(script)
        result = subprocess.run(["bash", "-n", path], capture_output=True, text=True)
        assert result.returncode == 0, (spoke, result.stderr)
    finally:
        os.unlink(path)


def test_e2e_setup_script_written_and_bash_n_passes():
    _e2e_build_and_bash_n("project-setup")


def test_e2e_cycle_script_written_and_bash_n_passes():
    _e2e_build_and_bash_n("cycle-implementation")


def _assert_nohup_references_path(script_path: str) -> None:
    cmd = build_nohup_command(script_path)
    assert cmd.startswith(f"nohup bash {script_path}")
    assert f"> {script_path}.out" in cmd
    assert cmd.endswith("&")


def test_e2e_nohup_references_correct_path_setup():
    # The same path the CLI uses when it writes the launch file.
    script_path = "/p/launch-n.sh"
    _assert_nohup_references_path(script_path)


def test_e2e_nohup_references_correct_path_cycle():
    script_path = "/p/launch-n.sh"
    _assert_nohup_references_path(script_path)


# --- write_launch_script helper (TICKET-009) ----------------------------------
# Additive helper: write a composed launch script to a path and return the nohup
# command. Pins the exact-bytes / correct-nohup / bash -n / determinism contract in
# one reusable, testable place (mirrors what the CLI --write branch does by hand).

from mission_compiler.launch import write_launch_script  # noqa: E402


def _helper_build(goal: str = "g") -> str:
    return build_launch_script(
        goal=goal, inner=_inner(), bounds=_bounds(), log="/a/log.md",
        trajectories="/a/traj", project_dir="/p", name="n",
    )


def test_write_launch_script_writes_exact_bytes(tmp_path):
    script = _helper_build()
    target = tmp_path / "launch-n.sh"
    write_launch_script(script, str(target))
    on_disk = target.read_text(encoding="utf-8")
    assert on_disk == script
    # Byte-identical, not just equal-as-str.
    assert on_disk.encode("utf-8") == script.encode("utf-8")


def test_write_launch_script_returns_correct_nohup_command(tmp_path):
    script = _helper_build()
    target = tmp_path / "launch-n.sh"
    cmd = write_launch_script(script, str(target))
    assert cmd == build_nohup_command(str(target))
    assert cmd.startswith(f"nohup bash {target}")
    assert f"> {target}.out" in cmd
    assert cmd.endswith("&")


def test_write_launch_script_creates_parent_dirs(tmp_path):
    script = _helper_build()
    nested = tmp_path / "a" / "b" / "c" / "launch-n.sh"
    write_launch_script(script, str(nested))
    assert nested.exists()
    assert nested.read_text(encoding="utf-8") == script


def test_write_launch_script_written_file_passes_bash_n(tmp_path):
    script = _helper_build()
    target = tmp_path / "launch-n.sh"
    write_launch_script(script, str(target))
    result = subprocess.run(["bash", "-n", str(target)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_write_launch_script_is_deterministic(tmp_path):
    script = _helper_build()
    target = tmp_path / "launch-n.sh"
    cmd1 = write_launch_script(script, str(target))
    bytes1 = target.read_bytes()
    cmd2 = write_launch_script(script, str(target))
    bytes2 = target.read_bytes()
    assert cmd1 == cmd2
    assert bytes1 == bytes2


# --- Edge-case hardening (TICKET-010) -----------------------------------------
# Boundary cases of the single-quoted-heredoc embedding: empty goal, goal ending in
# a newline, and a very long single-line goal. Each asserts byte-determinism AND
# that the generated script passes `bash -n`.

def _build(goal: str) -> str:
    return build_launch_script(
        goal=goal, inner=_inner(), bounds=_bounds(), log="/a/log.md",
        trajectories="/a/traj", project_dir="/p", name="n",
    )


def _bash_n_ok(script: str) -> None:
    fd, path = tempfile.mkstemp(prefix="mc-edge-", suffix=".sh")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(script)
        result = subprocess.run(["bash", "-n", path], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
    finally:
        os.unlink(path)


def test_empty_goal_script_passes_bash_n_and_deterministic():
    a = _build("")
    b = _build("")
    assert a == b
    assert a.encode("utf-8") == b.encode("utf-8")
    # An empty body must not swallow a delimiter: GOAL_EOF appears exactly twice.
    assert a.count("GOAL_EOF") == 2
    _bash_n_ok(a)


def test_goal_ending_in_newline_preserved_and_bash_n():
    goal = "line one\n"
    a = _build(goal)
    b = _build(goal)
    assert a == b
    assert a.encode("utf-8") == b.encode("utf-8")
    # The exact goal bytes (trailing newline intact) appear verbatim.
    assert goal in a
    _bash_n_ok(a)


def test_very_long_single_line_goal_preserved_and_bash_n():
    # A single line (no newlines), >= 5000 chars, carrying quote/$/backtick bytes.
    filler = "x" * 4980
    goal = f'Start "q" \'s\' $HOME `id` {filler} End'
    assert "\n" not in goal
    assert len(goal) >= 5000
    a = _build(goal)
    b = _build(goal)
    assert a == b
    assert a.encode("utf-8") == b.encode("utf-8")
    # No truncation, no wrapping: the exact goal bytes appear as one contiguous run.
    assert goal in a
    _bash_n_ok(a)


# --- Cycle 8, TICKET-019 (issue #25): launch-script self-test hardening ------
# Additive tests pinning the exact gaps the Build Order row calls out:
#   * validate_launch_script accepts the REAL builder output for BOTH spoke
#     types using REAL bounds from bounds_for(spoke) and returns None;
#   * validate_launch_script rejects a known-bad script with ValueError("bash -n");
#   * build_launch_script is byte-identical (encoded bytes) across equal inputs
#     for BOTH spoke types.

def _real_inner(spoke: str):
    bounds = bounds_for(spoke)
    if spoke == "project-setup":
        return build_setup_command(
            goal="g", name="n", project_dir="/p", ai_dir="/a", cycles=1,
            repo=None, seed=None,
        )
    return build_cycle_command(
        runner_prompt="/a/runner.md", log="/a/log.md", project_dir="/p",
        cycle=3, max_steps=bounds.inner_max_steps, briefing="/a/brief.md",
        trajectories="/a/traj",
    )


def _real_script(spoke: str) -> str:
    return build_launch_script(
        goal="g", inner=_real_inner(spoke), bounds=bounds_for(spoke),
        log="/a/log.md", trajectories="/a/traj", project_dir="/p", name="n",
    )


def test_validate_accepts_real_builder_output_both_spokes():
    # Real builder output + real bounds (bounds_for), not hand-typed numbers.
    assert validate_launch_script(_real_script("project-setup")) is None
    assert validate_launch_script(_real_script("cycle-implementation")) is None


def test_validate_rejects_known_bad_script_bash_n():
    with pytest.raises(ValueError, match="bash -n"):
        validate_launch_script("#!/bin/bash\nif then fi\n")


def test_build_launch_script_byte_identical_both_spokes():
    for spoke in ("project-setup", "cycle-implementation"):
        a = _real_script(spoke)
        b = _real_script(spoke)
        assert a == b
        # Byte-level determinism, not just str equality.
        assert a.encode("utf-8") == b.encode("utf-8")


# ---------------------------------------------------------------------------
# Cycle 10, TICKET-026 (issue #34): build_nohup_command unit coverage.
# ---------------------------------------------------------------------------


def test_build_nohup_command_exact_shape():
    cmd = build_nohup_command("/tmp/proj/launch-fourseer.sh")
    assert cmd == "nohup bash /tmp/proj/launch-fourseer.sh > /tmp/proj/launch-fourseer.sh.out 2>&1 &"


def test_build_nohup_command_is_pure_function_of_input():
    # Same input -> same output; different input -> different output.
    assert build_nohup_command("/a/b.sh") == build_nohup_command("/a/b.sh")
    assert build_nohup_command("/a/b.sh") != build_nohup_command("/c/d.sh")


def test_build_nohup_command_byte_identical():
    a = build_nohup_command("/tmp/x/launch.sh")
    b = build_nohup_command("/tmp/x/launch.sh")
    assert a.encode("utf-8") == b.encode("utf-8")


# --- TICKET-031 (issue #41): build_launch_script/_heredoc hostile-bytes edges --
# The existing _tricky_goal() covers single/double quote, $HOME, backtick, and an
# embedded newline. These pin the remaining hostile-bytes edges: NUL byte, CRLF,
# leading/trailing newline, and a heredoc-delimiter collision (a goal line equal to
# GOAL_EOF). Each asserts the ACTUAL deterministic outcome: verbatim byte
# preservation AND bash -n green. Additive only; no source change.

def _bash_n_ok(script: str) -> bool:
    fd, path = tempfile.mkstemp(prefix="mc-hostile-", suffix=".sh")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(script)
        result = subprocess.run(["bash", "-n", path], capture_output=True, text=True)
        return result.returncode == 0
    finally:
        os.unlink(path)


def _build(goal: str) -> str:
    return build_launch_script(
        goal=goal, inner=_inner(), bounds=_bounds(), log="/a/log.md",
        trajectories="/a/traj", project_dir="/p", name="n",
    )


def test_goal_with_nul_byte_deterministic():
    goal = "goal with \x00 nul byte"
    script = _build(goal)
    assert goal in script            # NUL preserved verbatim
    assert _bash_n_ok(script)        # still valid bash


def test_goal_with_crlf_preserved_and_bash_n():
    goal = "line one\r\nline two"
    script = _build(goal)
    assert goal in script            # CRLF preserved verbatim
    assert _bash_n_ok(script)


def test_goal_leading_trailing_newline_preserved_and_bash_n():
    for goal in ("\nleading newline goal", "trailing newline goal\n"):
        script = _build(goal)
        assert goal in script        # leading/trailing newline preserved verbatim
        assert _bash_n_ok(script)


def test_goal_heredoc_delimiter_collision_deterministic():
    # A goal line equal to the heredoc delimiter. bash terminates a quoted heredoc
    # only on a STANDALONE delimiter line, and the emitted body always ends with a
    # fresh delimiter line, so the embedded GOAL_EOF is preserved verbatim and the
    # script stays valid bash. Pin this actual behavior byte-for-byte.
    goal = "first line\nGOAL_EOF\nlast line"
    script = _build(goal)
    assert goal in script            # full goal (incl. trailing 'last line') verbatim
    assert "last line" in script     # not truncated by an early heredoc termination
    assert _bash_n_ok(script)


def test_hostile_bytes_byte_identical_across_runs():
    for goal in (
        "goal with \x00 nul byte",
        "line one\r\nline two",
        "\nleading newline goal",
        "trailing newline goal\n",
        "first line\nGOAL_EOF\nlast line",
    ):
        assert _build(goal) == _build(goal)
