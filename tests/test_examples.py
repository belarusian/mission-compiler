"""Tests that execute the shipped examples/ scripts end-to-end (TICKET-032).

The README and release notes advertise ``examples/`` as "runnable
byte-deterministic examples", but no test previously ran them. This module closes
that doc/code-consistency gap: it executes each example script as a real
subprocess and asserts exit 0, that the written launch script passes an explicit
``bash -n``, that all five section headers print, and that two identical runs are
byte-identical on stdout.

The examples use fixed ``/tmp/mission-compiler-example/...`` paths (no mktemp), so
their output is deterministic across runs. Additive only: no change to any public
API or signature in ``mission_compiler/``.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = REPO_ROOT / "examples"

FIVE_HEADERS = (
    "[1] GOAL",
    "[2] INNER SPOKE COMMAND",
    "[3] BOUNDS",
    "[4] SEED SCAFFOLD",
    "[5] NOHUP LAUNCH SCRIPT",
)


def _run_example(name: str) -> subprocess.CompletedProcess[str]:
    """Run ``examples/<name>`` as a real bash subprocess."""
    return subprocess.run(
        ["bash", str(EXAMPLES / name)], capture_output=True, text=True
    )


def _written_script_path(name: str) -> Path:
    """The fixed throwaway launch-script path each example writes to."""
    if name == "compose-fleet.sh":
        return Path("/tmp/mission-compiler-example/fleet/proj/launch-fleet.sh")
    if name == "compose-config.sh":
        return Path("/tmp/mission-compiler-example/fourseer-config/proj/launch-fourseer.sh")
    return Path("/tmp/mission-compiler-example/fourseer/proj/launch-fourseer.sh")


def _assert_example_green(name: str) -> None:
    result = _run_example(name)
    assert result.returncode == 0, f"{name} failed:\n{result.stderr}"
    for header in FIVE_HEADERS:
        assert header in result.stdout
    script = _written_script_path(name)
    assert script.exists(), f"{name} did not write {script}"
    bash_n = subprocess.run(["bash", "-n", str(script)], capture_output=True, text=True)
    assert bash_n.returncode == 0, f"{name} written script failed bash -n: {bash_n.stderr}"


def test_example_fleet_runs_and_bash_n():
    _assert_example_green("compose-fleet.sh")


def test_example_fourseer_runs_and_bash_n():
    _assert_example_green("compose-fourseer.sh")


def test_example_config_runs_and_reflects_bounds():
    result = _run_example("compose-config.sh")
    assert result.returncode == 0, f"compose-config.sh failed:\n{result.stderr}"
    for header in FIVE_HEADERS:
        assert header in result.stdout
    # The --config single-llm-long-pass row is reflected in the [3] BOUNDS section.
    assert "outer wall (perl alarm): 10800s" in result.stdout
    script = _written_script_path("compose-config.sh")
    assert script.exists()
    bash_n = subprocess.run(["bash", "-n", str(script)], capture_output=True, text=True)
    assert bash_n.returncode == 0, (
        f"compose-config.sh written script failed bash -n: {bash_n.stderr}"
    )


def test_examples_byte_identical_across_runs():
    for name in ("compose-fleet.sh", "compose-fourseer.sh", "compose-config.sh"):
        first = _run_example(name)
        second = _run_example(name)
        assert first.returncode == 0 and second.returncode == 0
        assert first.stdout.encode("utf-8") == second.stdout.encode("utf-8"), (
            f"{name} is not byte-deterministic across runs"
        )
