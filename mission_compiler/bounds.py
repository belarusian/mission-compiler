"""Proven-bounds table for mission-compiler.

Bounds are chosen from a table of values that have been proven to work in
production runs (see pipelines/v2/run-cycles.sh: "proven bounds kept: outer
wall 3600s, inner 3000s, outer-steps 40, inner 90"). The table is keyed by
spoke type. Values are pure data - no timestamps, no randomness - so the
compiled output is a deterministic function of its inputs.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Bounds:
    """A single row of the proven-bounds table.

    Attributes:
        outer_wall: wall-clock seconds for the OUTER orchestrator, enforced
            via ``perl -e 'alarm shift; exec @ARGV' <outer_wall> ...``.
        inner_seconds: the ``--inner-seconds`` bound passed to the outer
            orchestrator for the inner spoke.
        outer_steps: the ``--outer-steps`` bound for the outer orchestrator.
        inner_max_steps: the ``--max-steps`` bound for the inner spoke.
    """

    outer_wall: int
    inner_seconds: int
    outer_steps: int
    inner_max_steps: int


#: Proven-bounds table. Keyed by spoke name.
#:
#: DEPRECATED (Cycle 14, issue #45 / TICKET-035): the per-spoke table is
#: superseded by :data:`LLM_CONFIG_BOUNDS` (keyed by LLM config). The rows are
#: kept in lockstep with the proven config rows so the two tables agree:
#: ``project-setup`` mirrors ``LLM_CONFIG_BOUNDS["setup"]`` (7200/1500/25/60,
#: the proven v4 setup row - the legacy 1800s outer wall was a B1 violation by
#: default: ~300s left for the whole outer protocol after one 1500s inner pass;
#: evidence: spoke-lint validation compose 2026-08-19 section [3]) and
#: ``cycle-implementation`` mirrors ``LLM_CONFIG_BOUNDS["2-llm-fast"]``
#: (3600/3000/40/90, the proven dual-LLM row). New code should select rows via
#: :func:`bounds_for_config` / :func:`default_config_for`.
BOUNDS_TABLE: dict[str, Bounds] = {
    # Setup: aligned to the proven LLM_CONFIG_BOUNDS["setup"] row (7200/1500/25/60).
    "project-setup": Bounds(
        outer_wall=7200,
        inner_seconds=1500,
        outer_steps=25,
        inner_max_steps=60,
    ),
    # A full build cycle: aligned to the proven LLM_CONFIG_BOUNDS["2-llm-fast"]
    # row (the default dual-LLM launcher kind, issue #46).
    "cycle-implementation": Bounds(
        outer_wall=3600,
        inner_seconds=3000,
        outer_steps=40,
        inner_max_steps=90,
    ),
}


def bounds_for(spoke: str) -> Bounds:
    """Return the proven bounds for ``spoke``.

    The rows are kept in lockstep with :data:`LLM_CONFIG_BOUNDS` (Cycle 14,
    issue #45): ``project-setup`` mirrors the proven ``setup`` row and
    ``cycle-implementation`` mirrors the proven ``2-llm-fast`` (dual) row, so
    the default (no ``--config``) path and the explicit ``--config`` path can
    never disagree.

    Raises:
        ValueError: if ``spoke`` is not a known spoke type.
    """
    try:
        return BOUNDS_TABLE[spoke]
    except KeyError:
        known = ", ".join(sorted(BOUNDS_TABLE))
        raise ValueError(f"unknown spoke {spoke!r}; known spokes: {known}") from None


#: Proven-bounds table keyed by LLM CONFIG rather than spoke. The v4 pipeline
#: documents three proven configurations (see pipelines/v4/CHANGELOG.md,
#: "Bounds table (per project type)"): a 2-LLM fast config, a single-LLM
#: long-pass config, and the setup config. Values are pure data - no
#: timestamps, no randomness - so the compiled output stays deterministic.
LLM_CONFIG_BOUNDS: dict[str, Bounds] = {
    # 2-LLM (fast + large) with fast inners: TS run, 28 cycles, zero timeouts.
    "2-llm-fast": Bounds(
        outer_wall=3600,
        inner_seconds=3000,
        outer_steps=40,
        inner_max_steps=90,
    ),
    # Single-LLM with long validator passes: Python v6 run, 7/7 cycles; cycle 6
    # needed a full hour before delivery.
    "single-llm-long-pass": Bounds(
        outer_wall=10800,
        inner_seconds=3000,
        outer_steps=60,
        inner_max_steps=90,
    ),
    # Setup (project-setup spoke): lighter than a full build cycle.
    "setup": Bounds(
        outer_wall=7200,
        inner_seconds=1500,
        outer_steps=25,
        inner_max_steps=60,
    ),
}


def bounds_for_config(config: str) -> Bounds:
    """Return the proven bounds for an LLM ``config``.

    This is additive to :func:`bounds_for` (which keys by spoke): it lets a
    caller select a row by LLM configuration instead of by spoke type.

    Raises:
        ValueError: if ``config`` is not a known LLM config name.
    """
    try:
        return LLM_CONFIG_BOUNDS[config]
    except KeyError:
        known = ", ".join(sorted(LLM_CONFIG_BOUNDS))
        raise ValueError(
            f"unknown LLM config {config!r}; known configs: {known}"
        ) from None


#: Default LLM-config row per spoke type (Cycle 14, issue #45 / TICKET-035).
#: The default (no ``--config``) bounds axis routes through these proven
#: :data:`LLM_CONFIG_BOUNDS` rows: ``project-setup`` -> the proven ``setup``
#: row (7200/1500/25/60) and ``cycle-implementation`` -> the DUAL row
#: ``2-llm-fast`` (3600/3000/40/90), because the default launcher kind is
#: dual (issue #46). Operators with long validator passes on dual raise to the
#: conservative B1 line per rule via ``--config single-llm-long-pass``.
DEFAULT_CONFIG_BY_SPOKE: dict[str, str] = {
    "project-setup": "setup",
    "cycle-implementation": "2-llm-fast",
}


def default_config_for(spoke: str) -> str:
    """Return the default LLM-config name for ``spoke``.

    Additive to :func:`bounds_for`: it names the proven
    :data:`LLM_CONFIG_BOUNDS` row that the default (no ``--config``) path
    routes through for ``spoke``. The returned name is always a valid key of
    :data:`LLM_CONFIG_BOUNDS`, so ``bounds_for_config(default_config_for(s))``
    equals ``bounds_for(s)`` for every known spoke (the two tables agree).

    Raises:
        ValueError: if ``spoke`` is not a known spoke type (same contract as
            :func:`bounds_for`).
    """
    try:
        return DEFAULT_CONFIG_BY_SPOKE[spoke]
    except KeyError:
        known = ", ".join(sorted(DEFAULT_CONFIG_BY_SPOKE))
        raise ValueError(f"unknown spoke {spoke!r}; known spokes: {known}") from None
