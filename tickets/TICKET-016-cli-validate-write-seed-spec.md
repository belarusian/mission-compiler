# TICKET-016 — CLI: additive `--validate` flag + end-to-end `--write`/`--script-path` with `--seed-spec`

## Capability
Complete the "CLI + compose orchestration" row in the CLI. Add an additive,
default-off `--validate` flag to the `compose` subcommand that runs
`validate_composed(launch)` on the composed launch before printing/writing, so a
launch whose script fails `bash -n` fails fast with a non-zero exit code and a
clear message instead of silently emitting a broken script.

Also wire the existing `--write` / `--script-path` flags end-to-end together with
the new `--seed-spec`: when all three are supplied, the written script must be the
one built from the classified seed spec, and it must pass `bash -n`. A bad
`--seed-spec` (non-object JSON) or an invalid write path must fail fast.

## Additive-only constraints
- Do NOT change any existing public signature. `main`, `build_parser`,
  `parse_seed_spec` keep their current signatures; only a new flag and a small
  private helper are added.
- Default behavior (no `--validate`) is byte-identical to before: the composed
  launch, its render, and the written script are unchanged.
- stdlib only (json, pathlib, argparse, subprocess, tempfile, os, dataclasses).

## File paths + signatures
- `mission_compiler/cli.py`:
  - `build_parser()`: add `comp.add_argument("--validate", action="store_true", help=...)`.
  - `main(argv)`: after composing, if `args.validate` is true call
    `validate_composed(launch)`; on `ValueError` print the error to stderr and
    return a non-zero exit code (e.g. 2). Import `validate_composed` from
    `.compose`. The existing `--write` path already calls
    `validate_launch_script`; keep it, but route the new pre-print validation so
    both write and print are guarded when `--validate` is set.
- `tests/test_cli.py`: new tests (see acceptance).

## Acceptance tests
1. `--validate` defaults to False (`args.validate is False`).
2. `--validate` on a valid launch returns rc 0 and prints all sections.
3. `--validate --write --script-path <tmp>` writes a script that passes `bash -n`
   (assert via `subprocess.run(["bash","-n",path])` returncode == 0).
4. `--validate --seed-spec <mapping> --write` writes the classified-spec script
   and it passes `bash -n`.
5. Bad `--seed-spec` (`'["a","b"]'`) with `--validate` fails fast: rc != 0, no
   crash traceback (ValueError caught), message mentions "object".
6. Invalid write path (non-existent dir) with `--write --validate` fails fast:
   rc != 0.
7. Default (no `--validate`) output is byte-identical to a plain compose render.

## Determinism
Same input -> byte-identical output. No timestamps or randomness.
