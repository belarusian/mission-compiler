# TICKET-014 — CLI passthrough for the seed spec (`--seed-spec`)

## Capability
Accept an optional `--seed-spec` flag on the `compose` subcommand carrying either a
JSON mapping `{source: dest}` or a comma-separated path list, parse it into a
`dict[str,str]` / `list[str]`, and pass it through to `compose(seed_spec=...)`.
The composed launch's scaffold plan must reflect the classified entries.

- New flag on the `compose` subparser: `--seed-spec` (default None).
- A small pure parser `parse_seed_spec(value: str) -> dict[str,str] | list[str]`:
  - value starting with `{` -> `json.loads` (must be a mapping of str->str);
  - otherwise -> split on commas, strip whitespace, drop empties -> list.
- Default behavior (no flag) is byte-identical to before.

## Files / signatures
- `mission_compiler/cli.py`:
  - `build_parser()`: add `comp.add_argument("--seed-spec", default=None, ...)`.
  - New pure helper `parse_seed_spec(value: str) -> dict[str,str] | list[str]`.
  - `main(...)`: pass `seed_spec=parse_seed_spec(args.seed_spec)` when the flag is set.
- No existing public signature changed.

## Acceptance tests (tests/test_cli.py)
1. `--seed-spec` absent -> `args.seed_spec is None`; compose output unchanged.
2. `parse_seed_spec('{"a": "b"}')` -> mapping; `parse_seed_spec("x.py, y.md")` -> list.
3. CLI with a JSON mapping spec -> printed scaffold contains the classified copy/reference lines.
4. CLI with a comma-separated list spec -> printed scaffold contains create lines.
5. Determinism: same flag value twice -> identical output.
