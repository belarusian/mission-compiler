# TICKET-021: Top-level README + runnable examples/ (Docs + release row)

## Capability
Write the top-level `README.md` for mission-compiler and add one or two
runnable, byte-deterministic examples under `examples/`. This is the first half
of the "Docs + release" Build Order row (cycles 11-12). Additive only: no source
change to `mission_compiler/`.

## Files
- `README.md` (NEW) — top-level project documentation.
- `examples/compose-fourseer.sh` (NEW) — runnable example composing the fourseer project.
- `examples/compose-fleet.sh` (NEW) — runnable example composing the fleet project.

## README.md must document
1. **What it is**: a deterministic CLI that composes four pipeline launches from a
   free-text mission; stdlib-only; same input -> byte-identical output.
2. **The five composed sections** (in order):
   - `[1] GOAL (v3 deltas inline)` — mission + standing v3 rules.
   - `[2] INNER SPOKE COMMAND` — full argv line for the inner spoke.
   - `[3] BOUNDS (proven table)` — outer wall / inner-seconds / outer-steps / inner max-steps.
   - `[4] SEED SCAFFOLD` — reference/create/copy plan for the seed path.
   - `[5] NOHUP LAUNCH SCRIPT` — ready-to-run `bash` script (validated with `bash -n`).
3. **All CLI flags** for the `compose` subcommand: positional `mission`,
   `--cycles`, `--repo`, `--seed`, `--seed-spec`, `--spoke`, `--name`,
   `--project-dir`, `--ai-dir`, `--cycle`, `--run-py`, `--script-path`,
   `--write`, `--validate`. Note defaults and that `--validate`/`--write` are
   default-off (byte-identical behavior).
4. **A copy-pasteable end-to-end example** that composes a real project (fourseer)
   and shows the rendered launch, plus how to run it with `nohup`.
5. **Install / entry points**: `pip install -e .` -> `mission-compiler` command, or
   `python3 -m mission_compiler`.
6. **The gate**: `pytest tests/ -x -q`, `ruff check mission_compiler/`,
   `mypy mission_compiler/ --ignore-missing-imports`.

## examples/ must be
- Runnable via `bash examples/compose-fourseer.sh` and `bash examples/compose-fleet.sh`.
- Each composes a real project (fourseer / fleet) with a representative seed + seed-spec,
  writes the launch script to a temp path, runs `bash -n` on it, and prints the rendered
  launch. Output must be byte-deterministic (no timestamps/randomness).

## Acceptance tests
- `README.md` exists and mentions all five section headers, all flags listed above,
  both entry points, and the three gate commands.
- `bash examples/compose-fourseer.sh` exits 0 and its output is byte-identical across two runs.
- `bash examples/compose-fleet.sh` exits 0 and its output is byte-identical across two runs.
- The written launch script in each example passes `bash -n`.

## Constraints
- Additive only; no change to `mission_compiler/` public API or signatures.
- stdlib only. Deterministic (no timestamps/randomness).
