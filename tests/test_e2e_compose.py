"""End-to-end integration tests: compose a REAL four project end-to-end.

This is the "E2E + hardening" Build Order row (cycles 9-10). It drives the
public ``compose(...)`` API with a realistic project (name, repo, seed, and an
explicit seed_spec) and asserts the full contract for BOTH spoke types:

  * all five rendered sections are present;
  * ``validate_composed(launch)`` is green (``bash -n`` passes, no raise);
  * two equal calls are byte-identical (render + launch_script);
  * the scaffold section reflects the classified seed_spec (not the fixed
    builder);
  * the GOAL carries the project name and repo.

Additive tests only; ``mission_compiler/compose.py`` is read-only here.
"""

from __future__ import annotations

import pytest

from mission_compiler.compose import compose, validate_composed


#: A realistic four-project composition used across the E2E suite.
MISSION = "Build fourseer: a deterministic fleet supervisor for four projects."
NAME = "fourseer"
REPO = "belarusian/fourseer"
SEED = "/home/sasha/Research/four"
PROJECT_DIR = "/home/sasha/AI/fourseer/proj"
AI_DIR = "/home/sasha/AI/fourseer/ai"

#: A representative seed spec: one copy (source -> dest) + one reference.
SEED_SPEC = {
    "/home/sasha/Research/four/run.py": "run.py",
    "README.md": "README.md",
}

FIVE_HEADERS = (
    "[1] GOAL",
    "[2] INNER SPOKE COMMAND",
    "[3] BOUNDS",
    "[4] SEED SCAFFOLD",
    "[5] NOHUP LAUNCH SCRIPT",
)


def _compose(spoke: str, **kw):
    return compose(
        MISSION,
        cycles=12,
        repo=REPO,
        seed=SEED,
        name=NAME,
        project_dir=PROJECT_DIR,
        ai_dir=AI_DIR,
        spoke=spoke,
        seed_spec=dict(SEED_SPEC),
        **kw,
    )


def _scaffold_section(doc: str) -> str:
    return doc.split("[4] SEED SCAFFOLD")[1].split("[5] NOHUP LAUNCH SCRIPT")[0]


# --- TICKET-018 (issue #24): five sections + validate green + determinism ----


def test_e2e_setup_real_project_five_sections():
    doc = _compose("project-setup").render()
    for header in FIVE_HEADERS:
        assert header in doc


def test_e2e_cycle_real_project_five_sections():
    doc = _compose("cycle-implementation", cycle=5).render()
    for header in FIVE_HEADERS:
        assert header in doc


def test_e2e_setup_real_project_validate_composed_green():
    launch = _compose("project-setup")
    # No raise means bash -n passed; the helper returns None on success.
    assert validate_composed(launch) is None


def test_e2e_cycle_real_project_validate_composed_green():
    launch = _compose("cycle-implementation", cycle=5)
    assert validate_composed(launch) is None


def test_e2e_real_project_byte_identical_across_calls():
    a = _compose("project-setup")
    b = _compose("project-setup")
    assert a.render() == b.render()
    assert a.launch_script == b.launch_script
    # Byte-level, not just str equality.
    assert a.render().encode("utf-8") == b.render().encode("utf-8")


def test_e2e_cycle_real_project_byte_identical_across_calls():
    a = _compose("cycle-implementation", cycle=5)
    b = _compose("cycle-implementation", cycle=5)
    assert a.render() == b.render()
    assert a.launch_script.encode("utf-8") == b.launch_script.encode("utf-8")


def test_e2e_real_project_scaffold_reflects_seed_spec():
    doc = _compose("project-setup").render()
    section = _scaffold_section(doc)
    # The copy entry is classified (dest <- source), not the fixed builder.
    assert "[copy] /home/sasha/AI/fourseer/proj/run.py" in section
    assert "copy from /home/sasha/Research/four/run.py" in section
    assert "[reference]" in section


def test_e2e_real_project_goal_carries_name_and_repo():
    launch = _compose("project-setup")
    assert f"Project: {NAME}" in launch.goal
    assert f"GitHub repo: {REPO}" in launch.goal
    assert f"Seed (read-only reference, never copy files): {SEED}" in launch.goal


def test_e2e_real_project_validate_true_does_not_raise():
    # compose(validate=True) must also pass bash -n for a real project.
    _compose("project-setup", validate=True)
    _compose("cycle-implementation", cycle=5, validate=True)


def test_e2e_real_project_launch_script_is_valid_bash(tmp_path):
    import subprocess

    launch = _compose("project-setup")
    target = tmp_path / "launch-fourseer.sh"
    target.write_text(launch.launch_script, encoding="utf-8")
    result = subprocess.run(
        ["bash", "-n", str(target)], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
