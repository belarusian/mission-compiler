# TICKET-012 — Seed scaffold planner: determinism + edge cases for classify_seed_paths

## Capability
Pin the general classifier from TICKET-011 with determinism and boundary-case coverage.
This is tests-only (plus any tiny additive helper needed to make an edge case observable);
no behavior change to existing modules.

## Edge cases to cover (tests/test_seed_scaffold.py)
1. EMPTY spec: classify_seed_paths({}) and classify_seed_paths([]) both return [] and
   render_seed_entries([]) is a stable empty string (byte-deterministic).
2. DUPLICATE dest paths: two mapping entries resolving to the same dest must be handled with
   a DETERMINISTIC tie-break — the plan order is stable across calls and does not depend on
   dict insertion-order accidents; document + assert the chosen rule (e.g. first-seen wins,
   or last-wins) and that repeated calls are byte-identical.
3. NESTED dirs: paths containing multiple "/" segments (a/b/c/d.py) classify correctly and
   base_dir joins them with exactly one separator (no double slash).
4. PATH THAT IS BOTH A REFERENCE AND A COPY TARGET: the same path appears as a reference in
   one entry and as a copy dest in another; both entries are preserved, each labeled by its
   own action, and the rendered plan is byte-deterministic.

## Constraints
- stdlib only. Deterministic: same input -> byte-identical rendered plan string.
- Do NOT change any existing public signature. Additive tests (and at most a tiny additive
  helper) only. Test count must increase monotonically (>= 79).

## Acceptance
- python3 -m pytest tests/ -x -q green; ruff + mypy clean on mission_compiler/.
