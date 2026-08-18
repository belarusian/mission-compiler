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
BOUNDS_TABLE: dict[str, Bounds] = {
    # Setup is lighter: it only scaffolds the repo and writes 3 artifacts.
    "project-setup": Bounds(
        outer_wall=1800,
        inner_seconds=1500,
        outer_steps=20,
        inner_max_steps=60,
    ),
    # A full build cycle is heavier: it launches the auditor and validator.
    "cycle-implementation": Bounds(
        outer_wall=3600,
        inner_seconds=3000,
        outer_steps=40,
        inner_max_steps=90,
    ),
}


def bounds_for(spoke: str) -> Bounds:
    """Return the proven bounds for ``spoke``.

    Raises:
        ValueError: if ``spoke`` is not a known spoke type.
    """
    try:
        return BOUNDS_TABLE[spoke]
    except KeyError:
        known = ", ".join(sorted(BOUNDS_TABLE))
        raise ValueError(f"unknown spoke {spoke!r}; known spokes: {known}") from None
