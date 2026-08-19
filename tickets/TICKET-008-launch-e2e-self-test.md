# TICKET-008: End-to-end launch-script self-test (build -> write temp -> `bash -n` -> nohup path)

**Status:** OPEN
**Priority:** High
**Cycle:** 3
**Module:** `tests/test_launch.py` (exercises `mission_compiler/launch.py`)

## Context

The Build Order row for cycles 3-4 is "Launch script generation: heredoc embedding, nohup
wrapper, **bash -n self-test**." Cycle 2 pinned the quoting edge case and byte-determinism at
the unit level. What is still missing is a true END-TO-END self-test that mirrors exactly what
the CLI does when it writes a launch file: build a full script via `build_launch_script`, write
it to a real temp file, run `bash -n` on that file (not just the in-memory string), and assert
that the nohup wrapper produced by `build_nohup_command` references the correct path. This must
cover BOTH spoke types (`project-setup` and `cycle-implementation`) using realistic bounds taken
from the proven-bounds table (`bounds_for(spoke)`), not hand-typed numbers.

This is TESTS-ONLY: no source change to `launch.py`. It locks down the full write-and-validate
contract so a future regression (bad heredoc, wrong nohup path, broken quoting) fails the gate.

## What to do (tests only)

In `tests/test_launch.py`, add an end-to-end self-test covering both spoke types:

1. For each spoke in (`project-setup`, `cycle-implementation`):
   - Build a realistic inner command (`build_setup_command` / `build_cycle_command`).
   - Pull the REAL bounds from the proven table via `bounds_for(spoke)` (do not hard-code).
   - Build the full script with `build_launch_script(...)`.
   - Write it to a temp file (`tempfile.mkstemp`), run `bash -n <path>` via stdlib
     `subprocess`, assert returncode 0, and clean up in a `finally` block.
   - Compute `script_path = f"{project_dir}/launch-{name}.sh"` (the same path the CLI uses) and
     assert `build_nohup_command(script_path)` references that exact path: it starts with
     `nohup bash {script_path}`, redirects to `{script_path}.out`, and ends with `&`.

## Acceptance tests (new, in `tests/test_launch.py`)

- `test_e2e_setup_script_written_and_bash_n_passes` — project-setup spoke: build -> write temp
  file -> `bash -n` returncode 0. Uses `bounds_for("project-setup")`.
- `test_e2e_cycle_script_written_and_bash_n_passes` — cycle-implementation spoke: same flow,
  uses `bounds_for("cycle-implementation")`.
- `test_e2e_nohup_references_correct_path_setup` — the nohup command for the setup script path
  references the exact `<project-dir>/launch-<name>.sh` path and its `.out` redirect.
- `test_e2e_nohup_references_correct_path_cycle` — same assertion for the cycle spoke's path.

## Constraints

- Tests only; no source change to `launch.py`.
- stdlib only (subprocess, tempfile, os). Deterministic: identical inputs -> identical script.
- Every generated launch script must pass `bash -n`.
