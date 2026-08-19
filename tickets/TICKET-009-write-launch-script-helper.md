# TICKET-009: Additive `write_launch_script` helper (write bytes -> return nohup command)

**Status:** OPEN
**Priority:** High
**Cycle:** 4
**Module:** `mission_compiler/launch.py` + `tests/test_launch.py`

## Context

The Build Order row for cycles 3-4 is "Launch script generation: heredoc embedding, nohup
wrapper, bash -n self-test." Cycles 2-3 added `validate_launch_script`, wired validation into
the compose path, and pinned the E2E write->`bash -n`->nohup contract. What is still missing is a
small, first-class ADDITIVE helper that does exactly what the CLI's `--write` branch does by hand:
write a composed launch script to a path and return the nohup command for it. Today the CLI
re-implements this write+nohup logic inline; a named helper makes the contract reusable and
testable in one place without changing any existing public signature.

This is ADDITIVE-ONLY: a new function `write_launch_script` in `launch.py`. No existing public
signature changes. The helper must be byte-deterministic (same script + same path -> same bytes on
disk, same returned command) and the written file must pass `bash -n`.

## What to do

In `mission_compiler/launch.py`, add:

```python
def write_launch_script(script: str, path: str) -> str:
    """Write ``script`` to ``path`` (UTF-8, exact bytes) and return the nohup command.

    Creates parent directories if needed. Returns ``build_nohup_command(path)`` so the
    caller gets a ready-to-run background launch line for the file just written. The
    function is a pure function of its inputs: identical (script, path) always writes the
    same bytes and returns the same command. No timestamps or randomness are introduced.

    Args:
        script: the full launch script text to write.
        path: destination path for the ``.sh`` file.

    Returns:
        The nohup command string that launches ``path`` in the background.
    """
```

Implementation notes:
- Use `pathlib.Path(path)`; `mkdir(parents=True, exist_ok=True)` on the parent.
- Write with `Path.write_text(script, encoding="utf-8")` (exact bytes, no newline rewriting).
- Return `build_nohup_command(path)`.

## Acceptance tests (in `tests/test_launch.py`)

1. `test_write_launch_script_writes_exact_bytes`: build a real script via `build_launch_script`,
   call `write_launch_script(script, tmp_path/...)`, read the file back and assert it equals the
   input script byte-for-byte (`read_text` == script; also compare `.encode("utf-8")`).
2. `test_write_launch_script_returns_correct_nohup_command`: assert the returned string equals
   `build_nohup_command(path)` and references the exact path + `.out` redirect + trailing `&`.
3. `test_write_launch_script_creates_parent_dirs`: write into a nested non-existent dir under a
   temp root; assert the file exists at the full path.
4. `test_write_launch_script_written_file_passes_bash_n`: after writing, run `bash -n <path>` via
   stdlib subprocess and assert returncode 0.
5. `test_write_launch_script_is_deterministic`: call twice with the same (script, path); both
   returned commands equal and the on-disk bytes are identical across calls.

## Constraints
- stdlib only (pathlib, os). No new dependencies.
- Do NOT change any existing public signature in `launch.py`.
- Every generated launch script must pass `bash -n`.
