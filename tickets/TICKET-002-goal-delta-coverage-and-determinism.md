# TICKET-002: GOAL builder — v3 delta coverage per spoke + byte-level determinism

**Status:** OPEN
**Priority:** High
**Cycle:** 1
**Module:** `mission_compiler/goal.py` (tests in `tests/test_goal.py`)

## Context

`compose_goal(mission, *, spoke, cycles, repo, seed, project_dir, ai_dir, name) -> str`
builds the GOAL text with the four v3 delta descriptions inline. The Build Order row for
cycles 1-2 says: "verify coverage + determinism ... Add missing tests, no behavior change."

Current `tests/test_goal.py` (8 tests) asserts the four deltas are present in ONE goal
(default spoke = cycle-implementation) and that `_goal() == _goal()` (same-process equality).
It does NOT prove the deltas survive for every supported spoke type, nor byte-level
determinism across separate process invocations.

## What to do (tests only — no source change)

Add tests to `tests/test_goal.py`:

1. **Per-spoke delta coverage.** For each spoke in `("project-setup", "cycle-implementation")`,
   build a goal and assert all four v3 delta markers are present:
   `"Phase 0 PRE-FLIGHT"`, `"Phase 5 ISSUE SWEEP"`,
   `"BOUNDED POST-PLAN POLISH CLASS"`, `"INCOMPLETE LOG NOTE"`.
2. **Byte-level determinism across processes.** Write the composed goal to a temp file via
   two separate `python3 -c` subprocess invocations (same fixed inputs), read both back, and
   assert the bytes are identical (`open(...,'rb').read()`). This is stronger than same-process
   equality: it proves no hidden state / ordering nondeterminism leaks into the output.
3. **Spoke field echoed.** Assert `f"Spoke: {spoke}"` appears in the goal for each spoke type.

## Acceptance tests (new, must pass)

- `test_goal_deltas_present_for_project_setup`
- `test_goal_deltas_present_for_cycle_implementation`
- `test_goal_spoke_field_echoed_per_spoke`
- `test_goal_byte_identical_across_processes`

## Constraints

- No change to `compose_goal` signature or behavior (public API frozen).
- stdlib only. Deterministic — the subprocess test must use fixed inputs, no timestamps.
