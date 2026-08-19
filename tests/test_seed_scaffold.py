"""Tests for the seed scaffold plan."""

from __future__ import annotations

import dataclasses

import pytest

from mission_compiler.seed_scaffold import (
    SeedEntry,
    build_seed_scaffold,
    classify_seed_paths,
    render_seed_entries,
)


def test_scaffold_with_seed_references_it():
    s = build_seed_scaffold(
        seed="/seed", project_dir="/p", name="n", ai_dir="/a"
    )
    assert s.seed_path == "/seed"
    actions = [i.action for i in s.items]
    assert "reference" in actions
    ref = next(i for i in s.items if i.action == "reference")
    assert ref.path == "/seed"


def test_scaffold_without_seed_has_no_reference():
    s = build_seed_scaffold(seed=None, project_dir="/p", name="n", ai_dir="/a")
    assert s.seed_path is None
    assert all(i.action != "reference" for i in s.items)


def test_scaffold_creates_package_tests_and_config():
    s = build_seed_scaffold(seed=None, project_dir="/p", name="n", ai_dir="/a")
    paths = [i.path for i in s.items]
    assert "/p/n/__init__.py" in paths
    assert "/p/tests/test_smoke.py" in paths
    assert "/p/pyproject.toml" in paths


def test_scaffold_creates_ai_artifacts():
    s = build_seed_scaffold(seed=None, project_dir="/p", name="n", ai_dir="/a")
    paths = [i.path for i in s.items]
    assert "/a/cycle-001-n-gate.md" in paths
    assert "/a/n-cycle-runner-prompt.md" in paths
    assert "/a/n-cycle-1-briefing.md" in paths


def test_scaffold_render_is_deterministic():
    a = build_seed_scaffold(seed="/s", project_dir="/p", name="n", ai_dir="/a")
    b = build_seed_scaffold(seed="/s", project_dir="/p", name="n", ai_dir="/a")
    assert a.render() == b.render()


def test_scaffold_render_mentions_read_only():
    s = build_seed_scaffold(seed="/s", project_dir="/p", name="n", ai_dir="/a")
    assert "read-only" in s.render()


# ---------------------------------------------------------------------------
# Cycle 5, TICKET-011 (issue #14): general classify_seed_paths capability.
# ---------------------------------------------------------------------------


def test_classify_mapping_copy_entry():
    entries = classify_seed_paths({"/seed/src/app.py": "/proj/app.py"})
    assert len(entries) == 1
    e = entries[0]
    assert e.action == "copy"
    assert e.path == "/proj/app.py"
    assert e.source == "/seed/src/app.py"


def test_classify_mapping_reference_when_source_equals_dest():
    entries = classify_seed_paths({"/seed/README.md": "/seed/README.md"})
    assert len(entries) == 1
    e = entries[0]
    assert e.action == "reference"
    assert e.path == "/seed/README.md"
    assert e.source is None


def test_classify_mapping_reference_when_source_empty():
    entries = classify_seed_paths({"": "/seed/notes.md"})
    assert len(entries) == 1
    assert entries[0].action == "reference"
    assert entries[0].source is None


def test_classify_list_entries_are_create_with_extension_notes():
    entries = classify_seed_paths(["pkg/__init__.py", "docs/guide.md", "data.json"])
    actions = [e.action for e in entries]
    assert actions == ["create", "create", "create"]
    notes = {e.path: e.note for e in entries}
    assert notes["pkg/__init__.py"] == "python module"
    assert notes["docs/guide.md"] == "markdown doc"
    assert notes["data.json"] == "json data"
    # create entries never carry a source
    assert all(e.source is None for e in entries)


def test_classify_create_note_defaults_to_file_for_unknown_extension():
    entries = classify_seed_paths(["assets/logo.png"])
    assert entries[0].action == "create"
    assert entries[0].note == "file"


