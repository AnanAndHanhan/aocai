#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_ID="${AUCAI_RUN_ID:-$(date +%Y%m%d-%H%M%S)}"

echo "Run ID: ${RUN_ID}"

python3 "${SCRIPT_DIR}/vision_extract.py" --run-id "${RUN_ID}" "$@"
python3 "${SCRIPT_DIR}/analyze_with_qwen3.py" --run-id "${RUN_ID}"

echo "Final analysis:"
echo "${SCRIPT_DIR}/../outputs/${RUN_ID}/final_analysis.md"
