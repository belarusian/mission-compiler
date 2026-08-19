# TICKET-020 — CLI flag-matrix hardening (additive tests)

## Capability
Add hardening tests to `tests/test_cli.py` for the full flag matrix and path
override flow-through. `mission_compiler/cli.py` is read-only here; additive
tests only, no behavior change (default behavior byte-identical).

## Target file
- `tests/test_cli.py` (append)

## What to build
1. Full flag matrix: assert that
   `compose <mission> --spoke cycle-implementation --cycle N --validate --write`
   produces a valid, deterministic launch — rc 0, the written script passes
   `bash -n`, and two identical invocations yield byte-identical stdout.
2. Path override flow-through: assert that `--name`, `--project-dir`, and
   `--ai-dir` overrides flow through to ALL FIVE sections of the rendered output
   (GOAL carries name/project dir/ai dir; inner command + bounds + scaffold +
   launch script all reference the overridden paths). Use a tmp_path for
   project-dir so no real files are touched, and assert the overridden values
   appear in each section.

## Acceptance tests
- `test_cli_flag_matrix_cycle_validate_write_valid` — rc 0 + bash -n green on written script.
- `test_cli_flag_matrix_deterministic_stdout` — two identical invocations byte-equal.
- `test_cli_name_override_flows_through_all_sections` — name in all five sections.
- `test_cli_project_dir_and_ai_dir_flow_through_all_sections` — both paths in sections.

## Constraints
- stdlib only; no new dependencies.
- No change to any existing module's public API/signature.
- Deterministic: same input -> byte-identical output.
