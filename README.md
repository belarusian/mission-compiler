# mission-compiler

A deterministic, **stdlib-only** CLI that composes a four pipeline launch from a
free-text mission. You give it a mission; it renders a complete, ready-to-run
launch: the goal, the inner spoke command, the proven bounds, a seed-scaffold
plan, and a nohup-ready bash script validated with bash -n.

**Deterministic:** the same input always produces byte-identical output. No
timestamps, no randomness.

## What it does

mission-compiler compose "<mission>" renders a composed launch made of **five
sections, in order**:

1. [1] GOAL (v3 deltas inline) - your mission plus the standing v3 rules that
   apply every cycle (pre-flight, issue sweep, polish class, incomplete-log note).
2. [2] INNER SPOKE COMMAND - the full argv line for the inner spoke
   (project-setup or cycle-implementation).
3. [3] BOUNDS (proven table) - outer wall / inner-seconds / outer-steps /
   inner max-steps, chosen by spoke and LLM config.
4. [4] SEED SCAFFOLD - a reference/create/copy plan for the seed path, built
   from the general classifier (or an explicit --seed-spec).
5. [5] NOHUP LAUNCH SCRIPT - a ready-to-run bash script, validated with
   bash -n when --validate is set.

## Install / entry points

    pip install -e .          # installs the mission-compiler command
    # or run it as a module (no install needed):
    python3 -m mission_compiler compose "<mission>"

Both entry points are equivalent.

## CLI flags (compose)

| Flag | Meaning | Default |
|---|---|---|
| mission (positional) | Free-text mission description. | required |
| --cycles N | Planned cycle count. | 12 |
| --repo OWNER/NAME | GitHub repo owner/name. | none |
| --private | Create the GitHub repo private (with `--repo`; default public). Adds `--private` to the setup command and a `(private)` marker to the GOAL repo line. | off (public) |
| --seed PATH | Read-only reference project path. | none |
| --seed-spec SPEC | Explicit seed spec: a JSON mapping {source: dest}, a JSON list of paths ["a.py", "b.md"], or a comma-separated path list. When given, the scaffold plan is built from the general classifier instead of the fixed builder. | none |
| --spoke {project-setup,cycle-implementation} | Spoke type. | project-setup |
| --name NAME | Project / package name. | mission-compiler |
| --project-dir DIR | Project repository directory. | /home/sasha/AI/mission-compiler/proj |
| --ai-dir DIR | Directory for AI artifacts (log, runner prompt, briefing). | /home/sasha/AI/mission-compiler/ai |
| --cycle N | Cycle number (used by the cycle-implementation spoke). | 1 |
| --run-py PATH | Path to the outer orchestrator (run.py). | /home/sasha/Research/four/run.py |
| --config NAME | Select the proven-bounds row by LLM configuration instead of by spoke type (a key of `LLM_CONFIG_BOUNDS`: `2-llm-fast` / `single-llm-long-pass` / `setup`). | none (spoke-based) |
| --script-path PATH | Where to write the launch script. | <project-dir>/launch-<name>.sh |
| --write | Write the launch script to --script-path. | off (print only) |
| --validate | Validate the composed launch script with bash -n before printing/writing; fail fast (non-zero exit) if invalid. | off (byte-identical behavior) |

--write and --validate are **default-off**, so a plain compose is byte-identical to one that omits them.

## End-to-end example (copy-pasteable)

Compose the real fourseer project end-to-end, write the launch script, validate it, and print the rendered launch:

    python3 -m mission_compiler compose       "Build fourseer: a deterministic fleet supervisor."       --spoke project-setup       --name fourseer       --repo belarusian/fourseer       --seed /home/sasha/Research/four       --cycles 12       --project-dir /tmp/fourseer/proj       --ai-dir /tmp/fourseer/ai       --script-path /tmp/fourseer/proj/launch-fourseer.sh       --write       --validate

This prints all five sections: [1] GOAL (v3 deltas inline), [2] INNER SPOKE COMMAND, [3] BOUNDS (proven table), [4] SEED SCAFFOLD, and [5] NOHUP LAUNCH SCRIPT. To actually launch it in the background:

    nohup bash /tmp/fourseer/proj/launch-fourseer.sh > /tmp/fourseer/proj/launch.out 2>&1 &

## Runnable examples

Three byte-deterministic, runnable examples live under examples/:

    bash examples/compose-fourseer.sh   # composes the fourseer project
    bash examples/compose-fleet.sh      # composes the fleet project
    bash examples/compose-config.sh     # composes with --config single-llm-long-pass (LLM-bounds axis)

Each composes a real project with a representative seed + seed-spec, writes the launch script to a fixed throwaway path, runs bash -n on it, and prints the rendered launch. Output is byte-identical across runs (no timestamps/randomness).

## The gate

The CI gate must be green on main:

    python3 -m pytest tests/ -x -q
    python3 -m ruff check mission_compiler/
    python3 -m mypy mission_compiler/ --ignore-missing-imports

## Constraints

- Additive only: no change to the public API or signatures of existing modules.
- stdlib only (json, pathlib, argparse, subprocess, tempfile, os, dataclasses). No third-party dependencies at runtime.
- Deterministic: same input -> byte-identical output.
