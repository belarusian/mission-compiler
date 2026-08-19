#!/usr/bin/env bash
# mission-compiler example: compose a real project with the opt-in --config axis.
#
# Deterministic: running this script twice produces byte-identical output.
# It composes a real four project (fourseer) using the cycle-implementation spoke
# and selects the proven-bounds row by LLM configuration (--config
# single-llm-long-pass) instead of by spoke type, so the [3] BOUNDS section shows
# the config row (outer wall 10800s). It writes the launch script to a FIXED
# throwaway path, validates it with `bash -n`, and prints the rendered launch. A
# fixed (non-mktemp) path is used so the rendered output contains no run-specific
# bytes.
set -uo pipefail

# Fixed throwaway project/ai dir so the example never touches real artifacts
# AND so the rendered output is byte-identical across runs.
PROJ="/tmp/mission-compiler-example/fourseer-config/proj"
AI="/tmp/mission-compiler-example/fourseer-config/ai"
mkdir -p "$PROJ" "$AI"

SCRIPT_PATH="$PROJ/launch-fourseer.sh"

# Compose the launch (prints all five sections) and write the script. The --config
# flag selects the single-llm-long-pass proven-bounds row (outer wall 10800s).
python3 -m mission_compiler compose \
  "Build fourseer: a deterministic fleet supervisor." \
  --spoke cycle-implementation \
  --cycle 1 \
  --name fourseer \
  --repo belarusian/fourseer \
  --seed /home/sasha/Research/four \
  --config single-llm-long-pass \
  --cycles 12 \
  --project-dir "$PROJ" \
  --ai-dir "$AI" \
  --script-path "$SCRIPT_PATH" \
  --write \
  --validate

echo
echo "=== bash -n self-test on the written launch script ==="
bash -n "$SCRIPT_PATH" && echo "OK: $SCRIPT_PATH passes bash -n"
