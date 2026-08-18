# TICKET-001: Finalize setup artifacts (runner prompt + Build Order)

**Status:** OPEN
**Priority:** High
**Cycle:** 1

## Context

The mission-compiler package is fully implemented and passing (41 tests, ruff clean, mypy clean).
The CLI works end-to-end: `python3 -m mission_compiler compose <mission>` generates all 5 sections
(GOAL with v3 deltas, inner spoke command, bounds table, seed scaffold, launch script).

However, the setup spoke hit `max_steps_reached` before writing the full runner prompt and
Build Order into the gate log. The runner prompt at `ai/mission-compiler-cycle-runner-prompt.md`
is a stub (header only).

## What to do

1. Write the full runner prompt (6-phase framework + rules + Build Order table) for mission-compiler build cycles.
   - Gate: `pytest tests/ -x -q` + `ruff check mission_compiler/` + `mypy mission_compiler/ --ignore-missing-imports`
   - 12 cycles planned
   - V3 deltas inline (Phase 0 pre-flight, Phase 5 issue sweep, bounded POLISH class, INCOMPLETE log note)

2. Write the Build Order table in the gate log (`ai/cycle-001-mission-compiler-gate.md`). Suggested phases:
   | Phase | Cycles | Target |
   |---|---|---|
   | Foundations: GOAL + spoke command builders | 1-2 | goal.py, spoke_cmd.py, bounds.py (done — verify coverage) |
   | Launch script generation | 3-4 | launch.py heredoc embedding, nohup wrapper, bash -n self-test |
   | Seed scaffold planner | 5-6 | seed_scaffold.py: classify paths as reference/create/copy |
   | CLI + compose orchestration | 7-8 | cli.py, compose.py: wire all sections, --write flag, script output |
   | E2E + hardening | 9-10 | Integration test: compose real project (fourseer/fleet), validate bash -n on output |
   | Docs + release | 11-12 | README, examples, CI green, tag v0.1.0 |

3. Commit the completed artifacts. The next build cycle can then proceed with the full runner prompt in place.

## Verification

- `bash -n` on a generated launch script passes
- Runner prompt contains all 4 v3 delta descriptions
- Build Order table is in the gate log under "## Build Order"
