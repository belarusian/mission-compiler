# TICKET-010: Harden launch-script generation — remaining quoting/heredoc edge cases

**Status:** OPEN
**Priority:** Medium
**Cycle:** 4
**Module:** `tests/test_launch.py` (exercises `mission_compiler/launch.py`)

## Context

The Build Order row for cycles 3-4 is "Launch script generation: heredoc embedding, nohup
wrapper, bash -n self-test." Cycle 2 pinned the tricky-goal quoting edge case (single/double
quotes, `$`, backtick, embedded newline) and byte-determinism. Three boundary cases of the
single-quoted-heredoc embedding are still untested:

1. **Empty goal** — `goal=""`. The heredoc body becomes a single blank line between the
   delimiters. Must still be valid bash and byte-deterministic.
2. **Goal ending in a newline** — `goal="...\n"`. The trailing newline sits just before the
   closing delimiter; must not collapse or shift the delimiter line, and must stay valid bash.
3. **Very long single-line goal** — a single line with no newlines (e.g. 5000+ chars) that also
   carries quote/`$`/backtick bytes. Must be preserved verbatim on one line and pass `bash -n`.

This is TESTS-ONLY: no source change to `launch.py`. It locks down the boundary behavior of the
heredoc embedding so a future regression (delimiter collision, newline handling, long-line
truncation) fails the gate. Each case must assert BOTH byte-determinism (two builds equal as str
and as bytes) AND that the generated script passes `bash -n`.

## What to do (tests only)

In `tests/test_launch.py`, add a helper `_build(goal)` that builds a full script for a given goal
using fixed bounds + a setup inner command, and:

1. `test_empty_goal_script_passes_bash_n_and_deterministic`: build with `goal=""`; assert the two
   builds are byte-equal; write to temp file and run `bash -n` (returncode 0). Also assert the
   heredoc delimiters `GOAL_EOF` appear exactly twice (open + close) so an empty body did not
   swallow a delimiter.
2. `test_goal_ending_in_newline_preserved_and_bash_n`: build with `goal="line one\n"`; assert the
   exact goal bytes (`"line one\n"`) appear as a contiguous substring of the script (verbatim,
   trailing newline intact); two builds byte-equal; `bash -n` returncode 0.
3. `test_very_long_single_line_goal_preserved_and_bash_n`: build with a single-line goal of length
   >= 5000 that embeds `"`, `'`, `$HOME`, and a backtick; assert the exact goal bytes appear as a
   contiguous substring (no truncation, no wrapping); two builds byte-equal; `bash -n` returncode 0.

## Constraints
- stdlib only. No new dependencies.
- Do NOT change any existing public signature in `launch.py`.
- Every generated launch script must pass `bash -n`.
