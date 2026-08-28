"""Tests pinning the README.md CLI flag table to the real parser defaults.

Cycle 10, TICKET-024 (issue #32): the README flag table previously listed wrong
defaults for --project-dir / --ai-dir / --cycle / --run-py. These tests parse the
README and assert each of those Default cells matches the actual default produced
by ``mission_compiler.cli.build_parser``, so this class of doc drift cannot
silently return. Additive only; no source change.
"""

from __future__ import annotations

from pathlib import Path

from mission_compiler.cli import build_parser

#: Repo root is one level up from tests/.
README = Path(__file__).resolve().parent.parent / "README.md"


def _readme_flag_default(flag: str) -> str:
    """Return the Default cell (third column) of a flag row in the README table.

    A flag row looks like ``| --flag ... | description | default |``. We match on
    the first cell starting with the flag token and return the last pipe-delimited
    cell, stripped.
    """
    text = README.read_text(encoding="utf-8")
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not cells:
            continue
        first = cells[0]
        # Match the flag token as a whole leading token (e.g. "--project-dir DIR").
        tokens = first.split()
        if tokens and tokens[0] == flag:
            return cells[-1]
    raise AssertionError(f"flag {flag!r} not found in README.md flag table")


def test_readme_project_dir_default_matches_parser():
    args = build_parser().parse_args(["compose", "Build it."])
    assert _readme_flag_default("--project-dir") == str(args.project_dir)
    assert _readme_flag_default("--project-dir") == "/home/sasha/AI/mission-compiler/proj"


def test_readme_ai_dir_default_matches_parser():
    args = build_parser().parse_args(["compose", "Build it."])
    assert _readme_flag_default("--ai-dir") == str(args.ai_dir)
    assert _readme_flag_default("--ai-dir") == "/home/sasha/AI/mission-compiler/ai"


def test_readme_cycle_default_matches_parser():
    args = build_parser().parse_args(["compose", "Build it."])
    assert _readme_flag_default("--cycle") == str(args.cycle)
    assert _readme_flag_default("--cycle") == "1"


def test_readme_run_py_default_matches_parser():
    args = build_parser().parse_args(["compose", "Build it."])
    assert _readme_flag_default("--run-py") == str(args.run_py)
    # Cycle 14 (issue #46): the v3 path is the default outer orchestrator.
    assert _readme_flag_default("--run-py") == "/home/sasha/Research/four/run-v3.py"


def test_readme_correct_defaults_present_verbatim():
    text = README.read_text(encoding="utf-8")
    for value in (
        "/home/sasha/AI/mission-compiler/proj",
        "/home/sasha/AI/mission-compiler/ai",
        "/home/sasha/Research/four/run-v3.py",
    ):
        assert value in text, f"README missing correct default {value!r}"


def test_readme_private_default_matches_parser():
    """TICKET-033: README documents --private; default cell matches parser (off)."""
    args = build_parser().parse_args(["compose", "Build it."])
    assert args.private is False
    # The README row's Default cell must reflect the store_true off-state.
    assert _readme_flag_default("--private") == "off (public)"


def test_readme_mentions_v3_launcher():
    """TICKET-037: README prose narrates the v3 default launcher."""
    text = README.read_text(encoding='utf-8')
    assert 'run-v3.py' in text, 'README missing run-v3.py in prose'
    assert 'FIVE_REQUEST_TIMEOUT' in text, 'README missing FIVE_REQUEST_TIMEOUT in prose'


def test_readme_mentions_dual_pins():
    """TICKET-037: README prose mentions the dual-LLM endpoint pins."""
    text = README.read_text(encoding='utf-8')
    assert '192.168.1.157:8080' in text, 'README missing .157:8080 dual pin'
    assert '192.168.1.161:8081' in text, 'README missing .161:8081 dual pin'


def test_readme_mentions_single_llm_pin():
    """TICKET-037: README prose mentions the single-LLM endpoint pin."""
    text = README.read_text(encoding='utf-8')
    assert '192.168.1.161:8080' in text, 'README missing .161:8080 single-LLM pin'


def test_readme_mentions_proven_bounds():
    """TICKET-037: README prose mentions the proven default bounds."""
    text = README.read_text(encoding='utf-8')
    assert '7200' in text, 'README missing setup outer wall 7200'
    assert '3600' in text, 'README missing cycle outer wall 3600'
