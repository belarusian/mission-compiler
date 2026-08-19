# TICKET-013 — Wire the general seed-path classifier into compose (opt-in `seed_spec`)

## Capability
Add an additive, opt-in way for a mission to supply an explicit seed spec so
`compose(...)` can build the scaffold plan via the general
`classify_seed_paths` planner instead of only the fixed `build_seed_scaffold`.

- New keyword-only param on `compose`: `seed_spec: dict[str, str] | list[str] | None = None`.
  - `None` (default) -> current fixed behavior, byte-identical to before.
  - a mapping `{source: dest}` or a list of paths -> the scaffold section is built
    from `classify_seed_paths(seed_spec, base_dir=project_dir)` and rendered with
    `render_seed_entries`.
- The composed launch's `[4] SEED SCAFFOLD` section must reflect the classified
  entries (reference/create/copy) when a spec is supplied.

## Files / signatures
- `mission_compiler/compose.py`:
  - `compose(..., seed_spec: dict[str, str] | list[str] | None = None)` (new kw-only param).
  - New private helper `_build_scaffold(seed, project_dir, name, ai_dir, seed_spec) -> SeedScaffold`
    that returns the fixed scaffold when `seed_spec is None`, else a scaffold whose
    `items` are derived from `classify_seed_paths`.
- No existing public signature changed.

## Acceptance tests (tests/test_compose.py)
1. `compose(..., seed_spec=None)` -> scaffold byte-identical to the fixed builder output.
2. `compose(..., seed_spec={...})` mapping -> `[4] SEED SCAFFOLD` section contains the
   classified copy/reference lines from `render_seed_entries`.
3. `compose(..., seed_spec=[...])` list -> create lines present with extension notes.
4. Determinism: two composes with the same non-None spec render byte-identically.
5. Default (no spec) is unchanged vs. an explicit `seed_spec=None`.
