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


def test_compose_validate_true_accepts_valid_script():
    # validate=True must pass for the real builder output on both spoke types.
    setup = compose("Build it.", cycles=5, repo="o/r", seed="/s",
                    spoke="project-setup", validate=True)
    assert setup.launch_script.startswith("#!/bin/bash")
    cycle = compose("Run cycle 3.", spoke="cycle-implementation", cycle=3,
                    validate=True)
    assert cycle.launch_script.startswith("#!/bin/bash")


def test_compose_validate_false_is_default_and_unchanged():
    # The flag only adds a check; it must never change the emitted bytes.
    base = compose("Build it.", cycles=5, repo="o/r", seed="/s",
                   spoke="project-setup")
    validated = compose("Build it.", cycles=5, repo="o/r", seed="/s",
                        spoke="project-setup", validate=True)
    assert base.launch_script == validated.launch_script
    assert base.render() == validated.render()


def test_compose_validate_raises_on_bad_script():
    # The additive helper must surface a bash -n failure as ValueError.
    from mission_compiler.compose import ComposedLaunch, validate_composed

    bad = ComposedLaunch(
        goal="g",
        inner=base_inner(),
        bounds=base_bounds(),
        seed_scaffold=base_scaffold(),
        launch_script="if then fi\n",
        nohup_command="nohup bash /p/launch-n.sh > /p/launch-n.sh.out 2>&1 &",
        spoke="project-setup",
    )
    with pytest.raises(ValueError, match="bash -n"):
        validate_composed(bad)


def test_validate_composed_accepts_real_launch():
    from mission_compiler.compose import validate_composed

    launch = compose("Build it.", cycles=5, repo="o/r", seed="/s",
                     spoke="project-setup")
    assert validate_composed(launch) is None


def base_inner():
    from mission_compiler.spoke_cmd import build_setup_command

    return build_setup_command(
        goal="g", name="n", project_dir="/p", ai_dir="/a", cycles=1,
        repo=None, seed=None,
    )


def base_bounds():
    from mission_compiler.bounds import Bounds

    return Bounds(outer_wall=1800, inner_seconds=1500, outer_steps=20,
                  inner_max_steps=60)


def base_scaffold():
    from mission_compiler.seed_scaffold import build_seed_scaffold

    return build_seed_scaffold(seed=None, project_dir="/p", name="n", ai_dir="/a")


# ---------------------------------------------------------------------------
# Cycle 6, TICKET-013 (issue #17): opt-in seed_spec wiring into compose.
# ---------------------------------------------------------------------------


def test_compose_seed_spec_none_is_byte_identical_to_fixed():
    from mission_compiler.seed_scaffold import build_seed_scaffold

    base = compose("Build it.", cycles=5, repo="o/r", seed="/s", spoke="project-setup")
    explicit = compose(
        "Build it.", cycles=5, repo="o/r", seed="/s",
        spoke="project-setup", seed_spec=None,
    )
    # explicit None must be indistinguishable from omitting the flag
    assert base.render() == explicit.render()
    assert base.seed_scaffold.render() == explicit.seed_scaffold.render()
    # and it must equal the fixed builder output for the default paths
    fixed = build_seed_scaffold(
        seed="/s",
        project_dir="/home/sasha/AI/mission-compiler/proj",
        name="mission-compiler",
        ai_dir="/home/sasha/AI/mission-compiler/ai",
    )
    assert base.seed_scaffold.render() == fixed.render()


def test_compose_seed_spec_mapping_reflects_classified_entries():
    launch = compose(
        "Build it.", cycles=5, repo="o/r", seed="/s", spoke="project-setup",
        seed_spec={"/s/a.py": "/d/a.py", "/s/b.md": "/s/b.md"},
    )
    doc = launch.render()
    section = doc.split("[4] SEED SCAFFOLD")[1].split("[5] NOHUP LAUNCH SCRIPT")[0]
    # copy line (dest <- source) and reference line both present
    assert "[copy] /d/a.py" in section
    assert "/s/a.py" in section
    assert "[reference] /s/b.md" in section


