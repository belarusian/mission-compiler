# TICKET-003: Spoke command renderer — full spoke coverage + quoting round-trip

**Status:** OPEN
**Priority:** High
**Cycle:** 1
**Module:** `mission_compiler/spoke_cmd.py` (tests in `tests/test_spoke_cmd.py`)

## Context

The Build Order row for cycles 1-2 says: "verify the spoke command renderer covers all spokes
(project-setup, cycle-implementation, cycle-implementation-v3, auditor, validator)."

Current state: `spoke_cmd.py` exposes exactly two builders — `build_setup_command` (project-setup)
and `build_cycle_command` (cycle-implementation / v3). The `auditor` and `validator` spokes are
INNER sub-spokes launched by the cycle spoke; they are not top-level launch targets of
mission-compiler, so no dedicated builder is required. What IS missing from tests:

1. **Flag-order stability** — a full golden-string assertion on `render()` for both builders
   (proves the exact argv order is deterministic and stable).
2. **Quoting round-trip** — tokens containing whitespace are double-quoted; embedded double
   quotes are escaped (`"` -> `\"`). Only the whitespace case is tested today.
3. **`bounds_for_spoke` re-export** — `spoke_cmd.bounds_for_spoke(spoke)` delegates to
   `bounds.bounds_for`; it is currently untested and raises for unknown spokes.

## What to do (tests only — no source change)

Add tests to `tests/test_spoke_cmd.py`:

1. **Golden render, setup.** Build a setup command with fixed inputs and assert the exact
   rendered string (full argv order: python3 <spoke> --goal ... --name ... --project-dir ...
   --ai-dir ... --cycles ... [--repo ...] [--seed ...]).
2. **Golden render, cycle.** Same for `build_cycle_command` with briefing + trajectories set.
3. **Quoting escapes embedded double quotes.** A token like `a "quoted" goal` renders as
   `"a \"quoted\" goal"` (escaped), and a whitespace-free token is left bare.
4. **`bounds_for_spoke` delegates.** `bounds_for_spoke("cycle-implementation")` returns the same
   `Bounds` object values as `bounds.bounds_for("cycle-implementation")`; unknown spoke raises
   `ValueError`.

## Acceptance tests (new, must pass)

- `test_setup_command_golden_render`
- `test_cycle_command_golden_render`
- `test_render_escapes_embedded_double_quotes`
- `test_bounds_for_spoke_delegates_and_raises`

## Constraints

- No change to any builder signature or the `SpokeCommand` dataclass (public API frozen).
- stdlib only. Golden strings must be stable across runs (no timestamps/randomness).
