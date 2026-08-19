# TICKET-006: Launch — quoting edge case preserved literally + byte-determinism tests

**Status:** OPEN
**Priority:** High
**Cycle:** 2
**Module:** `mission_compiler/launch.py` (tests in `tests/test_launch.py`)

## Context

The Build Order row for cycles 3-4 says: "Ensure the composed launch script is byte-deterministic
for identical inputs and always passes `bash -n`. **Cover the quoting edge case that broke the
setup-era double-quoted embedding.**" The setup-era bug: embedding GOAL/INNER in a *double-quoted*
heredoc (or plain double-quoted assignment) lets `$VAR`, backticks, and unescaped newlines be
interpreted by bash — so a goal containing `\$HOME`, `` \`cmd\` ``, or a literal newline would
corrupt the script. The current `_heredoc` uses a single-quoted delimiter (`<<'NAME_EOF'`) which
preserves every byte literally, but there is NO test that proves this: no test feeds a GOAL full of
single quotes, double quotes, `$`, backticks, and newlines and asserts (a) the script still passes
`bash -n` and (b) the exact goal bytes appear verbatim in the emitted heredoc body.

This is TESTS-ONLY (no source change): the single-quoted heredoc already behaves correctly; we add
the tests that pin it down so a future regression to double-quoting fails the gate.

## What to do (tests only)

In `tests/test_launch.py`:

1. Add a helper `_tricky_goal()` returning a GOAL string containing, in one value: a single quote
   (`'`), a double quote (`"`), a dollar sign (`$HOME`), a backtick command (`` `id` ``), and a
   literal newline.
2. Add tests:
   - `test_tricky_goal_script_passes_bash_n` — build the script with `_tricky_goal()`; write it to
     a temp file; assert `subprocess.run(["bash","-n",path])` returncode == 0 (clean up in finally).
   - `test_tricky_goal_bytes_preserved_verbatim` — the exact `_tricky_goal()` string appears as a
     contiguous substring of the emitted script (proves literal preservation, not re-quoting).
   - `test_double_quoted_embedding_would_break` — construct the *hypothetical* double-quoted
     assignment for the same goal and assert it is NOT byte-identical to the single-quoted heredoc
     body (documents why single-quoting is required); keep this assertion purely structural so it
     stays deterministic.
   - `test_launch_script_byte_deterministic_across_runs` — build twice with identical inputs
     (including a tricky goal) and assert byte-equality (`==`) of the two full scripts.

## Constraints

- Tests only: do NOT modify any source module in this ticket.
- stdlib only (subprocess, tempfile, os). Deterministic assertions (no timestamps/randomness).
