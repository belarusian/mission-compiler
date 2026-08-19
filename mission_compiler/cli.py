"""Command-line interface for mission-compiler.

Usage:
    mission-compiler compose <mission> [--cycles N] [--repo owner/name]
        [--seed path] [--spoke project-setup|cycle-implementation]

The CLI is a thin wrapper over :func:`mission_compiler.compose.compose`.
It is deterministic: the same arguments always produce the same output.
"""

from __future__ import annotations

import argparse
import sys

from .compose import SPOKES, compose
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
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point for the mission-compiler CLI. Returns a process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command != "compose":
        parser.error(f"unknown command {args.command!r}")

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
    )

    print(launch.render())

    if args.write:
        # Fail fast: never write a launch script that is not valid bash.
        validate_launch_script(launch.launch_script)
        script_path = args.script_path or f"{args.project_dir}/launch-{args.name}.sh"
        with open(script_path, "w", encoding="utf-8") as fh:
            fh.write(launch.launch_script)
        print(f"\n[written] launch script -> {script_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
