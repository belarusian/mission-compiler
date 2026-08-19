# TICKET-015 — Remaining determinism/edge coverage for the seed scaffold planner

## Capability
Close the remaining edge-coverage gaps in `classify_seed_paths` / `render_seed_entries`.
Tests only; no behavior change to existing modules.

Cover:
- a copy whose SOURCE is absolute while `base_dir` is set (absolute source untouched,
  relative dest prefixed);
- a create path with NO extension vs a DOTFILE (`.env`) — both get the deterministic
  "file" note and render correctly;
- a mixed mapping+list composition rendered byte-identically across calls.

## Files / signatures
- `tests/test_seed_scaffold.py`: additive tests only. No module changes.

## Acceptance tests
1. absolute source + base_dir: source stays absolute, dest gets the single-separator prefix.
2. create with no extension -> note "file"; dotfile `.env` -> note "file" (no ext match).
3. mixed mapping+list composition rendered byte-identically across two calls.
