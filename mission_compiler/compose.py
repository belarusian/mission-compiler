"""Top-level ``compose`` for mission-compiler.

``compose`` takes a free-text mission plus optional parameters and produces
the complete launch invocation - the five sections:

  1. GOAL text with the v3 delta descriptions inline.
  2. Inner spoke command line with all args.
  3. Bounds (outer wall, inner-seconds, outer-steps, inner max-steps) from
     the proven-bounds table.
  4. Seed directory scaffold (what to copy or create for the seed path).
  5. The full nohup launch script ready to execute.

The whole thing is a pure function of its inputs: no timestamps, no
randomness, no I/O. Identical inputs always produce identical output.
"""

from __future__ import annotations

from dataclasses import dataclass

from .bounds import Bounds, bounds_for, bounds_for_config
from .goal import compose_goal
from .launch import (
    build_launch_script,
    build_nohup_command,
    validate_launch_script,
)
from .seed_scaffold import (
    ScaffoldItem,
    SeedScaffold,
    build_seed_scaffold,
    classify_seed_paths,
)
from .spoke_cmd import SpokeCommand, build_cycle_command, build_setup_command

#: The two supported spoke types.
SPOKES = ("project-setup", "cycle-implementation")

#: Default paths (overridable for tests / alternate installs).
DEFAULT_PROJECT_DIR = "/home/sasha/AI/mission-compiler/proj"
DEFAULT_AI_DIR = "/home/sasha/AI/mission-compiler/ai"
DEFAULT_NAME = "mission-compiler"
DEFAULT_RUN_PY = "/home/sasha/Research/four/run.py"


@dataclass(frozen=True)
class ComposedLaunch:
    """The complete, deterministic launch invocation for a mission."""

    goal: str
    inner: SpokeCommand
    bounds: Bounds
    seed_scaffold: SeedScaffold
    launch_script: str
    nohup_command: str
    spoke: str

    def render(self) -> str:
        """Render all five sections as a single readable document."""
        parts: list[str] = []
        parts.append("=" * 72)
        parts.append("MISSION-COMPILER COMPOSED LAUNCH")
        parts.append("=" * 72)
        parts.append("")
        parts.append("[1] GOAL (v3 deltas inline)")
        parts.append("-" * 72)
        parts.append(self.goal)
        parts.append("")
        parts.append("[2] INNER SPOKE COMMAND")
        parts.append("-" * 72)
        parts.append(self.inner.render())
        parts.append("")
        parts.append("[3] BOUNDS (proven table)")
        parts.append("-" * 72)
        b = self.bounds
        parts.append(f"  outer wall (perl alarm): {b.outer_wall}s")
        parts.append(f"  inner-seconds:           {b.inner_seconds}s")
        parts.append(f"  outer-steps:             {b.outer_steps}")
        parts.append(f"  inner max-steps:         {b.inner_max_steps}")
        parts.append("")
        parts.append("[4] SEED SCAFFOLD")
        parts.append("-" * 72)
        parts.append(self.seed_scaffold.render())
        parts.append("")
        parts.append("[5] NOHUP LAUNCH SCRIPT")
        parts.append("-" * 72)
        parts.append(self.launch_script)
        parts.append("")
        parts.append("Launch with:")
        parts.append(f"  {self.nohup_command}")
        return "\n".join(parts)


def _build_scaffold(
    *,
    seed: str | None,
    project_dir: str,
    name: str,
    ai_dir: str,
    seed_spec: dict[str, str] | list[str] | None,
) -> SeedScaffold:
    """Build the scaffold plan for a launch.

    When ``seed_spec`` is None this returns the fixed four-project scaffold from
    :func:`build_seed_scaffold` (byte-identical to before the opt-in existed).
    Otherwise it builds the plan from the general :func:`classify_seed_paths`
    planner: each entry becomes a :class:`ScaffoldItem` whose ``note`` carries the
    copy source (for ``copy``) or the create/reference note, and the rendered
    section reflects the classified reference/create/copy entries.

    Pure function of its inputs; deterministic.
    """
    if seed_spec is None:
        return build_seed_scaffold(
            seed=seed,
            project_dir=project_dir,
            name=name,
            ai_dir=ai_dir,
        )
    entries = classify_seed_paths(seed_spec, base_dir=project_dir)
    items: list[ScaffoldItem] = []
    for e in entries:
        if e.action == "copy":
            note = f"copy from {e.source}"
        elif e.action == "create":
            note = e.note
        else:  # reference
            note = e.note
        items.append(ScaffoldItem(action=e.action, path=e.path, note=note))
    return SeedScaffold(seed_path=seed, items=items)


