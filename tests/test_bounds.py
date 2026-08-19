"""Tests for the proven-bounds table."""

from __future__ import annotations

import pytest

from mission_compiler.bounds import (
    BOUNDS_TABLE,
    LLM_CONFIG_BOUNDS,
    Bounds,
    bounds_for,
    bounds_for_config,
)


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


# --- TICKET-004: additive LLM-config proven table -------------------------


def test_llm_config_table_has_three_rows():
    assert set(LLM_CONFIG_BOUNDS) == {
        "2-llm-fast",
        "single-llm-long-pass",
        "setup",
    }


def test_2llm_fast_matches_proven_values():
    b = bounds_for_config("2-llm-fast")
    # Proven 2-LLM (fast+large) config: TS run, 28 cycles, zero timeouts.
    assert b.outer_wall == 3600
    assert b.inner_seconds == 3000
    assert b.outer_steps == 40
    assert b.inner_max_steps == 90


def test_single_llm_long_pass_matches_proven_values():
    b = bounds_for_config("single-llm-long-pass")
    # Proven single-LLM config: Python v6, cycle 6 needed a full hour.
    assert b.outer_wall == 10800
    assert b.inner_seconds == 3000
    assert b.outer_steps == 60
    assert b.inner_max_steps == 90


def test_setup_config_matches_proven_values():
    b = bounds_for_config("setup")
    # Proven setup config: fourseer + mission-compiler setups.
    assert b.outer_wall == 7200
    assert b.inner_seconds == 1500
    assert b.outer_steps == 25
    assert b.inner_max_steps == 60


def test_bounds_for_config_unknown_raises():
    with pytest.raises(ValueError, match="unknown LLM config"):
        bounds_for_config("no-such-config")


def test_llm_config_rows_are_positive_ints():
    for b in LLM_CONFIG_BOUNDS.values():
        assert isinstance(b, Bounds)
        assert b.outer_wall > 0
        assert b.inner_seconds > 0
        assert b.outer_steps > 0
        assert b.inner_max_steps > 0
