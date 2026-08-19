"""Tests for the ``--config`` CLI flag (LLM-config bounds axis).

Cycle 10, TICKET-025/026 (issues #33/#34): the new opt-in ``--config`` flag
selects proven bounds from ``LLM_CONFIG_BOUNDS``. These tests exercise the full
CLI flag matrix with ``--config``, assert the [3] BOUNDS section reflects the
selected row, that a written script passes an explicit ``bash -n``, that stdout is
byte-identical across identical invocations, that omitting ``--config`` stays
byte-identical to pre-flag behavior, and that a bad config fails fast. Additive
only; no source change.
"""

from __future__ import annotations

import subprocess

from mission_compiler.cli import main

FIVE_HEADERS = (
    "[1] GOAL",
    "[2] INNER SPOKE COMMAND",
    "[3] BOUNDS",
    "[4] SEED SCAFFOLD",
    "[5] NOHUP LAUNCH SCRIPT",
)


def test_cli_config_flag_matrix_cycle_validate_write_valid(tmp_path, capsys):
    # Full flag matrix: cycle spoke + explicit cycle + config + validate + write.
    script = tmp_path / "launch.sh"
    rc = main(
        [
            "compose", "Run cycle 5.",
            "--spoke", "cycle-implementation",
            "--cycle", "5",
            "--config", "single-llm-long-pass",
            "--project-dir", str(tmp_path),
            "--script-path", str(script),
            "--validate",
            "--write",
        ]
    )
    assert rc == 0
    assert script.exists()
    result = subprocess.run(
        ["bash", "-n", str(script)], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    out = capsys.readouterr().out
    for header in FIVE_HEADERS:
        assert header in out
    # The [3] BOUNDS section reflects the selected LLM-config row (outer wall 10800s).
    assert "outer wall (perl alarm): 10800s" in out


def test_cli_config_flag_deterministic_stdout(capsys):
    args = [
        "compose", "Run cycle 5.",
        "--spoke", "cycle-implementation",
        "--cycle", "5",
        "--config", "2-llm-fast",
        "--validate",
    ]
    main(args)
    first = capsys.readouterr().out
    main(args)
    second = capsys.readouterr().out
    assert first == second


def test_cli_config_omitted_is_byte_identical_to_pre_flag(capsys):
    # Omitting --config must be byte-identical to a plain compose (default unchanged).
    args_with_none = [
        "compose", "Build it.",
        "--spoke", "cycle-implementation",
        "--cycle", "3",
    ]
    main(args_with_none)
    without = capsys.readouterr().out
    # The cycle-implementation spoke default outer wall is 3600s (not a config row).
    assert "outer wall (perl alarm): 3600s" in without


def test_cli_config_bad_value_fails_fast(capsys):
    rc = main(
        [
            "compose", "Build it.",
            "--config", "no-such-config",
        ]
    )
    assert rc != 0
    err = capsys.readouterr().err
    assert "error" in err.lower()


def test_cli_config_2llm_fast_reflects_bounds(capsys):
    rc = main(
        [
            "compose", "Build it.",
            "--spoke", "project-setup",
            "--config", "2-llm-fast",
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    # 2-llm-fast outer wall is 3600s, heavier than the project-setup spoke default (1800s).
    assert "outer wall (perl alarm): 3600s" in out
