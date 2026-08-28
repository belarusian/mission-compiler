# TICKET-034 — compose --write must create missing parent dirs of --script-path

## Capability
`python3 -m mission_compiler compose <mission> --script-path <new/dir/launch.sh> --write`
fails with EXIT=2 "could not write launch script: [Errno 2] No such file or directory"
when the parent directory of `--script-path` does not exist. A composed launch for a
NEW project always targets a dir that does not exist yet — the common case, not an edge.

## Root cause
`mission_compiler/cli.py::main` write path uses a raw `open(script_path, "w")` and
never creates parent directories. The helper `mission_compiler/launch.py::write_launch_script`
already does `target.parent.mkdir(parents=True, exist_ok=True)` and returns the nohup
command — the CLI just does not use it.

## Fix (additive)
In `cli.py::main`, replace the raw open/write block with a call to
`write_launch_script(launch.launch_script, script_path)` (keep the `validate_launch_script`
fail-fast call before it, keep the same error message shape and exit code 2 on OSError).

## Acceptance tests
- CLI: `--write --script-path <tmp>/a/b/c/launch.sh` (tmp fresh) -> rc 0, file exists at
  the nested path, content == composed launch_script, "[written]" line printed.
- CLI: `--write` with default script path (no --script-path) still works (regression).
- No change to print-only behavior (no --write): no file created.

## Files
- `mission_compiler/cli.py` (write block in main)
- `tests/test_cli.py` (new tests)
