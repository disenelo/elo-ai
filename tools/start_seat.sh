#!/usr/bin/env bash
set -euo pipefail
SEAT="${1:-builder}"
PROMPT="${2:-Read your inbox, pick the highest-priority card, build it, commit, file to board_review/, EXIT.}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="${REPO_ROOT}/data"
mkdir -p "${LOG_DIR}"
LOG_FILE="${LOG_DIR}/watchdog_seat_runs.log"
echo "[start_seat.sh] $(date '+%Y-%m-%d %H:%M:%S') seat=${SEAT}" >> "${LOG_FILE}"
exec claude --print --dangerously-skip-permissions --add-dir "${REPO_ROOT}" --output-format text "${PROMPT}" >> "${LOG_FILE}" 2>&1
