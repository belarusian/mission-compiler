# TICKET-018 — E2E integration test: compose a real four project end-to-end

## Capability
Add `tests/test_e2e_compose.py` (new file) that composes a REAL four project
end-to-end through the public `compose(...)` API and asserts the full contract.
This is the "E2E + hardening" Build Order row (cycles 9-10). Additive tests only;
no behavior change to any existing module (`mission_compiler/compose.py` is
read-only here).

## Target file
- `tests/test_e2e_compose.py` (new)

## What to build
Compose a realistic project, e.g. name=`fourseer`, repo=`belarusian/fourseer`,
a seed pointing at an existing reference dir (e.g. `/home/sasha/Research/four`),
and a representative `seed_spec` (a mapping with one copy + one reference entry).
For BOTH spoke types (`project-setup` and `cycle-implementation`) assert:

1. The full rendered launch has all five section headers:
   `[1] GOAL`, `[2] INNER SPOKE COMMAND`, `[3] BOUNDS`, `[4] SEED SCAFFOLD`,
   `[5] NOHUP LAUNCH SCRIPT`.
2. `validate_composed(launch)` returns None (i.e. `bash -n` is green on the
   composed script) — no raise.
3. Two equal calls are byte-identical: `render()` and `launch_script` compare
   equal across two independent `compose(...)` invocations with identical args.
4. The scaffold section reflects the classified seed_spec (a `[copy]` line for
   the mapping copy entry) rather than the fixed builder.
5. The GOAL section carries the project name and repo (`Project: fourseer`,
   `GitHub repo: belarusian/fourseer`).

## Acceptance tests
- `test_e2e_setup_real_project_five_sections` — all five headers present.
- `test_e2e_setup_real_project_validate_composed_green` — no raise, returns None.
- `test_e2e_cycle_real_project_validate_composed_green` — cycle spoke, no raise.
- `test_e2e_real_project_byte_identical_across_calls` — render + launch_script equal.
- `test_e2e_real_project_scaffold_reflects_seed_spec` — `[copy]` line present.
- `test_e2e_real_project_goal_carries_name_and_repo` — name + repo in GOAL.

## Constraints
- stdlib only; no new dependencies.
- No change to any existing module's public API/signature.
- Deterministic: same input -> byte-identical output.
