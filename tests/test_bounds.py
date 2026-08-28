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


def test_setup_bounds_match_proven_setup_row():
    # Cycle 14 (issue #45): the default setup row is the proven v4 setup row
    # (7200/1500/25/60), NOT the legacy 1800s wall (a B1 violation by default:
    # ~300s left for the whole outer protocol after one 1500s inner pass).
    b = bounds_for("project-setup")
    assert b == Bounds(outer_wall=7200, inner_seconds=1500, outer_steps=25, inner_max_steps=60)


def test_bounds_tables_agree_with_llm_config_rows():
    # Cycle 14 (issue #45): the legacy per-spoke table and the proven
    # LLM_CONFIG_BOUNDS table must agree row-for-row, so the default (no
    # --config) path and the explicit --config path can never disagree.
    assert bounds_for("project-setup") == LLM_CONFIG_BOUNDS["setup"]
    assert bounds_for("cycle-implementation") == LLM_CONFIG_BOUNDS["2-llm-fast"]


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


# --- TICKET-035 (issue #45): default config routing ------------------------


def test_default_config_for_setup_is_setup_row():
    from mission_compiler.bounds import default_config_for

    assert default_config_for("project-setup") == "setup"


def test_default_config_for_cycle_is_dual_row():
    from mission_compiler.bounds import default_config_for

    # The default launcher kind is dual (issue #46), so the default cycle row
    # is the proven 2-llm-fast row.
    assert default_config_for("cycle-implementation") == "2-llm-fast"


def test_default_config_for_unknown_spoke_raises():
    from mission_compiler.bounds import default_config_for

    with pytest.raises(ValueError, match="unknown spoke"):
        default_config_for("no-such-spoke")


def test_default_config_routing_equals_bounds_for():
    from mission_compiler.bounds import default_config_for

    for spoke in ("project-setup", "cycle-implementation"):
        assert bounds_for_config(default_config_for(spoke)) == bounds_for(spoke)
