# TICKET-005: Launch — `bash -n` self-test (additive) + tests

**Status:** OPEN
**Priority:** High
**Cycle:** 2
**Module:** `mission_compiler/launch.py` (tests in `tests/test_launch.py`)

## Context

The Build Order row for cycles 3-4 is "Launch script generation: heredoc embedding, nohup
wrapper, **bash -n self-test**." The setup-era `build_launch_script` already emits a valid
script (single-quoted heredocs), but there is NO function that validates a generated launch
script is syntactically valid bash. The mission invariant states "Every generated launch script
must pass `bash -n`" — that invariant is currently only checked ad-hoc by hand, not enforced or
tested in the module.

This is ADDITIVE: add a new public function to `launch.py`; leave `build_launch_script`,
`build_nohup_command`, `_heredoc`, and `_perl_alarm` untouched (no signature change).

## What to do (additive source + tests)

In `mission_compiler/launch.py`:

1. Add `validate_launch_script(script: str) -> None` that runs `bash -n` on the script text
   (via a temp file, stdlib `subprocess`) and raises `ValueError` with a message containing
   "bash -n" plus the stderr if the syntax check fails; returns normally (None) when valid.
   - Must be deterministic: it performs no I/O other than writing/reading a single temp file
     that is always cleaned up, and its return value depends only on `script`.
   - Use `tempfile` + `subprocess.run(["bash", "-n", path])`; clean the temp file in a
     `finally` block. Do NOT add any new dependency (stdlib only: subprocess, tempfile, os).

Do NOT modify `build_launch_script`, `build_nohup_command`, `_heredoc`, or `_perl_alarm`.

## Acceptance tests (new, in `tests/test_launch.py`)

- `test_validate_accepts_generated_setup_script` — build a real script via
  `build_launch_script(...)` and assert `validate_launch_script(script)` returns None.
- `test_validate_accepts_generated_cycle_script` — same for a cycle-implementation inner command.
- `test_validate_rejects_bad_syntax` — `validate_launch_script("if then fi\n")` (or an equally
  invalid snippet) raises `ValueError, match="bash -n"`.
- `test_validate_message_includes_stderr` — the raised message contains a non-empty stderr
  fragment from bash.

## Constraints

- Additive only: no existing public signature or value changed.
- stdlib only (subprocess, tempfile, os). Deterministic return value for identical input.
