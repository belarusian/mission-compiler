# TICKET-019 — Launch-script self-test hardening (additive tests)

## Capability
Add hardening tests to `tests/test_launch.py` for the launch-script self-test.
`mission_compiler/launch.py` is read-only here; this is additive tests only, no
behavior change.

## Target file
- `tests/test_launch.py` (append)

## What to build
The existing suite already covers a lot of this area; add the specific gaps the
Build Order row calls out that are NOT yet pinned:

1. `validate_launch_script` accepts the real builder output for BOTH spoke types
   using REAL bounds from `bounds_for(spoke)` (not hand-typed numbers) — assert
   it returns None (no raise). (Existing e2e tests build+write+bash -n; add a
   direct `validate_launch_script(...) is None` assertion for both spokes.)
2. `validate_launch_script` rejects a known-bad script with a `ValueError` whose
   message contains `"bash -n"` — assert via `pytest.raises(ValueError, match="bash -n")`.
3. `build_launch_script` is byte-identical across equal inputs for BOTH spoke
   types: compare `.encode("utf-8")` of two independent builds (byte-level, not
   just str equality).

## Acceptance tests
- `test_validate_accepts_real_builder_output_both_spokes` — None for setup + cycle.
- `test_validate_rejects_known_bad_script_bash_n` — ValueError match "bash -n".
- `test_build_launch_script_byte_identical_both_spokes` — encoded bytes equal.

## Constraints
- stdlib only; no new dependencies.
- No change to any existing module's public API/signature.
- Deterministic: same input -> byte-identical output.
