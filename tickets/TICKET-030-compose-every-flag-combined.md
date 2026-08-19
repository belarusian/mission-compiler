# TICKET-030 — compose/CLI with EVERY flag combined end-to-end (POLISH, bounded post-plan)

## Capability
The Build Order plan is complete and Cycles 9-11 closed the major polish gaps. The
Cycle 12 "What to Build" row explicitly names one residual coverage gap: *"`compose`
with every flag combined end-to-end"*. Today no single test drives `compose(...)` (or
the CLI) with **all** of its flags at once, and in particular the two opt-in axes
added in later cycles — `--seed-spec` (TICKET-027) and `--config` (TICKET-025) — are
each tested in isolation but **never together**. A test that combines every flag is
the natural regression guard that the full composition path stays byte-deterministic
and valid-bash when all opt-ins are active simultaneously.

This is a bounded POLISH gap (test coverage of the public API). No source change:
`compose`, `build_parser`, and `main` already accept every flag; we only add tests
that exercise them in combination and pin the result.

## File paths + signatures
- `tests/test_compose.py` — new tests (additive only; do not modify existing tests).
  Drive `mission_compiler.compose.compose(...)` with **every** keyword argument set at
  once: `mission`, `cycles`, `repo`, `seed`, `seed_spec` (a mapping), `spoke`, `name`,
  `project_dir`, `ai_dir`, `cycle`, `run_py`, `config`, `validate=True`. Assert the
  full contract for BOTH spoke types.
- `tests/test_cli.py` — new tests (additive only). Drive `mission_compiler.cli.main([...])`
  with **every** CLI flag on one argv: `--cycles --repo --seed --seed-spec --spoke
  --name --project-dir --ai-dir --cycle --run-py --config --script-path --write
  --validate`. Assert rc 0, the written script passes an explicit `bash -n`, all five
  section headers print, and stdout is byte-identical across two identical invocations.

## Behavior contract (deterministic)
For `compose` with every flag set (both spokes):
- returns a `ComposedLaunch` whose `render()` contains all five section headers;
- the `[3] BOUNDS` section reflects the **selected LLM-config row** (config wins over
  spoke-based bounds), e.g. `--config single-llm-long-pass` -> "outer wall (perl alarm):
  10800s";
- the `[4] SEED SCAFFOLD` section reflects the classified `seed_spec` mapping (a
  `[copy]` line for a source->dest entry and a `[reference]`/`[create]` line for the
  other), i.e. the general classifier path, not the fixed builder;
- `validate=True` does not raise (the composed script is valid bash);
- two equal calls are byte-identical (`render()` and `launch_script`).

For the CLI with every flag set:
- `main([...])` returns 0;
- the file at `--script-path` exists and passes an explicit `bash -n`;
- all five section headers appear on stdout;
- two identical invocations produce byte-identical stdout.

## Acceptance tests (new, additive)
1. `test_compose_every_flag_combined_setup` — every kwarg set, spoke=project-setup,
   config=single-llm-long-pass, seed_spec mapping, validate=True: five headers present;
   BOUNDS shows the config row (10800s); scaffold shows a `[copy]` line for the
   source->dest entry; `validate_composed(launch)` does not raise.
2. `test_compose_every_flag_combined_cycle` — same but spoke=cycle-implementation,
   cycle=7: five headers present; BOUNDS shows the config row; scaffold reflects the
   mapping; validate green.
3. `test_compose_every_flag_combined_byte_identical` — two equal every-flag calls
   (both spokes) are byte-identical on `render()` and `launch_script`.
4. `test_cli_every_flag_combined_write_validate_bash_n` — one argv with every flag,
   `--write --validate`, a tmp script path: rc 0; file exists; explicit `bash -n`
   passes; five headers on stdout.
5. `test_cli_every_flag_combined_deterministic_stdout` — two identical every-flag
   invocations produce byte-identical stdout.

## Constraints
- Additive only: no change to any public API or signature in `mission_compiler/`.
- stdlib only (json, pathlib, argparse, subprocess, tempfile, os, dataclasses).
- Deterministic: same input -> byte-identical output; no timestamps/randomness.
