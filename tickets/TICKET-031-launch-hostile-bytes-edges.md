# TICKET-031 — build_launch_script/_heredoc hostile-bytes edges (POLISH, bounded post-plan)

## Capability
The Cycle 12 "What to Build" row names a second residual coverage gap: *"`build_launch_script`/
`_heredoc` with hostile goal bytes like backticks/`$`/single-quotes already partly covered —
confirm"*. The existing `_tricky_goal()` covers a single quote, a double quote, `$HOME`, a
backtick, and an embedded newline. But three further hostile-bytes edges are **not** pinned:

1. **Heredoc delimiter collision.** `_heredoc` uses the fixed delimiter `GOAL_EOF`. If the
   goal text itself contains a line that is exactly `GOAL_EOF`, the single-quoted heredoc body
   would terminate early and the rest of the goal would leak into the script as bash. This is
   the one input class that can actually break `bash -n` (or change semantics) for the current
   builder, and it is untested. We must pin the *actual* behavior deterministically: either
   the script still passes `bash -n` and the goal bytes are preserved verbatim, or — if it does
   not — document that limitation precisely. (The honest record requires we assert what the
   code really does, byte-for-byte.)
2. **NUL byte** in the goal: pin whether the emitted script is still valid bash / how the NUL
   round-trips through `bash -n`.
3. **CRLF line endings** and **leading/trailing newline** in the goal: pin that the bytes are
   preserved verbatim and the script passes `bash -n`.

This is a bounded POLISH gap (test coverage of a public function). No source change unless the
delimiter-collision case reveals a real bug; if it does, the fix must be additive and keep every
existing test green.

## File paths + signatures
- `tests/test_launch.py` — new tests (additive only; do not modify existing tests).
  Use `mission_compiler.launch.build_launch_script(...)` with `goal=` set to each hostile value
  and assert the deterministic outcome (bash -n result + verbatim byte preservation where the
  code guarantees it).
- `mission_compiler/launch.py` — **only if** the delimiter-collision test reveals a genuine
  bug that breaks `bash -n`; any fix must be additive (e.g. derive a collision-free delimiter)
  and keep every existing launch test byte-green. If no bug, this file is untouched.

## Behavior contract (deterministic)
- For each of {NUL byte, CRLF, leading newline, trailing newline}: the goal bytes appear as a
  contiguous substring of the emitted script (verbatim preservation) AND the script passes
  `bash -n` — pin whichever subset the code actually satisfies and assert it exactly.
- For the delimiter-collision goal (a line equal to `GOAL_EOF`): assert the *actual* deterministic
  outcome of `build_launch_script(...)` + `validate_launch_script(...)`. If it raises / fails
  `bash -n`, that is a real limitation to document in the ticket's Decisions; if an additive fix
  is made, assert the fixed behavior (collision-free delimiter -> valid bash + verbatim bytes).

## Acceptance tests (new, additive)
1. `test_goal_with_nul_byte_deterministic` — goal containing `\x00`: pin the exact deterministic
   outcome of build + validate (assert what really happens, byte-for-byte).
2. `test_goal_with_crlf_preserved_and_bash_n` — goal with `\r\n`: bytes preserved verbatim and
   script passes `bash -n`.
3. `test_goal_leading_trailing_newline_preserved_and_bash_n` — goal starting and ending with a
   newline: verbatim + `bash -n` green.
4. `test_goal_heredoc_delimiter_collision_deterministic` — goal containing a line equal to
   `GOAL_EOF`: assert the exact deterministic outcome (valid-bash + verbatim, or the documented
   limitation / additive fix).
5. `test_hostile_bytes_byte_identical_across_runs` — two equal build calls for each hostile goal
   are byte-identical.

## Constraints
- Additive only: no change to any existing public API or signature; if a source fix is needed it
  must keep every existing launch test green.
- stdlib only. Deterministic: same input -> byte-identical output; no timestamps/randomness.
