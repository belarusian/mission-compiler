# TICKET-027 — `--seed-spec` JSON list-form round-trip (POLISH, bounded post-plan)

## Capability
The `--seed-spec` CLI flag accepts "a JSON mapping {source: dest} or a
comma-separated path list" (per the README and the `parse_seed_spec` docstring).
But `parse_seed_spec` routes any value whose first char is `{` **or** `[` into
`json.loads`, then rejects anything that is not a dict:

    if stripped.startswith("{") or stripped.startswith("["):
        data = json.loads(stried)
        if not isinstance(data, dict):
            raise ValueError("seed-spec JSON must be an object {source: dest}")

So a **JSON list** like `'["a.py", "b.md"]'` — which is the natural JSON spelling
of the same path-list that `classify_seed_paths` already accepts as a Python
`list[str]`, and that the comma-list form (`"a.py, b.md"`) already supports —
raises `ValueError` instead of round-tripping into the scaffold. The `[`-prefix
branch is therefore dead/misleading: it advertises JSON support for lists but
rejects them.

This is a bounded POLISH gap (CLI passthrough / doc-code consistency): make the
JSON list form behave exactly like the comma-list form, so the documented
"comma-separated path list" capability is reachable in both spellings and the
`[... ]` branch is no longer a trap.

## File paths + signatures
- `mission_compiler/cli.py` — `parse_seed_spec(value: str) -> dict[str, str] | list[str]`.
  Additive change only: when the JSON value parses to a **list**, validate that
  every element is a string and return it as `list[str]` (mirroring the
  comma-list path: strip each element, drop empties). Keep the existing dict
  behavior byte-identical. Keep the non-object/non-string error for genuinely
  invalid JSON (e.g. a bare number, or a list containing a non-string).
- `tests/test_cli.py` — new tests (additive only; do not modify existing tests).

## Behavior contract (deterministic)
- `parse_seed_spec('["a.py", "b.md"]')` -> `["a.py", "b.md"]`
- `parse_seed_spec('  [ "x.py" , "y.md" ]  ')` -> `["x.py", "y.md"]` (strip + drop empties)
- `parse_seed_spec('[]')` -> `[]`
- `parse_seed_spec('[1, 2]')` -> raises `ValueError` (non-string element)
- `parse_seed_spec('{"a": "b"}')` -> unchanged dict behavior
- The comma-list form is unchanged: `parse_seed_spec("a.py, b.md")` -> `["a.py", "b.md"]`

## Acceptance tests (new, in tests/test_cli.py)
1. `test_parse_seed_spec_json_list_form`: `'["a.py", "b.md"]'` -> `["a.py", "b.md"]`.
2. `test_parse_seed_spec_json_list_strips_and_drops_empty`: a JSON list with
   whitespace-padded and empty-string elements round-trips to the cleaned list.
3. `test_parse_seed_spec_json_empty_list`: `'[]'` -> `[]`.
4. `test_parse_seed_spec_json_list_non_string_raises`: `'[1, 2]'` raises ValueError.
5. `test_cli_seed_spec_json_list_reflects_create_entries(capsys)`: running the CLI
   with `--seed-spec '["pkg/mod.py", "docs/README.md"]'` renders `[4] SEED SCAFFOLD`
   with the two `[create]` entries (byte-deterministic across two runs).

## Constraints
- stdlib only; no new dependencies.
- Do NOT change any existing public signature or the dict/comma-list behavior.
- Deterministic: same input -> byte-identical output.
