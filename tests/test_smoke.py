"""Smoke tests for mission-compiler.

Covers:
  * the package imports cleanly (original smoke test);
  * the CLI runs end-to-end via ``python3 -m mission_compiler`` (subprocess),
    asserting exit 0 + all five composed sections;
  * subprocess determinism (byte-identical output across equal invocations);
  * the ``--validate`` flag path through the real entry point;
  * fail-fast on a bad ``--seed-spec``;
  * the ``parse_seed_spec`` comma-list form round-tripping into the scaffold.

Additive only: no change to any public API or signature in mission_compiler/.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# The five composed section headers, in order (see ComposedLaunch.render).
SECTION_HEADERS = [
    "[1] GOAL (v3 deltas inline)",
    "[2] INNER SPOKE COMMAND",
    "[3] BOUNDS (proven table)",
    "[4] SEED SCAFFOLD",
    "[5] NOHUP LAUNCH SCRIPT",
]


def test_import_mission_compiler():
    import mission_compiler

    assert mission_compiler.__version__ == "0.1.0"


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    """Run the CLI as a real subprocess via ``python3 -m mission_compiler``."""
    return subprocess.run(
        [sys.executable, "-m", "mission_compiler", *args],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).resolve().parent.parent),
    )


def test_subprocess_compose_exit_zero_and_five_sections():
    """End-to-end: the module entry point composes and prints all five sections."""
    result = _run_cli("compose", "Build it.", "--spoke", "project-setup")
    assert result.returncode == 0, result.stderr
    for header in SECTION_HEADERS:
        assert header in result.stdout


def test_subprocess_compose_is_deterministic():
    """Two equal invocations produce byte-identical stdout (encoded bytes)."""
    args = ["compose", "Build it.", "--spoke", "project-setup", "--name", "det"]
    r1 = _run_cli(*args)
    r2 = _run_cli(*args)
    assert r1.returncode == 0 and r2.returncode == 0
    assert r1.stdout.encode("utf-8") == r2.stdout.encode("utf-8")


def test_subprocess_compose_validate_flag():
    """--validate runs bash -n on the composed script; valid -> exit 0 + sections."""
    result = _run_cli(
        "compose", "Build it.", "--spoke", "project-setup", "--validate"
    )
    assert result.returncode == 0, result.stderr
    for header in SECTION_HEADERS:
        assert header in result.stdout


def test_subprocess_bad_seed_spec_fails_fast():
    """A non-object JSON --seed-spec fails fast (non-zero exit, 'object' on stderr)."""
    result = _run_cli(
        "compose", "Build it.", "--spoke", "project-setup",
        "--seed-spec", "[1, 2]",
    )
    assert result.returncode != 0
    assert "object" in result.stderr


def test_parse_seed_spec_comma_list_round_trips_into_scaffold():
    """The comma-list seed-spec form classifies into [create] scaffold lines."""
    from mission_compiler.cli import parse_seed_spec
    from mission_compiler.compose import compose

    spec = parse_seed_spec("run.py, README.md")
    assert isinstance(spec, list)
    assert spec == ["run.py", "README.md"]

    launch = compose(
        "Build it.",
        spoke="project-setup",
        name="listspec",
        project_dir="/tmp/mc-listspec/proj",
        ai_dir="/tmp/mc-listspec/ai",
        seed_spec=spec,
    )
    rendered = launch.render()
    # The general classifier turns a list into [create] entries.
    assert "[create] /tmp/mc-listspec/proj/run.py" in rendered
    assert "[create] /tmp/mc-listspec/proj/README.md" in rendered
