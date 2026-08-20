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


# --- TICKET-002: per-spoke delta coverage + byte-level determinism --------

#: The four v3 delta markers that must appear in every composed GOAL.
_DELTA_MARKERS = (
    "Phase 0 PRE-FLIGHT",
    "Phase 5 ISSUE SWEEP",
    "BOUNDED POST-PLAN POLISH CLASS",
    "INCOMPLETE LOG NOTE",
)


def _goal_for_spoke(spoke: str) -> str:
    return compose_goal(
        "Build the mission compiler.",
        spoke=spoke,
        cycles=12,
        repo="belarusian/mission-compiler",
        seed="/home/sasha/Research/four",
        project_dir="/home/sasha/AI/mission-compiler/proj",
        ai_dir="/home/sasha/AI/mission-compiler/ai",
        name="mission-compiler",
    )


def test_goal_deltas_present_for_project_setup():
    g = _goal_for_spoke("project-setup")
    for marker in _DELTA_MARKERS:
        assert marker in g


def test_goal_deltas_present_for_cycle_implementation():
    g = _goal_for_spoke("cycle-implementation")
    for marker in _DELTA_MARKERS:
        assert marker in g


def test_goal_spoke_field_echoed_per_spoke():
    assert "Spoke: project-setup" in _goal_for_spoke("project-setup")
    assert "Spoke: cycle-implementation" in _goal_for_spoke("cycle-implementation")


def test_goal_byte_identical_across_processes(tmp_path):
    """Two separate interpreter invocations must emit byte-identical GOAL text.

    Stronger than same-process equality: it rules out hidden state or ordering
    nondeterminism leaking into the composed output. Inputs are fixed (no
    timestamps, no randomness).
    """
    import subprocess
    import sys

    code = (
        "from mission_compiler.goal import compose_goal; "
        "print(compose_goal('Build the mission compiler.', spoke='project-setup', "
        "cycles=12, repo='belarusian/mission-compiler', "
        "seed='/home/sasha/Research/four', "
        "project_dir='/home/sasha/AI/mission-compiler/proj', "
        "ai_dir='/home/sasha/AI/mission-compiler/ai', "
        "name='mission-compiler'), end='')"
    )
    out_a = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, check=True
    ).stdout
    out_b = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, check=True
    ).stdout
    assert out_a == out_b
    # Sanity: the output is non-trivial and carries the deltas.
    for marker in _DELTA_MARKERS:
        assert marker.encode() in out_a


def test_goal_repo_private_line():
    """TICKET-033: repo+private -> 'GitHub repo: o/n (private)'."""
    g = _goal(repo="o/n", private=True)
    assert "GitHub repo: o/n (private)" in g


def test_goal_repo_public_line_unchanged():
    """TICKET-033: repo only (private=False) -> 'GitHub repo: o/n', no marker."""
    g = _goal(repo="o/n", private=False)
    assert "GitHub repo: o/n" in g
    assert "(private)" not in g


def test_goal_repo_none_private_no_line():
    """TICKET-033: repo=None with private=True -> no GitHub repo line at all."""
    g = _goal(repo=None, private=True)
    assert "GitHub repo:" not in g
