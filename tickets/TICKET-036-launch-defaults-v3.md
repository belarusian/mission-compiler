# TICKET-036 — launch defaults v3: run-v3.py + dual-LLM launcher default + endpoint pins + footer (issue #46, semantic update 2026-08-27)

## Capability
The compiler is unaware of runner versions that shipped after the ticket was written.
The current standard for new launches is the v3 path: `run.py`/`run-v2.py` are FROZEN
legacy (JUNIOR-v2 §2 + hard rule 7). A fresh compose (NO knobs) must emit a v3-valid
launcher: run-v3.py + dual endpoint pins + proven bounds + v4 inner spoke.

## Required
1. `launch.py` `DEFAULT_RUN_PY` -> `/home/sasha/Research/four/run-v3.py` (outer with
   explicit LLM request timeout via four.chat_model_v2; scar: sentry cycle 8 client-cancel).
   `compose.py` `DEFAULT_RUN_PY` and the CLI `--run-py` default follow (README table +
   test_readme_flags pins updated to the new value).
2. The generated script exports the endpoint config for the composed kind:
   - DEFAULT = dual: `FIVE_BASE_URL=http://192.168.1.157:8080/v1`, `FIVE_MODEL=fast-qwen`,
     `FIVE_LARGE_URL=http://192.168.1.161:8081/v1`, `FIVE_LARGE_MODEL=qwen`,
     `FIVE_REQUEST_TIMEOUT=21600` (proven shape: ~/AI/sentry/run-cycles-v3.sh).
   - single-LLM kind (selectable via the existing `--config` axis, e.g.
     `single-llm-long-pass`): pin `.161:8080` for BOTH roles
     (`FIVE_BASE_URL=http://192.168.1.161:8080/v1`, `FIVE_MODEL=qwen`,
     `FIVE_LARGE_URL=http://192.168.1.161:8080/v1`, `FIVE_LARGE_MODEL=qwen`,
     `FIVE_REQUEST_TIMEOUT=21600`).
   Pins are exported in the script after `set -uo pipefail`, before the heredocs.
3. The inner spoke command follows the kind: dual -> `cycle-implementation-v4.py`,
   single -> `cycle-implementation-v3.py`. `spoke_cmd.py` learns the v3/v4 lineage:
   new `DEFAULT_CYCLE_SPOKE_V4` constant + additive kw-only `config_kind: str = "dual-llm"`
   on `build_cycle_command` (default renders byte-identical to today's v3 path).
   The setup spoke is unaffected by kind.
4. Cosmetic (original report): the trailing "Launch with:" footer must honor
   `--script-path`, not just the default. Additive kw-only `script_path: str | None = None`
   on `compose()`; when given, `nohup_command` (and thus the footer) uses it; when None,
   byte-identical to today. CLI passes `script_path=args.script_path`.

## Kind routing (compose)
- `config is None` -> kind "dual-llm" (default launcher kind is dual).
- `config == "single-llm-long-pass"` -> kind "single-llm".
- any other explicit config -> kind "dual-llm".
Bounds follow the same axis (TICKET-035) so [3] BOUNDS and [5] pins never disagree.

## Acceptance tests
- Fresh compose (NO knobs, project-setup): script contains `run-v3.py`, all five dual
  exports, `FIVE_REQUEST_TIMEOUT=21600`; passes `bash -n`; deterministic byte-identical.
- Fresh compose (NO knobs, cycle-implementation): inner spoke path ends
  `cycle-implementation-v4.py`; bounds 3600/3000/40/90.
- compose(cycle-implementation, config="single-llm-long-pass"): inner spoke path ends
  `cycle-implementation-v3.py`; script exports the single pins (.161:8080 both roles);
  bounds 10800 row.
- `build_cycle_command(...)` without config_kind -> byte-identical v3 argv (regression).
- `build_launch_script(...)` without config_kind -> script byte-identical to today
  (regression: no export block when kind not passed? NO — default kind dual-llm adds the
  block; instead pin: explicit config_kind="dual-llm" == default output).
- Footer: compose(script_path="/x/y.sh") -> nohup_command == "nohup bash /x/y.sh > /x/y.sh.out 2>&1 &";
  compose() without -> default path footer (regression).
- CLI: `--script-path /tmp/... --write` footer shows the given path.
- README `--run-py` default cell == run-v3.py; test_readme_flags updated.

## Files
- `mission_compiler/launch.py` (DEFAULT_RUN_PY, endpoint pins, build_launch_script kw-only config_kind)
- `mission_compiler/spoke_cmd.py` (DEFAULT_CYCLE_SPOKE_V4, build_cycle_command kw-only config_kind)
- `mission_compiler/compose.py` (DEFAULT_RUN_PY, kind routing, script_path kw-only)
- `mission_compiler/cli.py` (--run-py default, script_path threading)
- `README.md`, `tests/test_launch.py`, `tests/test_spoke_cmd.py`, `tests/test_compose.py`,
  `tests/test_cli.py`, `tests/test_readme_flags.py`
