# TICKET-007: Wire the `bash -n` self-test into the compose path (additive)

**Status:** OPEN
**Priority:** High
**Cycle:** 3
**Module:** `mission_compiler/compose.py` + `mission_compiler/launch.py` (tests in `tests/test_compose.py`, `tests/test_launch.py`)

## Context

The Build Order row for cycles 3-4 is "Launch script generation: heredoc embedding, nohup
wrapper, **bash -n self-test**." Cycle 2 added the standalone `validate_launch_script(script)`
helper in `launch.py` (TICKET-005), but it is NOT yet wired into the compose path. Today
`compose(...)` builds `launch_script` and returns it without ever checking that it is valid
bash; the CLI's `--write` flag then writes that script to disk unvalidated. If a future change
to `build_launch_script` regressed the quoting (e.g. back to double-quoted embedding), the tool
would silently emit a broken nohup file instead of failing fast.

This is ADDITIVE: expose validation as an opt-in flag on `compose(...)` and/or a new helper,
and have the CLI `--write` path validate before writing. Do NOT change any existing public
signature or value (`build_launch_script`, `build_nohup_command`, `_heredoc`, `_perl_alarm`,
`validate_launch_script`, and the existing `compose` keyword set all keep their current
behavior when the new flag is not passed).

## What to do (additive source + tests)

In `mission_compiler/compose.py`:

1. Add a new keyword-only parameter `validate: bool = False` to `compose(...)`. When True, call
   `validate_launch_script(launch_script)` after building the script and before returning; on
   failure let the `ValueError` propagate (fail fast). When False (the default), behavior is
   byte-identical to today. This is additive: existing callers that omit the flag are unchanged.

In `mission_compiler/cli.py`:

2. In the `--write` branch of `main(...)`, call `validate_launch_script(launch.launch_script)`
   immediately before writing the file, so an invalid script fails fast (non-zero exit / raised
   error) rather than producing a broken nohup file on disk. This does not change the default
   print-only path.

Do NOT modify `build_launch_script`, `build_nohup_command`, `_heredoc`, `_perl_alarm`, or
`validate_launch_script`. Do NOT add any new dependency (stdlib only).

## Acceptance tests (new)

- `test_compose_validate_true_accepts_valid_script` — `compose(..., validate=True)` returns a
  `ComposedLaunch` whose `launch_script` is non-empty (i.e. validation passed for the real
  builder output) for both `project-setup` and `cycle-implementation`.
- `test_compose_validate_false_is_default_and_unchanged` — composing with and without
  `validate=True` yields byte-identical `launch_script` (the flag only adds a check, never
  changes the bytes).
- `test_compose_validate_raises_on_bad_script` — using a monkeypatched / injected invalid script
  path (or a direct call to the new helper with a bad string) raises `ValueError, match="bash -n"`.
  If wiring validation through `compose` requires injecting the script for this test, add a small
  additive helper `validate_composed(launch: ComposedLaunch) -> None` in `compose.py` that calls
  `validate_launch_script(launch.launch_script)` and is directly testable.

## Constraints

- Additive only: no existing public signature or value changed; the new flag defaults to False.
- stdlib only (subprocess, tempfile, os). Deterministic: identical inputs -> identical output.
- Every generated launch script must still pass `bash -n`.
