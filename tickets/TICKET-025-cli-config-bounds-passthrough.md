# TICKET-025 — CLI `--config` passthrough to LLM_CONFIG_BOUNDS

## Class
POLISH (CLI passthrough gap). Bounded post-plan; strictly additive.

## Problem
`mission_compiler/bounds.py` exposes a second, public bounds table keyed by LLM
configuration: `LLM_CONFIG_BOUNDS` and `bounds_for_config(config)` (rows
`2-llm-fast`, `single-llm-long-pass`, `setup`). But the CLI has **no way to reach
it**: `compose(...)` always selects bounds via `bounds_for(spoke)`, and
`build_parser()` exposes no flag that maps onto `bounds_for_config`. The README
even advertises "chosen by spoke **and LLM config**" for section [3] BOUNDS, yet
the LLM-config axis is unreachable from the front door. This is a genuine CLI
passthrough gap in the POLISH class.

## Capability
Add an opt-in `--config` flag that selects bounds from `LLM_CONFIG_BOUNDS` via
`bounds_for_config`, WITHOUT changing any existing public signature:

1. `mission_compiler/compose.py`: add a new **keyword-only, default-None** param
   `config: str | None = None` to `compose(...)`. When `config is None` (the
   default) bounds are chosen exactly as today via `bounds_for(spoke)` — byte
   identical. When `config` is given, bounds come from `bounds_for_config(config)`
   instead. The existing `spoke not in SPOKES` check and the `ValueError` raised
   by an unknown config both remain (an unknown config surfaces as a ValueError).
2. `mission_compiler/cli.py`: add `--config` (default `None`) to the `compose`
   subparser, help text noting it selects bounds from the LLM-config table and is
   default-off (byte-identical when omitted). Pass `config=args.config` through to
   `compose(...)`.

No existing signature changes: `compose` gains a new keyword-only param with a
default; `build_parser` gains one new option. All other behavior is unchanged.

## Files
- `mission_compiler/compose.py` (add `config` kwarg + bounds selection branch).
- `mission_compiler/cli.py` (add `--config` flag + pass-through).
- `README.md` (document the new `--config` flag in the flag table; additive row).

## Acceptance tests
Add tests (in `tests/test_compose.py` and/or a new `tests/test_cli_config.py`):

1. `compose(mission, config=None)` is byte-identical to `compose(mission)` for both
   spokes (render + launch_script compared as encoded bytes) — default unchanged.
2. `compose(mission, spoke="cycle-implementation", config="single-llm-long-pass")`
   yields bounds equal to `bounds_for_config("single-llm-long-pass")` and differs
   from the spoke-default bounds (outer_wall 10800 vs 3600).
3. `compose(mission, config="no-such-config")` raises `ValueError`.
4. CLI: `main(["compose", "Build it.", "--config", "2-llm-fast"])` returns rc 0 and
   the rendered [3] BOUNDS section reflects the `2-llm-fast` row; omitting
   `--config` is byte-identical to before (deterministic stdout across two runs).
5. CLI: a bad `--config` value fails fast with non-zero exit and an error on stderr.

All tests pass with `python3 -m pytest tests/ -x -q`; test count increases; ruff +
mypy clean; `git diff main` is additive only (no existing public signature changed).
