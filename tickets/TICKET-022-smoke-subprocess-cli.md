# TICKET-022: Subprocess smoke test for `python3 -m mission_compiler` + coverage gaps

## Capability
Add a smoke/integration path that runs the CLI via `python3 -m mission_compiler`
(subprocess) end-to-end and asserts exit 0 + all five sections, plus any remaining
uncovered public functions/branches identified by a quick manual coverage pass.
Additive tests only; no behavior change to existing modules.

## Files
- `tests/test_smoke.py` (EXTEND the existing import-only smoke test) — add
  subprocess-based end-to-end CLI tests.

## What to add (in tests/test_smoke.py)
1. **Subprocess end-to-end**: run
   `python3 -m mission_compiler compose <mission> --spoke project-setup` via
   `subprocess.run([...], capture_output=True, text=True)`; assert returncode == 0,
   and that stdout contains all five section headers:
   `[1] GOAL`, `[2] INNER SPOKE COMMAND`, `[3] BOUNDS`, `[4] SEED SCAFFOLD`,
   `[5] NOHUP LAUNCH SCRIPT`.
2. **Subprocess determinism**: run the same command twice; assert stdout is
   byte-identical (compare encoded bytes).
3. **Subprocess `--validate`**: run with `--validate`; assert returncode == 0 and
   all five sections present (validates the composed script via `bash -n`).
4. **Subprocess fail-fast**: run with a bad `--seed-spec` (e.g. `[1,2]` non-object
   JSON); assert returncode != 0 and stderr mentions "object".
5. **Coverage-gap fills** (manual pass — no coverage tooling installed):
   - `mission_compiler.launch.write_launch_script` is already covered in
     test_launch.py; confirm the `python3 -m mission_compiler` entry point
     (`__main__.py`) is exercised by the subprocess tests above.
   - `mission_compiler.cli.parse_seed_spec` list-form (comma-separated) path:
     assert a comma-list seed-spec round-trips through compose and renders the
     classified `[create]` lines (if not already covered).

## Acceptance tests
- All new tests pass with `python3 -m pytest tests/ -x -q`.
- Test count increases monotonically (>= 146 before this cycle).
- The subprocess tests actually spawn a real interpreter (not an in-process call).

## Constraints
- Additive only; no change to `mission_compiler/` public API or signatures.
- stdlib only (subprocess, tempfile, os). Deterministic.
