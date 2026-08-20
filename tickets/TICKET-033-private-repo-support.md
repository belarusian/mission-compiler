# TICKET-033 — private repo support: --private flag end-to-end (additive)

## Capability
The compose path can only create PUBLIC GitHub repos: `cli.py` has no `--private`,
`build_setup_command` can never emit one, and the GOAL text cannot carry it. For
personal-data projects (e.g. generated resumes) that is a footgun: composing a launch
saying "push to GitHub" risks a public repo. Add `--private` end-to-end, additive only:

1. `mission_compiler/cli.py` — `comp.add_argument("--private", action="store_true",
   help="Create the GitHub repo private (default: public).")` next to the `--repo`
   argument; pass `private=args.private` into `compose()`.
2. `mission_compiler/compose.py` — additive kw-only `private: bool = False` on the
   `compose(...)` signature (placed beside `repo`); thread it to `compose_goal(...)`
   and to the setup-command builder. No other behavior change.
3. `mission_compiler/spoke_cmd.py::build_setup_command` — additive kw-only
   `private: bool = False` (beside `repo`); when True, append `["--private"]` to argv
   immediately after the `["--repo", repo]` addition (before `--seed`). When False:
   argv byte-identical to today.
4. `mission_compiler/goal.py::compose_goal` — additive kw-only `private: bool = False`
   (beside `repo`); the repo line becomes `GitHub repo: {repo} (private)` when BOTH
   `repo` and `private` are set; `GitHub repo: {repo}` when only `repo`; no repo line
   at all when `repo` is None (regardless of `private`).

## Behavior contract (deterministic)
- `compose(...)` without `private` produces byte-identical output to today in every
  section (existing tests pin this; add one explicit regression pin).
- `compose(..., repo="o/n", private=True)` → setup argv contains `--repo o/n --private`
  as adjacent tokens in that order, and GOAL text contains exactly
  `GitHub repo: o/n (private)`.
- Cycle commands (`build_cycle_command`) are untouched by this ticket.

## Acceptance tests (new, additive)
1. `test_setup_command_private` — `build_setup_command(repo="o/n", private=True, ...)`.argv:
   `"--private"` present immediately after `"o/n"`; with `private=False` the argv equals
   today's exact list (no `"--private"` anywhere).
2. `test_goal_repo_private_line` — `compose_goal(repo="o/n", private=True)` contains
   `GitHub repo: o/n (private)`; `private=False` contains `GitHub repo: o/n` and NOT
   `(private)`; `repo=None, private=True` contains no `GitHub repo:` line.
3. `test_cli_private_roundtrip` — CLI `compose "m" --repo o/n --private` (in-process
   argv) yields a launch whose setup command argv carries `--private` adjacent to the
   repo; without `--private` it does not.
4. `test_compose_without_private_byte_identical` — full `compose()` run without
   `--private`: no `"--private"` in any emitted argv and no `(private)` in the GOAL
   text; output identical to a pre-feature reference (assert via the exact expected
   substrings the existing tests already pin).

## Constraints
- Additive only: no change to any existing public API or signature (kw-only params
  with defaults only).
- stdlib only; deterministic (same input -> byte-identical output; no timestamps).
- Gate: `python3 -m pytest tests/ -x -q`, `python3 -m ruff check mission_compiler/`,
  `python3 -m mypy mission_compiler/ --ignore-missing-imports` all green; test count
  increases monotonically (>= 205 + new).
