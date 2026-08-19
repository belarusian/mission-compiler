#!/usr/bin/env bash
# mission-compiler example: compose the fleet project end-to-end (cycle spoke).
#
# Deterministic: running this script twice produces byte-identical output.
# It composes a real four project (fleet) using the cycle-implementation spoke
# with an explicit --seed-spec, writes the launch script to a FIXED throwaway
# path, validates it with `bash -n`, and prints the rendered launch. A fixed
# (non-mktemp) path is used so the rendered output contains no run-specific bytes.
set -uo pipefail

# Fixed throwaway project/ai dir so the example never touches real artifacts
# AND so the rendered output is byte-identical across runs.
PROJ="/tmp/mission-compiler-example/fleet/proj"
AI="/tmp/mission-compiler-example/fleet/ai"
mkdir -p "$PROJ" "$AI"

SCRIPT_PATH="$PROJ/launch-fleet.sh"

# Compose the launch (prints all five sections) and write the script.
python3 -m mission_compiler compose \
  "Build fleet: a deterministic multi-agent build orchestrator." \
  --spoke cycle-implementation \
  --cycle 1 \
  --name fleet \
  --repo belarusian/fleet \
  --seed /home/sasha/Research/four \
  --seed-spec '{"run.py": "run.py", "README.md": "README.md"}' \
  --cycles 12 \
  --project-dir "$PROJ" \
  --ai-dir "$AI" \
  --script-path "$SCRIPT_PATH" \
  --write \
  --validate

echo
echo "=== bash -n self-test on the written launch script ==="
bash -n "$SCRIPT_PATH" && echo "OK: $SCRIPT_PATH passes bash -n"
