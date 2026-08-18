"""Tests for the mission-compiler CLI."""

from __future__ import annotations

import pytest

from mission_compiler.cli import build_parser, main


def test_parser_defaults():
    args = build_parser().parse_args(["compose", "Build it."])
    assert args.command == "compose"
    assert args.mission == "Build it."
    assert args.cycles == 12
    assert args.spoke == "project-setup"
    assert args.repo is None
    assert args.seed is None


def test_parser_reads_options():
    args = build_parser().parse_args(
        [
            "compose", "Build it.",
            "--cycles", "7",
            "--repo", "o/r",
            "--seed", "/s",
            "--spoke", "cycle-implementation",
        ]
    )
    assert args.cycles == 7
    assert args.repo == "o/r"
    assert args.seed == "/s"
    assert args.spoke == "cycle-implementation"


def test_cli_prints_all_sections(capsys):
    rc = main(["compose", "Build it.", "--spoke", "project-setup"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "[1] GOAL" in out
    assert "[5] NOHUP LAUNCH SCRIPT" in out


def test_cli_write_creates_script(tmp_path, capsys):
    script = tmp_path / "launch.sh"
    rc = main(
        [
            "compose", "Build it.",
            "--project-dir", str(tmp_path),
            "--script-path", str(script),
            "--write",
        ]
    )
    assert rc == 0
    assert script.exists()
    content = script.read_text()
    assert content.startswith("#!/bin/bash")
    assert "perl -e 'alarm shift; exec @ARGV'" in content
    capsys.readouterr()


def test_cli_deterministic_output(capsys):
    main(["compose", "Build it.", "--spoke", "project-setup"])
    first = capsys.readouterr().out
    main(["compose", "Build it.", "--spoke", "project-setup"])
    second = capsys.readouterr().out
    assert first == second
