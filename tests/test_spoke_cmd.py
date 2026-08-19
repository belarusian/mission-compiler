"""Tests for inner spoke command-line construction."""

from __future__ import annotations

from mission_compiler.bounds import bounds_for
from mission_compiler.spoke_cmd import (
    DEFAULT_CYCLE_SPOKE,
    DEFAULT_SETUP_SPOKE,
    bounds_for_spoke,
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


# --- TICKET-003: golden render + quoting round-trip + re-export -----------


def test_setup_command_golden_render():
    """The exact rendered argv order is deterministic and stable."""
    cmd = build_setup_command(
        goal="g",
        name="mission-compiler",
        project_dir="/p",
        ai_dir="/a",
        cycles=12,
        repo="belarusian/mission-compiler",
        seed="/seed",
    )
    assert cmd.render() == (
        f"python3 {DEFAULT_SETUP_SPOKE} --goal g "
        "--name mission-compiler --project-dir /p --ai-dir /a "
        "--cycles 12 --repo belarusian/mission-compiler --seed /seed"
    )


def test_cycle_command_golden_render():
    """The exact rendered argv order is deterministic and stable."""
    cmd = build_cycle_command(
        runner_prompt="/a/rp.md",
        log="/a/log.md",
        project_dir="/p",
        cycle=5,
        max_steps=90,
        briefing="/a/brief.md",
        trajectories="/a/traj",
    )
    assert cmd.render() == (
        f"python3 {DEFAULT_CYCLE_SPOKE} --runner-prompt /a/rp.md "
        "--log /a/log.md --briefing /a/brief.md --project-dir /p "
        "--cycle 5 --trajectories /a/traj --max-steps 90"
    )


def test_render_escapes_embedded_double_quotes():
    """Whitespace tokens are quoted; embedded double quotes are escaped."""
    cmd = build_setup_command(
        goal='a "quoted" goal',
        name="n",
        project_dir="/p",
        ai_dir="/a",
        cycles=1,
        repo=None,
        seed=None,
    )
    rendered = cmd.render()
    # The token is wrapped in double quotes with the inner quotes escaped.
    assert '\\"quoted\\"' in rendered
    assert '"a \\"quoted\\" goal"' in rendered
    # A whitespace-free token stays bare (no quoting).
    assert "--name n" in rendered


def test_bounds_for_spoke_delegates_and_raises():
    """bounds_for_spoke is a thin re-export of bounds.bounds_for."""
    import pytest

    got = bounds_for_spoke("cycle-implementation")
    want = bounds_for("cycle-implementation")
    assert (got.outer_wall, got.inner_seconds, got.outer_steps, got.inner_max_steps) == (
        want.outer_wall,
        want.inner_seconds,
        want.outer_steps,
        want.inner_max_steps,
    )
    with pytest.raises(ValueError, match="unknown spoke"):
        bounds_for_spoke("no-such-spoke")


# ---------------------------------------------------------------------------
# Cycle 11, TICKET-028 (issue #37): _quote whitespace edge coverage.
# Pins the full whitespace-character matrix and the empty / no-whitespace cases
# so a regression in any branch is caught. Additive only; no source change.
# ---------------------------------------------------------------------------


def test_quote_tab_is_quoted():
    from mission_compiler.spoke_cmd import _quote

    assert _quote("a\tb") == '"a\tb"'


def test_quote_leading_and_trailing_space_are_quoted():
    from mission_compiler.spoke_cmd import _quote

    assert _quote(" x") == '" x"'
    assert _quote("x ") == '"x "'


def test_quote_empty_token_is_empty():
    from mission_compiler.spoke_cmd import _quote

    assert _quote("") == ""


def test_quote_no_whitespace_stays_bare():
    from mission_compiler.spoke_cmd import _quote

    assert _quote("abc") == "abc"


def test_quote_embedded_double_without_whitespace_not_escaped():
    # An embedded double quote with NO whitespace is not quoted and the quote is
    # not escaped (escaping only happens inside a quoted token).
    from mission_compiler.spoke_cmd import _quote

    assert _quote('a"b') == 'a"b'


def test_render_composes_quoted_and_bare_tokens():
    # A goal with a tab is quoted; a name with no whitespace stays bare.
    cmd = build_setup_command(
        goal="a\tgoal",
        name="n",
        project_dir="/p",
        ai_dir="/a",
        cycles=1,
        repo=None,
        seed=None,
    )
    rendered = cmd.render()
    assert '"a\tgoal"' in rendered
    assert "--name n" in rendered  # bare, unquoted
