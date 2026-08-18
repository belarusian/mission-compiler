"""Tests for the proven-bounds table."""

from __future__ import annotations

import pytest

from mission_compiler.bounds import BOUNDS_TABLE, Bounds, bounds_for


def test_bounds_table_has_both_spokes():
    assert "project-setup" in BOUNDS_TABLE
    assert "cycle-implementation" in BOUNDS_TABLE


def test_cycle_bounds_match_proven_values():
    b = bounds_for("cycle-implementation")
    # Proven bounds from pipelines/v2/run-cycles.sh.
    assert b.outer_wall == 3600
    assert b.inner_seconds == 3000
    assert b.outer_steps == 40
    assert b.inner_max_steps == 90


def test_setup_bounds_are_lighter():
    b = bounds_for("project-setup")
    assert b.outer_wall < bounds_for("cycle-implementation").outer_wall
    assert b.inner_max_steps < bounds_for("cycle-implementation").inner_max_steps


def test_bounds_is_frozen_dataclass():
    b = bounds_for("project-setup")
    with pytest.raises(Exception):
        b.outer_wall = 1  # type: ignore[misc]


def test_unknown_spoke_raises():
    with pytest.raises(ValueError, match="unknown spoke"):
        bounds_for("no-such-spoke")


def test_bounds_fields_are_positive_ints():
    for b in BOUNDS_TABLE.values():
        assert isinstance(b, Bounds)
        assert b.outer_wall > 0
        assert b.inner_seconds > 0
        assert b.outer_steps > 0
        assert b.inner_max_steps > 0
