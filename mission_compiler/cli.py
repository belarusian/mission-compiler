"""Command-line interface for mission-compiler.

Usage:
    mission-compiler compose <mission> [--cycles N] [--repo owner/name]
        [--seed path] [--spoke project-setup|cycle-implementation]

The CLI is a thin wrapper over :func:`mission_compiler.compose.compose`.
It is deterministic: the same arguments always produce the same output.
"""

from __future__ import annotations

import argparse
import json
import sys

from .compose import SPOKES, compose, validate_composed
from .launch import validate_launch_script


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the mission-compiler CLI."""
    parser = argparse.ArgumentParser(
        prog="mission-compiler",
        description=(
            "Compose the complete pipeline launch invocation from a free-text "
            "mission: GOAL (v3 deltas inline), inner spoke command, proven "
            "bounds, seed scaffold, and a ready-to-run nohup launch script."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    comp = sub.add_parser(
        "compose",
        help="Compose the launch invocation for a mission.",
    )
    comp.add_argument("mission", help="Free-text mission description.")
    comp.add_argument(
        "--cycles", type=int, default=12, help="Planned cycle count (default: 12)."
    )
    comp.add_argument(
        "--repo", default=None, help="GitHub repo owner/name (optional)."
    )
    comp.add_argument(
        "--seed", default=None, help="Read-only reference project path (optional)."
    )
    comp.add_argument(
        "--seed-spec",
        default=None,
        help=(
            "Explicit seed spec: a JSON mapping {source: dest} or a "
            "comma-separated path list. When given, the scaffold plan is built "
            "from the general classifier instead of the fixed builder."
        ),
    )
    comp.add_argument(
        "--spoke",
        choices=SPOKES,
        default="project-setup",
        help="Spoke type (default: project-setup).",
    )
    comp.add_argument(
        "--name",
        default="mission-compiler",
        help="Project / package name (default: mission-compiler).",
    )
    comp.add_argument(
        "--project-dir",
        default="/home/sasha/AI/mission-compiler/proj",
        help="Project repository directory.",
    )
    comp.add_argument(
        "--ai-dir",
        default="/home/sasha/AI/mission-compiler/ai",
        help="Directory for AI artifacts (log, runner prompt, briefing).",
    )
    comp.add_argument(
        "--cycle",
        type=int,
        default=1,
        help="Cycle number (used by the cycle-implementation spoke).",
    )
    comp.add_argument(
        "--run-py",
        default="/home/sasha/Research/four/run.py",
        help="Path to the outer orchestrator (run.py).",
    )
    comp.add_argument(
        "--script-path",
        default=None,
        help="Where to write the launch script (default: <project-dir>/launch-<name>.sh).",
    )
    comp.add_argument(
        "--write",
        action="store_true",
        help="Write the launch script to --script-path (default: print only).",
    )
    comp.add_argument(
        "--validate",
        action="store_true",
        help=(
            "Validate the composed launch script with `bash -n` before printing "
            "or writing; fail fast (non-zero exit) if it is not valid bash. "
            "Default off -> byte-identical behavior."
        ),
    )
    return parser


def parse_seed_spec(value: str) -> dict[str, str] | list[str]:
    """Parse a ``--seed-spec`` value into a seed spec.

    A value starting with ``{`` is parsed as JSON and must be a mapping of
    string to string (returns ``dict[str, str]``). Any other value is treated as
    a comma-separated path list: split on commas, strip surrounding whitespace,
    drop empty tokens (returns ``list[str]``).

    Raises:
        ValueError: if the JSON value is not an object, or any key/value is not a
            string.
    """
    stripped = value.strip()
    if stripped.startswith("{") or stripped.startswith("["):
        data = json.loads(stripped)
        if not isinstance(data, dict):
            raise ValueError("seed-spec JSON must be an object {source: dest}")
        out: dict[str, str] = {}
        for k, v in data.items():
            if not isinstance(k, str) or not isinstance(v, str):
                raise ValueError("seed-spec JSON keys and values must be strings")
            out[k] = v
        return out
    parts = [p.strip() for p in value.split(",")]
    return [p for p in parts if p]


def main(argv: list[str] | None = None) -> int:
    """Entry point for the mission-compiler CLI. Returns a process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command != "compose":
        parser.error(f"unknown command {args.command!r}")

    try:
        launch = compose(
            args.mission,
            cycles=args.cycles,
            repo=args.repo,
            seed=args.seed,
            spoke=args.spoke,
            name=args.name,
            project_dir=args.project_dir,
            ai_dir=args.ai_dir,
            cycle=args.cycle,
            run_py=args.run_py,
            seed_spec=parse_seed_spec(args.seed_spec) if args.seed_spec is not None else None,
        )
    except ValueError as exc:
        # Fail fast on a bad --seed-spec (e.g. non-object JSON).
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.validate:
        try:
            validate_composed(launch)
        except ValueError as exc:
            print(f"error: launch script failed validation: {exc}", file=sys.stderr)
            return 2

    print(launch.render())

    if args.write:
        # Fail fast: never write a launch script that is not valid bash.
        validate_launch_script(launch.launch_script)
        script_path = args.script_path or f"{args.project_dir}/launch-{args.name}.sh"
        try:
            with open(script_path, "w", encoding="utf-8") as fh:
                fh.write(launch.launch_script)
        except OSError as exc:
            print(f"error: could not write launch script to {script_path}: {exc}", file=sys.stderr)
            return 2
        print(f"\n[written] launch script -> {script_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
