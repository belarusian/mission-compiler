"""mission-compiler: deterministic CLI tool that composes four pipeline launches
from a free-text mission description.

Public API:
    compose(mission, ...) -> ComposedLaunch
    ComposedLaunch
    Bounds, bounds_for
    SpokeCommand
    SeedScaffold, SeedEntry, classify_seed_paths, render_seed_entries
"""

from __future__ import annotations

from .bounds import Bounds, bounds_for
from .compose import ComposedLaunch, compose
from .seed_scaffold import (
    SeedEntry,
    SeedScaffold,
    classify_seed_paths,
    render_seed_entries,
)
from .spoke_cmd import SpokeCommand

__version__ = "0.1.0"

__all__ = [
    "Bounds",
    "ComposedLaunch",
    "SeedEntry",
    "SeedScaffold",
    "classify_seed_paths",
    "render_seed_entries",
    "SpokeCommand",
    "bounds_for",
    "compose",
    "__version__",
]