def test_classify_base_dir_prefixes_relative_paths():
    entries = classify_seed_paths(
        {"/seed/x.py": "out/x.py"}, base_dir="/root"
    )
    e = entries[0]
    assert e.action == "copy"
    # dest was relative -> prefixed with base_dir; source absolute -> untouched
    assert e.path == "/root/out/x.py"
    assert e.source == "/seed/x.py"


def test_classify_base_dir_prefixes_list_paths():
    entries = classify_seed_paths(["a/b.py"], base_dir="/root")
    assert entries[0].path == "/root/a/b.py"


def test_classify_absolute_dest_untouched_by_base_dir():
    entries = classify_seed_paths({"s.py": "/abs/dest.py"}, base_dir="/root")
    e = entries[0]
    assert e.action == "copy"
    assert e.path == "/abs/dest.py"  # absolute dest not prefixed
    assert e.source == "/root/s.py"  # relative source IS prefixed


def test_classify_seed_entry_is_frozen_dataclass():
    e = SeedEntry(action="reference", path="/p", source=None, note="n")
    with pytest.raises(dataclasses.FrozenInstanceError):
        e.path = "/other"  # type: ignore[misc]


def test_render_seed_entries_one_line_per_entry_in_order():
    entries = classify_seed_paths(
        {"/s/a.py": "/d/a.py", "/s/b.md": "/s/b.md"},
    ) + classify_seed_paths(["c.py"])
    rendered = render_seed_entries(entries)
    lines = rendered.split("\n")
    assert lines[0] == "  [copy] /d/a.py <- /s/a.py"
    assert lines[1] == "  [reference] /s/b.md"
    assert lines[2] == "  [create] c.py - python module"


def test_render_seed_entries_is_byte_deterministic():
    spec = {"/s/a.py": "/d/a.py", "/s/b.md": "/s/b.md"}
    a = render_seed_entries(classify_seed_paths(spec))
    b = render_seed_entries(classify_seed_paths(spec))
    assert a == b


# ---------------------------------------------------------------------------
# Cycle 5, TICKET-012 (issue #15): determinism + edge cases for the planner.
# ---------------------------------------------------------------------------


def test_classify_empty_dict_returns_empty_plan():
    assert classify_seed_paths({}) == []
    assert render_seed_entries(classify_seed_paths({})) == ""


def test_classify_empty_list_returns_empty_plan():
    assert classify_seed_paths([]) == []
    assert render_seed_entries(classify_seed_paths([])) == ""


def test_classify_duplicate_dest_first_seen_wins_deterministically():
    # Two mapping entries resolve to the SAME dest. The plan is a stable,
    # deterministic function of the input: first-seen order is preserved and two
    # calls over an equal dict are byte-identical (no insertion-order accidents).
    spec = {"/s/a.py": "/d/target.py", "/s/b.py": "/d/target.py"}
    a = classify_seed_paths(spec)
    b = classify_seed_paths(dict(spec))  # re-inserted in the same order
    assert [e.path for e in a] == ["/d/target.py", "/d/target.py"]
    assert [e.source for e in a] == ["/s/a.py", "/s/b.py"]
    # byte-determinism of the rendered plan across equal inputs
    assert render_seed_entries(a) == render_seed_entries(b)


def test_classify_duplicate_dest_render_is_byte_deterministic():
    spec = {"/s/a.py": "/d/target.py", "/s/b.py": "/d/target.py"}
    r1 = render_seed_entries(classify_seed_paths(spec))
    r2 = render_seed_entries(classify_seed_paths(spec))
    assert r1 == r2
    # both copy lines present, in input order
    assert "  [copy] /d/target.py <- /s/a.py" in r1.split("\n")
    assert "  [copy] /d/target.py <- /s/b.py" in r1.split("\n")


def test_classify_nested_dirs_single_separator():
    entries = classify_seed_paths(
        {"/seed/a/b/c/d.py": "out/x/y/z.py"}, base_dir="/root"
    )
    e = entries[0]
    assert e.action == "copy"
    # exactly one separator between base_dir and the relative dest (no double slash)
    assert e.path == "/root/out/x/y/z.py"
    assert "//" not in e.path
    assert e.source == "/seed/a/b/c/d.py"


