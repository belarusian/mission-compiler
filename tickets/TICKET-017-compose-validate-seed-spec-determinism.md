# TICKET-017 — compose hardening: `validate=True` + non-None `seed_spec` passes bash -n; five sections byte-deterministic with both `seed` and `seed_spec`

## Capability
Orchestration hardening tests for `compose`. Pin two invariants that the CLI
`--validate` flag (TICKET-016) depends on:

1. `compose(..., validate=True)` with a non-None `seed_spec` (both a mapping and
   a list form) still passes `bash -n` — i.e. supplying an explicit seed spec does
   not break the generated launch script's syntax, and validation accepts it.
2. When BOTH `seed` and `seed_spec` are supplied together, the composed launch's
   five rendered sections stay byte-deterministic across equal calls (the scaffold
   section reflects the classified spec while the other four sections are stable).

## Additive-only constraints
- Tests only. No behavior change to any existing module; no signature changes.
- stdlib only.

## File paths + signatures
- `tests/test_compose.py`: new tests (see acceptance). Reuse the existing
  `compose` import and helpers.

## Acceptance tests
1. `compose("Build it.", seed="/s", seed_spec={"/s/a.py": "/d/a.py"}, validate=True)`
   returns without raising (bash -n passes) and its `[4] SEED SCAFFOLD` section
   contains the classified copy line.
2. Same with a list spec `seed_spec=["pkg/mod.py"]`, `validate=True`: no raise,
   create line present.
3. Both `seed` and `seed_spec` supplied: two equal calls produce byte-identical
   `render()` output (all five sections).
4. The scaffold section with both seed+seed_spec reflects the classified entries
   (not the fixed builder) while `[1] GOAL`, `[2] INNER SPOKE COMMAND`,
   `[3] BOUNDS` are present and stable.

## Determinism
Same input -> byte-identical output. No timestamps or randomness.
