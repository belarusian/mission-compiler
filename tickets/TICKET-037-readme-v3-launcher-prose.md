# TICKET-037: README prose for the v3 default launcher

## Capability
Add a short "Default launcher (v3)" section to README.md that narrates the
new default launcher behavior a fresh compose (NO knobs) now emits, so the
docs are byte-consistent with the code. Pin it with a test in
tests/test_readme_flags.py that asserts the README mentions the key facts.

## What the prose must cover
1. The v3 path: `run-v3.py` is the default outer orchestrator; it adds an
   explicit LLM request timeout via `four.chat_model_v2` (env
   `FIVE_REQUEST_TIMEOUT`, default 21600s) so the client never cancels long
   inferences mid-generation.
2. The default DUAL endpoint pins: a fresh compose (no `--config`) exports
   `FIVE_BASE_URL=http://192.168.1.157:8080/v1` (fast-qwen) +
   `FIVE_LARGE_URL=http://192.168.1.161:8081/v1` (qwen) +
   `FIVE_REQUEST_TIMEOUT=21600` in the generated script.
3. The single-LLM kind: `--config single-llm-long-pass` pins
   `FIVE_BASE_URL=http://192.168.1.161:8080/v1` for both roles.
4. The proven default bounds: setup 7200/1500/25/60; cycle (dual)
   3600/3000/40/90.

## File paths
- `README.md` — add a "Default launcher (v3)" section (after the flag table,
  before the end-to-end example).
- `tests/test_readme_flags.py` — add a test asserting the README mentions
  `run-v3.py`, the dual pins (`.157:8080`, `.161:8081`), and the proven
  bounds values.

## Acceptance tests
- `test_readme_mentions_v3_launcher`: README contains "run-v3.py" and
  "FIVE_REQUEST_TIMEOUT".
- `test_readme_mentions_dual_pins`: README contains "192.168.1.157:8080"
  and "192.168.1.161:8081".
- `test_readme_mentions_single_llm_pin`: README contains
  "192.168.1.161:8080" (the single-LLM pin).
- `test_readme_mentions_proven_bounds`: README contains "7200" and
  "3600" (the proven default bounds).

## Constraints
- Additive only: no public API change.
- stdlib only.
- Deterministic: no timestamps or randomness.
