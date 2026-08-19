# TICKET-028 — `SpokeCommand._quote` whitespace edge coverage (POLISH, bounded post-plan)

## Capability
`_quote(token)` in `mission_compiler/spoke_cmd.py` is the shell-quoting primitive
behind every rendered inner spoke command. Its rule: quote a token only when it
contains **any** whitespace character; escape embedded double quotes. The existing
tests cover (a) a plain space-separated goal, and (b) an embedded-double-quote
goal. They do NOT pin the full whitespace-character matrix or the empty-token /
no-whitespace cases, so a regression in any of those branches would be silent.

This is a bounded POLISH coverage gap: add tests that pin `_quote`'s exact
behavior across the whitespace edge cases (tab, leading space, trailing space,
empty token, no-whitespace token) and confirm `render()` composes them correctly.
No source change — additive tests only.

## File paths + signatures
- `mission_compiler/spoke_cmd.py` — `_quote(token: str) -> str` (unchanged).
- `tests/test_spoke_cmd.py` — new tests (additive only; do not modify existing tests).

## Behavior contract (deterministic, pure function of input)
- `_quote('a\tb')` -> `'"a\tb"'` (tab is whitespace -> quoted)
- `_quote(' x')`  -> `'" x"'`   (leading space -> quoted)
- `_quote('x ')`  -> `'"x "'`   (trailing space -> quoted)
- `_quote('')`    -> `''`       (empty token stays empty, never quoted)
- `_quote('abc')` -> `'abc'`    (no whitespace -> bare)
- A token with an embedded double quote but NO whitespace is NOT quoted and the
  quote is NOT escaped (the escape only happens inside a quoted token).

## Acceptance tests (new, in tests/test_spoke_cmd.py)
1. `test_quote_tab_is_quoted`: `_quote('a\tb') == '"a\tb"'`.
2. `test_quote_leading_and_trailing_space_are_quoted`: `_quote(' x') == '" x"'`
   and `_quote('x ') == '"x "'`.
3. `test_quote_empty_token_is_empty`: `_quote('') == ''`.
4. `test_quote_no_whitespace_stays_bare`: `_quote('abc') == 'abc'`.
5. `test_quote_embedded_double_without_whitespace_not_escaped`: a token like
   `'a"b'` (embedded quote, no whitespace) renders bare as `a"b` (no wrapping,
   no backslash).
6. `test_render_composes_quoted_and_bare_tokens`: build a setup command whose goal
   has a tab and whose name has no whitespace; assert the rendered line quotes the
   goal token and leaves the name token bare.

## Constraints
- stdlib only; no new dependencies.
- Do NOT change any existing public signature or `_quote` behavior.
- Deterministic: same input -> byte-identical output.
