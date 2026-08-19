# TICKET-029 — `classify_seed_paths` base_dir resolution edge coverage (POLISH, bounded post-plan)

## Capability
`classify_seed_paths(spec, *, base_dir="")` in `mission_compiler/seed_scaffold.py`
resolves relative paths against `base_dir` via the private `_resolve` helper
(single `/` separator; absolute paths untouched; empty base_dir leaves path as-is).
The existing tests cover: trailing-slash-free base prefixing, absolute dest/source
untouched, nested single-separator. They do NOT pin a few remaining resolution
edges that a regression could slip through silently:

  * `base_dir` with a **trailing slash** (`/root/`) must still yield exactly one
    separator (no `//`).
  * the **reference-vs-copy decision** when `source == dest` but both are relative
    and a `base_dir` is present — the comparison is made on the raw strings, so it
    must still classify as reference (not copy) even though the resolved paths
    would be prefixed.
  * an empty-string `base_dir` (the default) leaves relative paths untouched for
    both mapping and list forms.

This is a bounded POLISH coverage gap: add tests pinning these edges. No source
change — additive tests only.

## File paths + signatures
- `mission_compiler/seed_scaffold.py` — `classify_seed_paths(...)` / `_resolve(...)`
  (unchanged).
- `tests/test_seed_scaffold.py` — new tests (additive only; do not modify existing tests).

## Behavior contract (deterministic, pure function of input)
- `classify_seed_paths(["a.py"], base_dir="/root/")` -> path `/root/a.py` (single sep).
- `classify_seed_paths({"rel.md": "rel.md"}, base_dir="/root")` -> a single
  **reference** entry with path `/root/rel.md`, source None (source==dest on raw
  strings, so reference even though the resolved dest is prefixed).
- `classify_seed_paths(["a.py"], base_dir="")` -> path `a.py` (untouched).
- `classify_seed_paths({"s.py": "d.py"}, base_dir="")` -> copy, source `s.py`,
  path `d.py` (both untouched when base_dir empty).

## Acceptance tests (new, in tests/test_seed_scaffold.py)
1. `test_classify_base_dir_trailing_slash_single_separator`: list form with
   `base_dir="/root/"` yields `/root/a.py` and no `//`.
2. `test_classify_relative_source_equals_dest_is_reference_with_base_dir`: mapping
   `{"rel.md": "rel.md"}` with `base_dir="/root"` is a reference entry, path
   `/root/rel.md`, source None.
3. `test_classify_empty_base_dir_leaves_list_paths_untouched`: list form with the
   default `base_dir=""` leaves paths as given.
4. `test_classify_empty_base_dir_mapping_source_dest_untouched`: mapping form with
   `base_dir=""` keeps source and dest exactly as given (copy entry).
5. `test_classify_base_dir_edges_byte_deterministic`: the above specs render
   byte-identically across two independent calls.

## Constraints
- stdlib only; no new dependencies.
- Do NOT change any existing public signature or `_resolve`/`classify_seed_paths` behavior.
- Deterministic: same input -> byte-identical output.
