# TICKET-011 — Seed scaffold planner: general classify_seed_paths (reference/create/copy)

## Capability
The module mission_compiler/seed_scaffold.py currently only exposes a FIXED builder,
build_seed_scaffold(seed, project_dir, name, ai_dir) -> SeedScaffold, which emits a
hard-coded set of reference + create items (no copy). This ticket adds the GENERAL
classify capability: given an arbitrary seed spec — a mapping of source -> dest, or a list
of paths with a base dir — classify every entry by action and emit a deterministic plan.

## New public API (additive; no existing signature changes)
Add to mission_compiler/seed_scaffold.py:

1. A frozen dataclass SeedEntry describing one classified path:
   - action: str            # "reference" | "create" | "copy"
   - path: str              # the destination / canonical path for this entry
   - source: str | None     # resolved source, set ONLY for action == "copy"; None otherwise
   - note: str              # human note; for "create" this is the intended content/placeholder

2. A function:
       def classify_seed_paths(spec, *, base_dir="") -> list[SeedEntry]:
   where spec may be a MAPPING {source: dest} or a LIST of paths.
   Classification rules (deterministic):
     * A mapping entry whose dest equals its source (or whose source is empty/None) is a
       REFERENCE: record the path, no copy.
     * A mapping entry with a distinct non-empty source and dest is a COPY: resolve source
       against base_dir (if relative) and record both resolved source + dest.
     * A list entry (no explicit source) is a CREATE: the path is created in place; the note
       carries an intended content/placeholder derived deterministically from the path by
       extension (.py -> "python module", .md -> "markdown doc", else "file").
   base_dir, when non-empty, prefixes relative paths (both source and dest) with a single "/"
   separator; absolute paths are left untouched.

3. A render helper for byte-determinism assertions:
       def render_seed_entries(entries) -> str:
   Renders one line per entry in input order, e.g.
     [copy] <dest> <- <source>
     [create] <path> - <note>
     [reference] <path>

## Constraints
- stdlib only (dataclasses, pathlib). No new dependencies.
- Deterministic: same input -> byte-identical output. No timestamps/randomness.
- Do NOT change any existing public signature (build_seed_scaffold, SeedScaffold,
  ScaffoldItem untouched). New symbols are additive.

## Acceptance tests (tests/test_seed_scaffold.py)
- Mapping with a copy entry -> action "copy", source resolved, dest recorded.
- Mapping with source == dest -> action "reference".
- List of paths -> all "create" with extension-derived notes.
- base_dir prefixes relative paths; absolute paths untouched.
- render_seed_entries output is byte-deterministic (two calls equal).
