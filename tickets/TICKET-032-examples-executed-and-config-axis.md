# TICKET-032 — examples/ executed by a test + --config axis exercised (POLISH, bounded post-plan)

## Capability
The Cycle 12 "What to Build" row names a third residual gap: *"README/example refinements that
keep docs byte-consistent with code"*. Two concrete facts make this a genuine, testable gap:

1. **`examples/` is never executed by any test.** `examples/compose-fleet.sh` and
   `examples/compose-fourseer.sh` are advertised as "runnable byte-deterministic examples" (and
   the README/release notes say so), but no test runs them. If a flag name, default, or section
   header drifted, nothing would catch it. A test that executes both example scripts and asserts
   exit 0 + `bash -n` green + determinism closes this doc/code-consistency gap.
2. **Neither example uses `--config`.** The `--config` LLM-bounds axis (TICKET-025, Cycle 10) is
   a documented public capability, yet no shipped example demonstrates it. Adding a third example
   that composes a real project with `--config single-llm-long-pass` (and asserts the `[3] BOUNDS`
   section reflects the selected row) makes the documented capability reachable in the examples and
   keeps the docs byte-consistent with the code.

This is a bounded POLISH gap (examples / doc-code consistency). No change to any public API or
signature in `mission_compiler/`.

## File paths + signatures
- `tests/test_examples.py` — NEW test module (additive only). Executes each example script as a
  real subprocess (`bash examples/<name>.sh`) and asserts: exit 0; the written launch script
  passes an explicit `bash -n`; all five section headers appear on stdout; and two identical runs
  produce byte-identical stdout. Uses the fixed `/tmp/mission-compiler-example/...` paths the
  scripts already use (no mktemp, so output stays deterministic).
- `examples/compose-config.sh` — NEW example script (additive only), mirroring the style of the
  two existing examples: composes a real project with `--config single-llm-long-pass`, writes to a
  fixed throwaway path, `--write --validate`, and prints the rendered launch. Deterministic
  (fixed paths, no timestamps).
- `README.md` — additive only: add the new example to the examples list / usage section so the
  docs stay byte-consistent with what ships.

## Behavior contract (deterministic)
- Each existing example script exits 0 and its written launch script passes `bash -n`.
- The new `compose-config.sh` exits 0, its written launch script passes `bash -n`, and its stdout
  contains the `[3] BOUNDS` line "outer wall (perl alarm): 10800s" (the single-llm-long-pass row).
- Two identical runs of any example produce byte-identical stdout.

## Acceptance tests (new, additive)
1. `test_example_fleet_runs_and_bash_n` — run `examples/compose-fleet.sh`: rc 0; written script
   passes explicit `bash -n`; five headers on stdout.
2. `test_example_fourseer_runs_and_bash_n` — same for `examples/compose-fourseer.sh`.
3. `test_example_config_runs_and_reflects_bounds` — run the new `examples/compose-config.sh`: rc 0;
   written script passes `bash -n`; stdout contains "outer wall (perl alarm): 10800s".
4. `test_examples_byte_identical_across_runs` — two identical runs of each example are byte-identical
   on stdout.

## Constraints
- Additive only: no change to any public API or signature in `mission_compiler/`.
- stdlib only. Deterministic: same input -> byte-identical output; no timestamps/randomness.