def compose(
    mission: str,
    *,
    cycles: int = 12,
    repo: str | None = None,
    private: bool = False,
    seed: str | None = None,
    seed_spec: dict[str, str] | list[str] | None = None,
    spoke: str = "project-setup",
    name: str = DEFAULT_NAME,
    project_dir: str = DEFAULT_PROJECT_DIR,
    ai_dir: str = DEFAULT_AI_DIR,
    cycle: int = 1,
    run_py: str = DEFAULT_RUN_PY,
    config: str | None = None,
    validate: bool = False,
) -> ComposedLaunch:
    """Compose the complete launch invocation for ``mission``.

    Args:
        mission: free-text mission description.
        cycles: planned cycle count (setup) / used to name artifacts.
        repo: optional GitHub ``owner/name``.
        private: when True (with ``repo`` set) the setup command gains a
            ``--private`` flag and the GOAL repo line reads
            ``GitHub repo: {repo} (private)``; when False (the default) the
            output is byte-identical to before this param existed.
        seed: optional read-only reference project path.
        seed_spec: optional explicit seed spec (a mapping ``{source: dest}`` or a
            list of paths). When given, the scaffold plan is built from the general
            ``classify_seed_paths`` planner instead of the fixed builder; when None
            (the default) the behavior is byte-identical to before this param existed.
        spoke: ``project-setup`` or ``cycle-implementation``.
        name: project / package name.
        project_dir: project repository directory.
        ai_dir: directory for the AI artifacts (log, runner prompt, briefing).
        cycle: cycle number (only used for the cycle-implementation spoke).
        run_py: path to the outer orchestrator.
        config: optional LLM-config name (a key of ``LLM_CONFIG_BOUNDS``, e.g.
            ``2-llm-fast`` / ``single-llm-long-pass`` / ``setup``). When given, the
            proven bounds are selected via ``bounds_for_config(config)`` instead of
            by spoke type; when None (the default) the behavior is byte-identical to
            before this param existed. An unknown config raises ``ValueError``.
        validate: when True, run ``validate_launch_script`` on the composed
            launch script before returning so an invalid script fails fast
            (raises ``ValueError``). When False (the default) the behavior is
            byte-identical to before this flag existed - no validation call.

    Raises:
        ValueError: if ``spoke`` is not a supported spoke type.
    """
    if spoke not in SPOKES:
        raise ValueError(f"unknown spoke {spoke!r}; supported: {', '.join(SPOKES)}")

    if config is None:
        bounds = bounds_for(spoke)
    else:
        # Opt-in: select the proven-bounds row by LLM configuration instead of
        # by spoke type. Default (config=None) stays byte-identical to before.
        bounds = bounds_for_config(config)
    goal = compose_goal(
        mission,
        spoke=spoke,
        cycles=cycles,
        repo=repo,
        seed=seed,
        project_dir=project_dir,
        ai_dir=ai_dir,
        name=name,
        private=private,
    )

    log = f"{ai_dir}/cycle-001-{name}-gate.md"
    trajectories = f"{ai_dir}/trajectories"

    if spoke == "project-setup":
        inner = build_setup_command(
            goal=goal,
            name=name,
            project_dir=project_dir,
            ai_dir=ai_dir,
            cycles=cycles,
            repo=repo,
            seed=seed,
            private=private,
        )
    else:
        runner_prompt = f"{ai_dir}/{name}-cycle-runner-prompt.md"
        briefing = f"{ai_dir}/{name}-cycle-{cycle}-briefing.md"
        inner = build_cycle_command(
            runner_prompt=runner_prompt,
            log=log,
            project_dir=project_dir,
            cycle=cycle,
            max_steps=bounds.inner_max_steps,
            briefing=briefing,
            trajectories=trajectories,
        )

    seed_scaffold = _build_scaffold(
        seed=seed,
        project_dir=project_dir,
        name=name,
        ai_dir=ai_dir,
        seed_spec=seed_spec,
    )

    script_path = f"{project_dir}/launch-{name}.sh"
    launch_script = build_launch_script(
        goal=goal,
        inner=inner,
        bounds=bounds,
        log=log,
        trajectories=trajectories,
        project_dir=project_dir,
        name=name,
        run_py=run_py,
    )
    nohup_command = build_nohup_command(script_path)

    if validate:
        # Fail fast: an invalid launch script must not be returned (or written).
        validate_launch_script(launch_script)

    return ComposedLaunch(
        goal=goal,
        inner=inner,
        bounds=bounds,
        seed_scaffold=seed_scaffold,
        launch_script=launch_script,
        nohup_command=nohup_command,
        spoke=spoke,
    )

def validate_composed(launch: ComposedLaunch) -> None:
    """Validate the composed launch script is syntactically valid bash.

    Additive helper that runs ``validate_launch_script`` on
    ``launch.launch_script``. It exists so callers (and tests) can validate a
    fully-composed :class:`ComposedLaunch` without re-running the whole compose
    path. Raises ``ValueError`` (containing "bash -n") if the script is not
    valid bash; returns None when valid.

    Args:
        launch: a composed launch whose ``launch_script`` should be checked.

    Raises:
        ValueError: if the launch script fails ``bash -n``.
    """
    validate_launch_script(launch.launch_script)
