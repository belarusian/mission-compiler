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


# ---------------------------------------------------------------------------
# Cycle 6, TICKET-014 (issue #18): CLI --seed-spec passthrough.
# ---------------------------------------------------------------------------


def test_parser_seed_spec_defaults_none():
    args = build_parser().parse_args(["compose", "Build it."])
    assert args.seed_spec is None


def test_parse_seed_spec_json_mapping():
    from mission_compiler.cli import parse_seed_spec

    spec = parse_seed_spec('{"a.py": "b.py", "c.md": "c.md"}')
    assert isinstance(spec, dict)
    assert spec == {"a.py": "b.py", "c.md": "c.md"}


def test_parse_seed_spec_comma_list():
    from mission_compiler.cli import parse_seed_spec

    spec = parse_seed_spec("x.py, y.md , z.toml")
    assert isinstance(spec, list)
    assert spec == ["x.py", "y.md", "z.toml"]


def test_parse_seed_spec_drops_empty_tokens():
    from mission_compiler.cli import parse_seed_spec

    assert parse_seed_spec("a.py,, b.md ,") == ["a.py", "b.md"]


def test_parse_seed_spec_json_non_object_raises():
    import pytest

    from mission_compiler.cli import parse_seed_spec

    with pytest.raises(ValueError, match="object"):
        parse_seed_spec('["a", "b"]')


def test_cli_seed_spec_mapping_reflects_classified_entries(capsys):
    rc = main(
        [
            "compose", "Build it.",
            "--seed-spec", '{"a.py": "/d/a.py", "ref.md": "ref.md"}',
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    section = out.split("[4] SEED SCAFFOLD")[1].split("[5] NOHUP LAUNCH SCRIPT")[0]
    # SeedScaffold.render format: "[action] path - note"; relative source/dest
    # are resolved against the default project dir.
    assert "[copy] /d/a.py" in section
    assert "copy from" in section
    assert "[reference] /home/sasha/AI/mission-compiler/proj/ref.md" in section


def test_cli_seed_spec_list_reflects_create_entries(capsys):
    rc = main(
        [
            "compose", "Build it.",
            "--seed-spec", "pkg/mod.py, docs/README.md",
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    section = out.split("[4] SEED SCAFFOLD")[1].split("[5] NOHUP LAUNCH SCRIPT")[0]
    assert "[create]" in section
    assert "python module" in section
    assert "markdown doc" in section


def test_cli_seed_spec_deterministic(capsys):
    args = ["compose", "Build it.", "--seed-spec", '{"a.py": "/d/a.py"}']
    main(args)
    first = capsys.readouterr().out
    main(args)
    second = capsys.readouterr().out
    assert first == second


def test_cli_no_seed_spec_unchanged(capsys):
    # Without the flag, output must be byte-identical to a plain compose.
    from mission_compiler.compose import compose

    main(["compose", "Build it.", "--spoke", "project-setup"])
    out = capsys.readouterr().out
    expected = compose("Build it.", spoke="project-setup").render()
    assert expected in out
