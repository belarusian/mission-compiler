"""Describe the seed-directory scaffold for a mission-compiler launch.

The seed is a READ-ONLY reference. mission-compiler never copies the seed's
source files into the project; it only records what the seed path provides
and what the project must create itself. This module produces that scaffold
description deterministically.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ScaffoldItem:
    """One line of the seed scaffold plan."""

    action: str  # "reference" | "create" | "copy"
    path: str
    note: str


@dataclass(frozen=True)
class SeedScaffold:
    """The full seed scaffold plan for a launch."""

    seed_path: str | None
    items: list[ScaffoldItem] = field(default_factory=list)

    def render(self) -> str:
        """Render the scaffold plan as a readable block."""
        lines: list[str] = []
        if self.seed_path:
            lines.append(f"Seed (read-only reference, never copy files): {self.seed_path}")
        else:
            lines.append("Seed: (none - no reference project)")
        lines.append("")
        lines.append("Scaffold plan:")
        for item in self.items:
            lines.append(f"  [{item.action}] {item.path} - {item.note}")
        return "\n".join(lines)


def build_seed_scaffold(
    *,
    seed: str | None,
    project_dir: str,
    name: str,
    ai_dir: str,
) -> SeedScaffold:
    """Build the seed scaffold plan for a launch.

    The plan is a pure function of its inputs. It records:
      * the seed path as a read-only reference (if given);
      * the project files that must be created (package, tests, config);
      * the AI artifacts that must be created (log, runner prompt, briefing).
    """
    items: list[ScaffoldItem] = []
    if seed:
        items.append(
            ScaffoldItem(
                action="reference",
                path=seed,
                note="read for semantics only; synthesize original code; never copy files",
            )
        )
    items.append(
        ScaffoldItem(
            action="create",
            path=f"{project_dir}/{name}/__init__.py",
            note="package init with __version__",
        )
    )
    items.append(
        ScaffoldItem(
            action="create",
            path=f"{project_dir}/tests/test_smoke.py",
            note="smoke test asserting the package imports",
        )
    )
    items.append(
        ScaffoldItem(
            action="create",
            path=f"{project_dir}/pyproject.toml",
            note="project metadata + pytest/ruff/mypy config",
        )
    )
    items.append(
        ScaffoldItem(
            action="create",
            path=f"{ai_dir}/cycle-001-{name}-gate.md",
            note="cycle log (single source of truth)",
        )
    )
    items.append(
        ScaffoldItem(
            action="create",
            path=f"{ai_dir}/{name}-cycle-runner-prompt.md",
            note="runner prompt (rules + 6-phase framework)",
        )
    )
    items.append(
        ScaffoldItem(
            action="create",
            path=f"{ai_dir}/{name}-cycle-1-briefing.md",
            note="first cycle briefing",
        )
    )
    return SeedScaffold(seed_path=seed, items=items)


# ---------------------------------------------------------------------------
# General seed-path classifier (Cycle 5, TICKET-011 / issue #14).
#
# build_seed_scaffold above is a FIXED builder for the standard four-project
# layout. The functions below are the GENERAL planner: given an arbitrary seed
# spec (a mapping of source -> dest, or a list of paths with a base dir), every
# entry is classified as reference / create / copy and rendered deterministically.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SeedEntry:
    """One classified path in a general seed scaffold plan."""

    action: str  # "reference" | "create" | "copy"
    path: str  # destination / canonical path for this entry
    source: str | None  # resolved source, set ONLY when action == "copy"
    note: str  # human note; for "create" the intended content/placeholder


# Deterministic content/placeholder by file extension (for "create" entries).
_CREATE_NOTES = {
    ".py": "python module",
    ".md": "markdown doc",
    ".toml": "toml config",
    ".json": "json data",
    ".txt": "text file",
}


def _resolve(base_dir: str, path: str) -> str:
    """Prefix a relative path with base_dir using a single '/' separator.

    Absolute paths are returned untouched. An empty base_dir leaves the path as-is.
    """
    if not base_dir or path.startswith("/"):
        return path
    return f"{base_dir.rstrip('/')}/{path.lstrip('/')}"


def _create_note(path: str) -> str:
    """Deterministic intended-content note for a create entry, by extension."""
    dot = path.rfind(".")
    ext = path[dot:].lower() if dot != -1 else ""
    return _CREATE_NOTES.get(ext, "file")


def classify_seed_paths(
    spec: dict[str, str] | list[str],
    *,
    base_dir: str = "",
) -> list[SeedEntry]:
    """Classify an arbitrary seed spec into a deterministic plan of SeedEntry.

    ``spec`` is either:
      * a MAPPING ``{source: dest}`` — each pair is classified as reference or copy;
        - if ``dest == source`` (or ``source`` is empty/None) -> **reference** (path only);
        - otherwise -> **copy**, with the source resolved against ``base_dir``.
      * a LIST of paths — each path is a **create** entry (created in place), with a
        deterministic content note derived from its extension.

    ``base_dir``, when non-empty, prefixes relative paths (source and dest) with a single
    '/' separator; absolute paths are left untouched. The result order follows the input
    order (dict insertion order / list order), so the plan is byte-deterministic.
    """
    entries: list[SeedEntry] = []
    if isinstance(spec, dict):
        for source, dest in spec.items():
            src = "" if source is None else str(source)
            dst = _resolve(base_dir, str(dest))
            if not src or src == str(dest):
                entries.append(
                    SeedEntry(
                        action="reference",
                        path=dst,
                        source=None,
                        note="read for semantics only; synthesize original code; never copy files",
                    )
                )
            else:
                resolved_src = _resolve(base_dir, src)
                entries.append(
                    SeedEntry(
                        action="copy",
                        path=dst,
                        source=resolved_src,
                        note=f"copy from {resolved_src}",
                    )
                )
    else:
        for path in spec:
            dst = _resolve(base_dir, str(path))
            entries.append(
                SeedEntry(
                    action="create",
                    path=dst,
                    source=None,
                    note=_create_note(dst),
                )
            )
    return entries


def render_seed_entries(entries: list[SeedEntry]) -> str:
    """Render classified entries as a deterministic, one-line-per-entry block.

    Line formats (input order preserved):
      * copy:      ``  [copy] <dest> <- <source>``
      * create:    ``  [create] <path> - <note>``
      * reference: ``  [reference] <path>``
    An empty list renders as the empty string.
    """
    lines: list[str] = []
    for e in entries:
        if e.action == "copy":
            lines.append(f"  [copy] {e.path} <- {e.source}")
        elif e.action == "create":
            lines.append(f"  [create] {e.path} - {e.note}")
        else:  # reference
            lines.append(f"  [reference] {e.path}")
    return "\n".join(lines)
