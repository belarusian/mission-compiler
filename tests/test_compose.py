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