def test_classify_nested_list_path_single_separator():
    entries = classify_seed_paths(["a/b/c/d/e.py"], base_dir="/root")
    assert entries[0].path == "/root/a/b/c/d/e.py"
    assert "//" not in entries[0].path


def test_classify_same_path_as_reference_and_copy_both_preserved():
    # The SAME canonical path "/d/thing.py" appears as a REFERENCE (source==dest) in one
    # entry and as a COPY dest in another. Both entries are preserved, each labeled by its
    # own action; the plan is byte-deterministic across equal inputs.
    spec = {"/d/thing.py": "/d/thing.py", "/other/thing.py": "/d/thing.py"}
    entries = classify_seed_paths(spec)
    assert len(entries) == 2
    actions = [e.action for e in entries]
    assert actions == ["reference", "copy"]
    ref = entries[0]
    cp = entries[1]
    assert ref.path == "/d/thing.py" and ref.source is None
    assert cp.path == "/d/thing.py" and cp.source == "/other/thing.py"
    rendered = render_seed_entries(entries)
    assert "  [reference] /d/thing.py" in rendered.split("\n")
    assert "  [copy] /d/thing.py <- /other/thing.py" in rendered.split("\n")
    # byte-deterministic across equal inputs
    assert rendered == render_seed_entries(classify_seed_paths(spec))


def test_classify_full_plan_byte_deterministic_mixed_spec():
    spec = {"/s/a.py": "/d/a.py", "/s/b.md": "/s/b.md"}
    mixed = classify_seed_paths(spec) + classify_seed_paths(["c.py"], base_dir="/root")
    r1 = render_seed_entries(mixed)
    r2 = render_seed_entries(
        classify_seed_paths(spec) + classify_seed_paths(["c.py"], base_dir="/root")
    )
    assert r1 == r2


# ---------------------------------------------------------------------------
# Cycle 6, TICKET-015 (issue #19): remaining determinism/edge coverage.
# ---------------------------------------------------------------------------


def test_classify_absolute_source_with_base_dir():
    # Source is absolute -> left untouched; relative dest gets the single-separator
    # base_dir prefix.
    entries = classify_seed_paths({"/abs/src/a.py": "out/a.py"}, base_dir="/root")
    e = entries[0]
    assert e.action == "copy"
    assert e.source == "/abs/src/a.py"  # absolute source untouched
    assert e.path == "/root/out/a.py"   # relative dest prefixed
    assert "//" not in e.path


def test_classify_create_no_extension_gets_file_note():
    entries = classify_seed_paths(["data/raw"])
    e = entries[0]
    assert e.action == "create"
    assert e.note == "file"  # no extension -> default note


def test_classify_create_dotfile_gets_file_note():
    # A dotfile like ".env" has no recognized extension -> deterministic "file" note.
    entries = classify_seed_paths([".env"])
    e = entries[0]
    assert e.action == "create"
    assert e.note == "file"


def test_classify_create_dotfile_render():
    rendered = render_seed_entries(classify_seed_paths([".env"]))
    assert rendered == "  [create] .env - file"


def test_classify_mixed_mapping_and_list_byte_identical():
    # A mapping (reference/copy) composed with a list (create) renders byte-identically
    # across two independent calls.
    spec_map = {"/s/a.py": "/d/a.py", "/s/b.md": "/s/b.md"}
    spec_list = ["c.py", ".env"]

    def build():
        return render_seed_entries(
            classify_seed_paths(spec_map) + classify_seed_paths(spec_list, base_dir="/root")
        )

    r1 = build()
    r2 = build()
    assert r1 == r2
    # all three actions present
    assert "  [copy] /d/a.py <- /s/a.py" in r1.split("\n")
    assert "  [reference] /s/b.md" in r1.split("\n")
    assert "  [create] /root/c.py - python module" in r1.split("\n")
    assert "  [create] /root/.env - file" in r1.split("\n")
