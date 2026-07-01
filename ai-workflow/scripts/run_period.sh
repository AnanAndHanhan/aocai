#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 PERIOD [image ...]" >&2
  echo "Example: $0 2026-178 image1.png image2.png" >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PERIOD="$1"
shift
RUN_ID="${AUCAI_RUN_ID:-${PERIOD}}"

echo "Period: ${PERIOD}"
echo "Run ID: ${RUN_ID}"

python3 "${SCRIPT_DIR}/vision_extract.py" --run-id "${RUN_ID}" "$@"
python3 "${SCRIPT_DIR}/build_brief.py" --period "${PERIOD}" --run-id "${RUN_ID}"
python3 "${SCRIPT_DIR}/cross_analyze.py" --period "${PERIOD}" --run-id "${RUN_ID}"

echo "Final analysis:"
echo "${SCRIPT_DIR}/../output/${PERIOD}/当期分析.md"
