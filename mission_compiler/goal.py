"""Compose the GOAL text for a mission-compiler launch.

The GOAL carries the free-text mission plus the four v3 delta descriptions
inline, so the inner spoke sees them as standing rules rather than one-time
prose:

  * Phase 0 pre-flight - verify the gate is green and no unmerged build
    branch remains before any new work.
  * Phase 5 issue sweep - close issues shipped this cycle, evidence cited.
  * Bounded post-plan POLISH class - docs/tests/CLI/examples/release; if
    exhausted, log DONE and stop.
  * INCOMPLETE log note - on unmerged cycle exit, record what remains.
"""

from __future__ import annotations


def _delta_block() -> str:
    """The four v3 delta descriptions, inline in the GOAL."""
    return (
        "STANDING RULES (v3 deltas, apply every cycle):\n"
        "- Phase 0 PRE-FLIGHT: `git checkout main && git pull`. If the gate is red "
        "or an unmerged build branch remains from a previous cycle, that repair is "
        "this cycle's work FIRST: finish/merge it, get the gate green, log it as a "
        "Repair cycle, only then continue.\n"
        "- Phase 5 ISSUE SWEEP: after merge, `gh issue list --state open`; for every "
        "issue whose ticket was implemented THIS cycle, close it with evidence cited "
        "(PR number + short sha + gate green). Close only what this cycle shipped.\n"
        "- BOUNDED POST-PLAN POLISH CLASS: once the cycle number is past the last row "
        "of the Build Order, work the POLISH class only (docs/README, missing test "
        "coverage, CLI passthrough gaps, examples, release metadata). Never invent "
        "scope beyond the mission; if the polish class is exhausted, log "
        "`## Cycle N: DONE - plan and polish complete` and stop cleanly.\n"
        "- INCOMPLETE LOG NOTE: if the cycle ends without merging (bound reached, "
        "gate red, stuck), append `## Cycle N: INCOMPLETE - <branch> + what remains>` "
        "before stopping, so the next cycle's Phase 0 has the trail."
    )


def compose_goal(
    mission: str,
    *,
    spoke: str,
    cycles: int,
    repo: str | None,
    seed: str | None,
    project_dir: str,
    ai_dir: str,
    name: str,
    private: bool = False,
) -> str:
    """Return the full GOAL text for a launch.

    The result is a pure function of its arguments (no timestamps, no
    randomness), so identical inputs always produce identical GOAL text.
    """
    parts: list[str] = []
    parts.append(f"Mission: {mission.strip()}")
    parts.append("")
    parts.append(f"Project: {name}")
    parts.append(f"Spoke: {spoke}")
    parts.append(f"Planned cycles: {cycles}")
    parts.append(f"Project dir: {project_dir}")
    parts.append(f"AI dir: {ai_dir}")
    if repo:
        # Additive: when both repo and private are set the repo line carries a
        # (private) marker; otherwise it is byte-identical to before. No repo
        # line at all when repo is None (regardless of private).
        if private:
            parts.append(f"GitHub repo: {repo} (private)")
        else:
            parts.append(f"GitHub repo: {repo}")
    if seed:
        parts.append(f"Seed (read-only reference, never copy files): {seed}")
    parts.append("")
    parts.append(_delta_block())
    return "\n".join(parts)