def test_compose_seed_spec_list_reflects_create_entries():
    launch = compose(
        "Build it.", cycles=5, repo="o/r", seed="/s", spoke="project-setup",
        seed_spec=["pkg/mod.py", "docs/README.md"],
    )
    section = launch.render().split("[4] SEED SCAFFOLD")[1].split("[5] NOHUP LAUNCH SCRIPT")[0]
    assert "[create]" in section
    assert "python module" in section
    assert "markdown doc" in section


def test_compose_seed_spec_deterministic():
    a = compose("Build it.", seed="/s", spoke="project-setup",
                seed_spec={"/s/a.py": "/d/a.py"})
    b = compose("Build it.", seed="/s", spoke="project-setup",
                seed_spec={"/s/a.py": "/d/a.py"})
    assert a.render() == b.render()
    assert a.seed_scaffold.render() == b.seed_scaffold.render()


def test_compose_seed_spec_default_unchanged_vs_explicit_none():
    base = compose("Build it.", cycles=5, repo="o/r", seed="/s", spoke="project-setup")
    explicit = compose(
        "Build it.", cycles=5, repo="o/r", seed="/s",
        spoke="project-setup", seed_spec=None,
    )
    assert base.launch_script == explicit.launch_script
    assert base.render() == explicit.render()


# ---------------------------------------------------------------------------
# Cycle 7, TICKET-017 (issue #22): compose hardening — validate=True with a
# non-None seed_spec still passes bash -n; five sections byte-deterministic
# when both seed and seed_spec are supplied.
# ---------------------------------------------------------------------------


def test_compose_validate_true_with_mapping_seed_spec_passes_bash_n():
    launch = compose(
        "Build it.",
        seed="/s",
        seed_spec={"/s/a.py": "/d/a.py"},
        spoke="project-setup",
        validate=True,
    )
    # No raise means bash -n passed. The scaffold reflects the classified spec.
    section = launch.render().split("[4] SEED SCAFFOLD")[1].split("[5] NOHUP LAUNCH SCRIPT")[0]
    assert "[copy]" in section


def test_compose_validate_true_with_list_seed_spec_passes_bash_n():
    launch = compose(
        "Build it.",
        seed="/s",
        seed_spec=["pkg/mod.py"],
        spoke="project-setup",
        validate=True,
    )
    section = launch.render().split("[4] SEED SCAFFOLD")[1].split("[5] NOHUP LAUNCH SCRIPT")[0]
    assert "[create]" in section


def test_compose_seed_and_seed_spec_together_byte_deterministic():
    a = compose(
        "Build it.",
        seed="/s",
        seed_spec={"/s/a.py": "/d/a.py"},
        spoke="project-setup",
    )
    b = compose(
        "Build it.",
        seed="/s",
        seed_spec={"/s/a.py": "/d/a.py"},
        spoke="project-setup",
    )
    assert a.render() == b.render()


def test_compose_seed_and_seed_spec_sections_stable():
    launch = compose(
        "Build it.",
        seed="/s",
        seed_spec={"/s/a.py": "/d/a.py"},
        spoke="project-setup",
    )
    rendered = launch.render()
    # All five section headers present and stable.
    for header in (
        "[1] GOAL",
        "[2] INNER SPOKE COMMAND",
        "[3] BOUNDS",
        "[4] SEED SCAFFOLD",
        "[5] NOHUP LAUNCH SCRIPT",
    ):
        assert header in rendered
    # The scaffold section reflects the classified spec (not the fixed builder).
    section = rendered.split("[4] SEED SCAFFOLD")[1].split("[5] NOHUP LAUNCH SCRIPT")[0]
    assert "[copy]" in section


# --- TICKET-030 (issue #40): compose with EVERY flag combined end-to-end ------
# The Build Order plan is complete; this pins the full composition path when all
# opt-in axes (--seed-spec, --config) are active simultaneously, for BOTH spokes.
# Additive only: no change to compose() or any public signature.

_EVERY_FLAG_SEED_SPEC = {
    "/home/sasha/Research/four/run.py": "run.py",   # copy (source != dest)
    "README.md": "README.md",                        # reference (source == dest)
}


