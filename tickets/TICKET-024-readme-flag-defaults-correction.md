# TICKET-024 — README flag-table default corrections

## Class
POLISH (docs/README refinement). Bounded post-plan; no source change.

## Problem
The top-level `README.md` "CLI flags (compose)" table lists **wrong defaults**
for four flags. The actual defaults live in `mission_compiler/cli.py`
(`build_parser`) and are concrete, not the placeholders the README shows:

| Flag | README says | Actual default (cli.py) |
|---|---|---|
| `--project-dir DIR` | `cwd` | `/home/sasha/AI/mission-compiler/proj` |
| `--ai-dir DIR` | `<project-dir>/../ai` | `/home/sasha/AI/mission-compiler/ai` |
| `--cycle N` | `none` | `1` |
| `--run-py PATH` | `auto` | `/home/sasha/Research/four/run.py` |

These four rows are factually incorrect and mislead users about what a plain
`compose` produces. The other rows (`--cycles 12`, `--repo none`, `--seed none`,
`--spoke project-setup`, `--name mission-compiler`, `--script-path
<project-dir>/launch-<name>.sh`, `--write off`, `--validate off`) are correct and
must be left untouched.

## Capability
Correct the four wrong default cells in the README flag table so they match the
actual `build_parser` defaults exactly. Additive docs-only change; no source file
under `mission_compiler/` is modified.

## Files
- `README.md` (edit only the four Default cells on the `--project-dir`,
  `--ai-dir`, `--cycle`, and `--run-py` rows).

## Acceptance tests
Add a new test module `tests/test_readme_flags.py` that pins the README flag table
to the real parser defaults so this class of doc drift cannot silently return:

1. Parse `README.md` (relative to the repo root) and extract the four Default cells
   for `--project-dir`, `--ai-dir`, `--cycle`, `--run-py`.
2. Build the parser via `mission_compiler.cli.build_parser()` and parse a bare
   `["compose", "Build it."]`; assert each README cell equals the corresponding
   `args.<attr>` default (as a string).
3. Assert the four correct values are present verbatim in the README:
   `/home/sasha/AI/mission-compiler/proj`, `/home/sasha/AI/mission-compiler/ai`,
   `1`, `/home/sasha/Research/four/run.py`.

All tests must pass with `python3 -m pytest tests/ -x -q`; test count increases.
No change to any public API or signature in `mission_compiler/`.
