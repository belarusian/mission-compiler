# TICKET-023: Release metadata verification + CI green on main (v0.1.0)

## Capability
Ensure the package is importable/installable as documented, that the `python3 -m
mission_compiler` entry point works, and that the CI gate (pytest + ruff + mypy)
is green on main. Prepare a v0.1.0 tag description. Do NOT cut the tag unless the
row explicitly requires it — the row says "do NOT cut the tag unless the row
explicitly requires it", so this cycle only PREPARES the tag description and
verifies metadata; no `git tag` is created. Additive only.

## Files
- `tests/test_release_metadata.py` (NEW) — pins release metadata invariants.
- `README.md` (from TICKET-021) — must state the version (v0.1.0).

## What to verify / pin
1. **Entry point**: `python3 -m mission_compiler compose <mission>` runs and exits 0
   (covered by TICKET-022 subprocess tests; re-assert here that `__main__.py` is the
   module entry point).
2. **Version consistency**: `mission_compiler.__version__ == "0.1.0"` AND
   `pyproject.toml` `[project] version == "0.1.0"` (parse pyproject with stdlib
   `tomllib` if available, else a lightweight read) — they must agree.
3. **No dependencies**: `pyproject.toml` `[project] dependencies == []` (stdlib-only
   invariant).
4. **CI gate green on main**: the three commands are green:
   - `python3 -m pytest tests/ -x -q`
   - `python3 -m ruff check mission_compiler/`
   - `python3 -m mypy mission_compiler/ --ignore-missing-imports`
5. **v0.1.0 tag description** (prepared, not cut): a short release-note string
   documenting what v0.1.0 ships (the five-section composer, all CLI flags, the
   gate). Store it as a module-level constant in test_release_metadata.py and assert
   it is non-empty and mentions "v0.1.0".

## Acceptance tests
- `tests/test_release_metadata.py` passes with `python3 -m pytest tests/ -x -q`.
- Version in `__init__.py` and `pyproject.toml` agree (both "0.1.0").
- `dependencies == []` is asserted.
- No `git tag` is created this cycle (verified by `git tag --list` unchanged).

## Constraints
- Additive only; no change to `mission_compiler/` public API or signatures.
- stdlib only. Do NOT cut the v0.1.0 tag (row does not require it).