def _every_flag_kwargs(spoke: str, cycle: int) -> dict:
    """Every compose() keyword argument set at once (the full flag surface)."""
    return dict(
        cycles=12,
        repo="belarusian/fourseer",
        seed="/home/sasha/Research/four",
        seed_spec=dict(_EVERY_FLAG_SEED_SPEC),
        spoke=spoke,
        name="fourseer",
        project_dir="/home/sasha/AI/fourseer/proj",
        ai_dir="/home/sasha/AI/fourseer/ai",
        cycle=cycle,
        run_py="/home/sasha/Research/four/run.py",
        config="single-llm-long-pass",   # opt-in LLM-config bounds axis
        validate=True,                    # fail-fast bash -n validation
    )


def _scaffold_section(doc: str) -> str:
    return doc.split("[4] SEED SCAFFOLD")[1].split("[5] NOHUP LAUNCH SCRIPT")[0]


def test_compose_every_flag_combined_setup():
    from mission_compiler.compose import validate_composed

    launch = compose("Build fourseer.", **_every_flag_kwargs("project-setup", 1))
    rendered = launch.render()
    for header in (
        "[1] GOAL",
        "[2] INNER SPOKE COMMAND",
        "[3] BOUNDS",
        "[4] SEED SCAFFOLD",
        "[5] NOHUP LAUNCH SCRIPT",
    ):
        assert header in rendered
    # config wins over spoke-based bounds: single-llm-long-pass -> outer wall 10800s.
    assert "outer wall (perl alarm): 10800s" in rendered
    # scaffold reflects the classified mapping (copy + reference), not the fixed builder.
    section = _scaffold_section(rendered)
    assert "[copy]" in section
    assert "[reference]" in section
    # validate=True did not raise; re-validate explicitly to be sure it is valid bash.
    validate_composed(launch)


def test_compose_every_flag_combined_cycle():
    from mission_compiler.compose import validate_composed

    launch = compose("Run cycle 7.", **_every_flag_kwargs("cycle-implementation", 7))
    rendered = launch.render()
    for header in (
        "[1] GOAL",
        "[2] INNER SPOKE COMMAND",
        "[3] BOUNDS",
        "[4] SEED SCAFFOLD",
        "[5] NOHUP LAUNCH SCRIPT",
    ):
        assert header in rendered
    # config row still selected for the cycle spoke.
    assert "outer wall (perl alarm): 10800s" in rendered
    section = _scaffold_section(rendered)
    assert "[copy]" in section
    assert "[reference]" in section
    validate_composed(launch)


def test_compose_every_flag_combined_byte_identical():
    for spoke, cycle in (("project-setup", 1), ("cycle-implementation", 7)):
        a = compose("Build fourseer.", **_every_flag_kwargs(spoke, cycle))
        b = compose("Build fourseer.", **_every_flag_kwargs(spoke, cycle))
        assert a.render() == b.render()
        assert a.launch_script == b.launch_script


def test_compose_private_end_to_end():
    """TICKET-033: compose(repo, private=True) threads --private + GOAL marker."""
    launch = compose(
        "Build the mission compiler.",
        cycles=12,
        repo="o/n",
        private=True,
        spoke="project-setup",
    )
    argv = launch.inner.argv
    assert "--private" in argv
    i = argv.index("o/n")
    assert argv[i + 1] == "--private"
    assert "GitHub repo: o/n (private)" in launch.goal


def test_compose_without_private_byte_identical():
    """TICKET-033 regression pin: no --private anywhere, no (private) marker."""
    launch = compose(
        "Build the mission compiler.",
        cycles=12,
        repo="o/n",
        seed="/home/sasha/Research/four",
        spoke="project-setup",
    )
    assert "--private" not in launch.inner.argv
    assert "(private)" not in launch.goal
    # The public repo line is unchanged.
    assert "GitHub repo: o/n" in launch.goal
    # Deterministic: a second identical call renders byte-identically.
    again = compose(
        "Build the mission compiler.",
        cycles=12,
        repo="o/n",
        seed="/home/sasha/Research/four",
        spoke="project-setup",
    )
    assert launch.render() == again.render()
