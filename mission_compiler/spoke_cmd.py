"""Build the inner spoke command line for a mission-compiler launch.

Two spoke types are supported:

  * ``project-setup`` - the setup spoke that scaffolds a new project.
  * ``cycle-implementation`` - the per-cycle build spoke (v3).

Each returns the exact command line (list of argv tokens) with all args:
spoke path, --goal, --name, --project-dir, --ai-dir, --cycles, --repo, --seed
(setup) or --runner-prompt/--log/--briefing/--project-dir/--cycle/--max-steps
(cycle). The command is a pure function of its inputs.
"""

from __future__ import annotations

from dataclasses import dataclass

from .bounds import Bounds

#: Default spoke paths (overridable for tests / alternate installs).
DEFAULT_SETUP_SPOKE = "/home/sasha/Research/four/examples/spokes/project-setup.py"
DEFAULT_CYCLE_SPOKE = "/home/sasha/Research/four/examples/spokes/cycle-implementation-v3.py"


@dataclass(frozen=True)
class SpokeCommand:
    """A fully-specified inner spoke invocation."""

    argv: list[str]

    def render(self) -> str:
        """Render as a single shell line (tokens joined by spaces)."""
        return " ".join(_quote(t) for t in self.argv)


def _quote(token: str) -> str:
    """Quote a shell token only when it contains whitespace."""
    if token and any(c.isspace() for c in token):
        return '"' + token.replace('"', '\\"') + '"'
    return token


def build_setup_command(
    *,
    goal: str,
    name: str,
    project_dir: str,
    ai_dir: str,
    cycles: int,
    repo: str | None,
    seed: str | None,
    spoke_path: str = DEFAULT_SETUP_SPOKE,
) -> SpokeCommand:
    """Build the ``project-setup`` spoke command line (all args)."""
    argv: list[str] = ["python3", spoke_path]
    argv += ["--goal", goal]
    argv += ["--name", name]
    argv += ["--project-dir", project_dir]
    argv += ["--ai-dir", ai_dir]
    argv += ["--cycles", str(cycles)]
    if repo:
        argv += ["--repo", repo]
    if seed:
        argv += ["--seed", seed]
    return SpokeCommand(argv)


def build_cycle_command(
    *,
    runner_prompt: str,
    log: str,
    project_dir: str,
    cycle: int,
    max_steps: int,
    briefing: str | None = None,
    trajectories: str | None = None,
    spoke_path: str = DEFAULT_CYCLE_SPOKE,
) -> SpokeCommand:
    """Build the ``cycle-implementation`` (v3) spoke command line (all args)."""
    argv: list[str] = ["python3", spoke_path]
    argv += ["--runner-prompt", runner_prompt]
    argv += ["--log", log]
    if briefing:
        argv += ["--briefing", briefing]
    argv += ["--project-dir", project_dir]
    argv += ["--cycle", str(cycle)]
    if trajectories:
        argv += ["--trajectories", trajectories]
    argv += ["--max-steps", str(max_steps)]
    return SpokeCommand(argv)


def bounds_for_spoke(spoke: str) -> Bounds:
    """Re-export for convenience (delegates to the bounds table)."""
    from .bounds import bounds_for

    return bounds_for(spoke)
