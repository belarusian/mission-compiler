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
