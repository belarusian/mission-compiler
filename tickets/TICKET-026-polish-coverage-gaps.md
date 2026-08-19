# TICKET-026 — POLISH coverage gaps: nohup/write determinism + config flag matrix

## Class
POLISH (missing test coverage). Bounded post-plan; additive tests only.

## Problem
Two small, real coverage gaps remain after cycles 1-9:

1. `mission_compiler/launch.py::build_nohup_command` is a public helper but has no
   dedicated unit test pinning its exact output shape and determinism (it is only
   exercised indirectly through `write_launch_script`).
2. The new `--config` flag added by TICKET-025 needs a full CLI flag-matrix test:
   the combination `compose <mission> --spoke cycle-implementation --cycle N
   --config C --validate --write` must produce a valid, deterministic launch whose
   [3] BOUNDS section reflects the selected LLM-config row, and omitting `--config`
   must remain byte-identical to the pre-flag behavior.

## Capability
Add additive tests that close these gaps without changing any source behavior:

1. `tests/test_launch.py`: add unit tests for `build_nohup_command` — it returns
   exactly `nohup bash <path> > <path>.out 2>&1 &`, is a pure function of its input,
   and is byte-identical across equal inputs (compared as encoded bytes).
2. `tests/test_cli_config.py` (or append to `tests/test_cli.py`): add the
   `--config` CLI flag-matrix test described in TICKET-025 acceptance item 4/5 —
   full matrix with `--spoke cycle-implementation --cycle N --config C --validate
   --write`, asserting rc 0, a written script that passes an explicit `bash -n`,
   the [3] BOUNDS section reflecting the config row, and byte-identical stdout
   across identical invocations; plus the bad-config fail-fast path.

## Files
- `tests/test_launch.py` (append `build_nohup_command` unit tests).
- `tests/test_cli_config.py` (new) or `tests/test_cli.py` (append) for the
  `--config` flag-matrix tests.

## Acceptance tests
All new tests pass with `python3 -m pytest tests/ -x -q`; test count increases
monotonically; ruff + mypy clean; `git diff main` is additive only (tests only, no
source change). No change to any public API or signature in `mission_compiler/`.
