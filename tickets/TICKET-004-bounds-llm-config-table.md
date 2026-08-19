# TICKET-004: Bounds — LLM-config proven table (additive) + coverage tests

**Status:** OPEN
**Priority:** High
**Cycle:** 1
**Module:** `mission_compiler/bounds.py` (tests in `tests/test_bounds.py`)

## Context

The Build Order row for cycles 1-2 says: "bounds table returns the proven rows per LLM config
(2-LLM fast / single-LLM long-pass / setup)." The v4 CHANGELOG
(`~/Research/four/pipelines/v4/CHANGELOG.md`, "Bounds table (per project type)") and
`AGENTS.md` document THREE proven configs:

| Config | outer wall | inner-seconds | outer-steps | inner max-steps | Evidence |
|--------|-----------|---------------|-------------|-----------------|----------|
| 2-LLM (fast+large), fast inners | 3600s | 3000s | 40 | 90 | TS: 28 cycles, zero timeouts |
| Single-LLM, long validator passes | 10800s | 3000s | 60 | 90 | Python v6: 7/7 cycles, cycle 6 needed full hour |
| Setup (project-setup spoke) | 7200s | 1500s | 25 | 60 (spoke default) | fourseer + mission-compiler setups |

Current `bounds.py` keys the table by SPOKE (`project-setup`, `cycle-implementation`) and only
encodes two rows. The single-LLM long-pass config is not represented anywhere, and there is no
way to select a bounds row by LLM config. Per the invariant "new capabilities are new modules or
new flags" and "public API never changes", this is ADDITIVE: add a new table + accessor; leave
`BOUNDS_TABLE`, `bounds_for`, and `Bounds` untouched.

## What to do (additive source + tests)

In `mission_compiler/bounds.py`:

1. Add `LLM_CONFIG_BOUNDS: dict[str, Bounds]` with the three proven rows above, keyed by config
   name: `"2-llm-fast"`, `"single-llm-long-pass"`, `"setup"`. Values are pure data (no
   timestamps/randomness).
2. Add `bounds_for_config(config: str) -> Bounds` that returns the row for a known config and
   raises `ValueError(f"unknown LLM config {config!r}; known configs: ...")` otherwise (mirrors
   `bounds_for`).

Do NOT modify `BOUNDS_TABLE`, `bounds_for`, or the `Bounds` dataclass.

## Acceptance tests (new, in `tests/test_bounds.py`)

- `test_llm_config_table_has_three_rows` — keys are exactly the three config names.
- `test_2llm_fast_matches_proven_values` — 3600/3000/40/90.
- `test_single_llm_long_pass_matches_proven_values` — 10800/3000/60/90.
- `test_setup_config_matches_proven_values` — 7200/1500/25/60.
- `test_bounds_for_config_unknown_raises` — `ValueError, match="unknown LLM config"`.
- `test_llm_config_rows_are_positive_ints` — all four fields > 0 for every row.

## Constraints

- Additive only: no existing public signature or value changed.
- stdlib only. Deterministic pure data.
