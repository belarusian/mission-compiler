"""Build the full nohup launch script for a mission-compiler launch.

The launch script wraps the OUTER orchestrator (``run.py``) in a ``perl
alarm`` wall-clock bound, and the outer orchestrator in turn wraps the INNER
spoke. This is the "four pipeline launches" composition:

  1. outer orchestrator (run.py) - wall-bounded by ``perl alarm``
  2. inner spoke (project-setup / cycle-implementation)
  3. auditor spoke (invoked by the inner spoke in Phase 2)
  4. validator spoke (invoked by the inner spoke in Phase 4)

The script is a pure function of its inputs (no timestamps), so the same
inputs always produce the same script. GOAL and INNER are embedded via
single-quoted heredocs so that newlines, double quotes, and single quotes in
the goal text are preserved literally and the script is always valid bash.
"""

from __future__ import annotations

from .bounds import Bounds
from .spoke_cmd import SpokeCommand

#: Default path to the outer orchestrator.
DEFAULT_RUN_PY = "/home/sasha/Research/four/run.py"


def _perl_alarm(seconds: int, cmd: str) -> str:
    """Wrap ``cmd`` in a ``perl alarm`` wall-clock bound.

    ``perl -e 'alarm shift; exec @ARGV' <seconds> <cmd...>`` fires SIGALRM
    after ``seconds`` and then execs the command. This is the portable
    wall-clock bound used by the proven pipelines (run-cycles.sh).
    """
    return f"perl -e 'alarm shift; exec @ARGV' {seconds} {cmd}"


def _heredoc(name: str, content: str) -> str:
    """Embed ``content`` as a single-quoted heredoc assignment.

    A single-quoted heredoc delimiter (``<<'NAME'``) preserves every byte of
    the body literally - newlines, double quotes, single quotes, backticks,
    and dollar signs are all taken verbatim. This makes the generated script
    valid bash regardless of what the goal text contains.
    """
    return f"{name}=$(cat <<'{name}_EOF'\n{content}\n{name}_EOF\n)"


def build_launch_script(
    *,
    goal: str,
    inner: SpokeCommand,
    bounds: Bounds,
    log: str,
    trajectories: str,
    project_dir: str,
    name: str,
    run_py: str = DEFAULT_RUN_PY,
) -> str:
    """Return the full nohup launch script, ready to execute.

    The script:
      * sets ``set -uo pipefail``;
      * defines the GOAL and INNER variables via single-quoted heredocs;
      * runs the outer orchestrator wall-bounded by ``perl alarm``;
      * is launched with ``nohup ... &`` so it survives the terminal.
    """
    inner_line = inner.render()
    outer_cmd = (
        f"python3 {run_py} \\\n"
        f"  --goal \"$GOAL\" --inner \"$INNER\" --inner-seconds {bounds.inner_seconds} \\\n"
        f"  --log \"$LOG\" --trajectories \"$TRAJECTORIES\" \\\n"
        f"  --project-dir \"$PROJECT_DIR\" --outer-steps {bounds.outer_steps}"
    )
    bounded = _perl_alarm(bounds.outer_wall, outer_cmd)

    goal_heredoc = _heredoc("GOAL", goal)
    inner_heredoc = _heredoc("INNER", inner_line)

    script = f"""#!/bin/bash
# mission-compiler launch script for {name}
# Generated deterministically by mission-compiler compose.
# Bounds (proven table): outer wall {bounds.outer_wall}s, inner {bounds.inner_seconds}s,
#   outer-steps {bounds.outer_steps}, inner max-steps {bounds.inner_max_steps}.
set -uo pipefail

PROJECT_DIR="{project_dir}"
LOG="{log}"
TRAJECTORIES="{trajectories}"
OUT="$PROJECT_DIR/launch.out"

{goal_heredoc}
{inner_heredoc}

echo "========== {name} launch  (outer wall {bounds.outer_wall}s) =========="
{bounded}
echo "========== {name} launch done =========="
"""
    return script


def build_nohup_command(script_path: str) -> str:
    """Return the ``nohup`` command that launches the script in the background."""
    return f"nohup bash {script_path} > {script_path}.out 2>&1 &"
