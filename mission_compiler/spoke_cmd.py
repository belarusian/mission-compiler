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

#: Inner-spoke lineage by LLM-config kind (Cycle 14, issue #46 / TICKET-036).
#: The v3 path (run-v3.py + explicit LLM request timeout) pairs each launcher
#: kind with its proven inner spoke: the dual/2-LLM explicit-timeout line is
#: ``cycle-implementation-v4.py``; the single-LLM line is
#: ``cycle-implementation-v3.py``. ``DEFAULT_CYCLE_SPOKE`` (v3) remains the
#: byte-identical default for callers that do not pass ``config_kind``.
DEFAULT_CYCLE_SPOKE_V4 = "/home/sasha/Research/four/examples/spokes/cycle-implementation-v4.py"

#: The two supported LLM-config kinds for the cycle-implementation spoke.
CONFIG_KINDS = ("dual-llm", "single-llm")

#: Inner spoke path per config kind.
_CYCLE_SPOKE_BY_KIND: dict[str, str] = {
    "dual-llm": DEFAULT_CYCLE_SPOKE_V4,
    "single-llm": DEFAULT_CYCLE_SPOKE,
}


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
    private: bool = False,
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
        if private:
            # Additive: emit --private immediately after the --repo addition,
            # before --seed. When private is False (the default) argv is
            # byte-identical to before this param existed.
            argv += ["--private"]
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
    config_kind: str = "single-llm",
) -> SpokeCommand:
    """Build the ``cycle-implementation`` spoke command line (all args).

    Args:
        config_kind: additive (Cycle 14, issue #46) - selects the inner-spoke
            lineage for the composed launcher kind: ``"dual-llm"`` (the default
            launcher kind) renders ``cycle-implementation-v4.py``;
            ``"single-llm"`` renders ``cycle-implementation-v3.py`` (the
            byte-identical default, so existing callers are unchanged). An
            explicit ``spoke_path`` always wins over ``config_kind``.
            Unknown kinds raise ``ValueError``.
    """
    if spoke_path == DEFAULT_CYCLE_SPOKE and config_kind != "single-llm":
        try:
            spoke_path = _CYCLE_SPOKE_BY_KIND[config_kind]
        except KeyError:
            known = ", ".join(sorted(_CYCLE_SPOKE_BY_KIND))
            raise ValueError(
                f"unknown config kind {config_kind!r}; known kinds: {known}"
            ) from None
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
