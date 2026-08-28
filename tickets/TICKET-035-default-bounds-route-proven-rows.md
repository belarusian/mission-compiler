# TICKET-035 — default bounds route to the proven LLM_CONFIG_BOUNDS rows (issue #45, semantic update 2026-08-27)

## Capability
The default (no `--config`) bounds axis is frozen at a stale row while the proven table
moved. `--spoke project-setup` with no `--config` emits 1800/1500/20 (legacy BOUNDS_TABLE)
— a 1800s outer wall leaves ~300s for the entire outer protocol after one 1500s inner
pass (B1 violation by default). The proven rows already exist in `LLM_CONFIG_BOUNDS`.

## Required (supersedes original "setup only" target)
1. `--spoke project-setup`, no `--config` -> the proven `setup` row (7200/1500/25/60).
2. `--spoke cycle-implementation`, no `--config` -> the DUAL row `2-llm-fast`
   (3600/3000/40/90) — the default launcher kind is dual (TICKET-036).
3. `LLM_CONFIG_BOUNDS['setup']` must equal the default when `--spoke project-setup`
   (the two tables agree). Legacy `BOUNDS_TABLE` 1800-row aligned to the proven setup
   row and marked deprecated in the docstring. `bounds_for()` public behavior stays
   additive-compatible (same signature, same ValueError contract).
4. Bounds must follow the config kind emitted in the script (TICKET-036), so [3] BOUNDS
   and the exported pins in [5] never disagree: explicit `--config` keeps routing through
   `bounds_for_config(config)` unchanged.

## Fix (additive)
- `bounds.py`: align `BOUNDS_TABLE["project-setup"]` to (7200, 1500, 25, 60) with a
  deprecation note; add `DEFAULT_CONFIG_BY_SPOKE: dict[str, str] = {"project-setup": "setup",
  "cycle-implementation": "2-llm-fast"}` and `default_config_for(spoke) -> str` (ValueError
  for unknown spoke, same contract as bounds_for).
- `compose.py`: when `config is None`, route through
  `bounds_for_config(default_config_for(spoke))` (explicit `--config` path unchanged).

## Evidence to cite in tests/README
JUNIOR-v2 §5 proven-bounds table + B1 rule (outer_wall >= 3 x max_observed_inner_pass);
pipelines/v4/CHANGELOG.md bounds table; the 1800-row death class: spoke-lint validation
compose 2026-08-19 section [3].

## Acceptance tests
- `bounds_for("project-setup") == LLM_CONFIG_BOUNDS["setup"]` (tables agree).
- `bounds_for_config(default_config_for("project-setup"))` == setup row (7200/1500/25/60).
- compose(project-setup, no config) -> bounds 7200/1500/25/60 in [3] BOUNDS.
- compose(cycle-implementation, no config) -> bounds 3600/3000/40/90 (dual row).
- compose(cycle-implementation, config="single-llm-long-pass") -> 10800 row (unchanged).
- `default_config_for("bogus")` raises ValueError.
- Existing `--config` tests still pass (explicit axis untouched).

## Files
- `mission_compiler/bounds.py`
- `mission_compiler/compose.py`
- `tests/test_bounds.py`, `tests/test_compose.py`, `tests/test_compose_config.py` (update stale 1800 pins)
