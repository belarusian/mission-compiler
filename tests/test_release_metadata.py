"""Release-metadata invariants for mission-compiler v0.1.0 (TICKET-023).

Pins, with stdlib only:
  * the module entry point ``python3 -m mission_compiler`` works;
  * ``mission_compiler.__version__`` and ``pyproject.toml [project] version``
    agree (both "0.1.0");
  * ``[project] dependencies == []`` (the stdlib-only invariant);
  * a prepared v0.1.0 tag description (non-empty, mentions "v0.1.0").

The v0.1.0 tag is PREPARED here (as a constant) but NOT cut: the Build Order row
says "do NOT cut the tag unless the row explicitly requires it", and this row does
not. Additive only: no change to any public API or signature in mission_compiler/.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = REPO_ROOT / "pyproject.toml"

# Prepared v0.1.0 release-note string (tag description). Not cut this cycle.
V0_1_0_TAG_DESCRIPTION = (
    "v0.1.0 - mission-compiler first release.\n"
    "\n"
    "A deterministic, stdlib-only CLI that composes four pipeline launches from a\n"
    "free-text mission: GOAL (v3 deltas inline), inner spoke command, proven bounds,\n"
    "seed scaffold plan, and a nohup-ready bash launch script validated with `bash -n`.\n"
    "\n"
    "Ships the five-section composer, all CLI flags (--seed-spec, --validate, --write),\n"
    "the proven-bounds table (by spoke and by LLM config), the general seed-path\n"
    "classifier, runnable byte-deterministic examples/, and a green gate\n"
    "(pytest + ruff + mypy).\n"
)


def _pyproject_field(name: str) -> str | None:
    """Lightweight stdlib read of a top-level ``[project]`` scalar field.

    Returns the raw value string (without surrounding quotes) or None if absent.
    Avoids a tomllib dependency (not present on Python 3.10).
    """
    text = PYPROJECT.read_text(encoding="utf-8")
    m = re.search(rf"^{name}\s*=\s*(.+)$", text, flags=re.MULTILINE)
    if not m:
        return None
    return m.group(1).strip()


def test_module_entry_point_runs():
    """``python3 -m mission_compiler compose ...`` exits 0 (entry point works)."""
    result = subprocess.run(
        [sys.executable, "-m", "mission_compiler", "compose", "Build it."],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, result.stderr


def test_version_consistent_between_init_and_pyproject():
    """__init__.__version__ and pyproject [project] version both say 0.1.0."""
    import mission_compiler

    init_version = mission_compiler.__version__
    pyproject_version = _pyproject_field("version")
    assert init_version == "0.1.0"
    # Strip surrounding quotes from the toml value, e.g. '0.1.0' -> 0.1.0
    assert pyproject_version is not None
    assert pyproject_version.strip("'\"") == "0.1.0"
    assert init_version == pyproject_version.strip("'\"")


def test_no_dependencies_stdlib_only():
    """[project] dependencies is empty (stdlib-only invariant)."""
    deps = _pyproject_field("dependencies")
    assert deps is not None
    assert deps.strip() == "[]"


def test_v0_1_0_tag_description_prepared_not_cut():
    """The prepared tag description is non-empty and mentions v0.1.0."""
    assert V0_1_0_TAG_DESCRIPTION.strip()
    assert "v0.1.0" in V0_1_0_TAG_DESCRIPTION


def test_no_git_tag_created_this_cycle():
    """No git tag exists (the row does not require cutting v0.1.0)."""
    result = subprocess.run(
        ["git", "tag", "--list"], capture_output=True, text=True, cwd=str(REPO_ROOT)
    )
    assert result.returncode == 0
    tags = [t for t in result.stdout.splitlines() if t.strip()]
    assert tags == [], f"unexpected git tags present: {tags}"
