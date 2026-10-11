#!/usr/bin/env bash
# start_seat.sh — loop until queue empty, seat-locked.
# Usage: bash tools/start_seat.sh [seat]
# Seats: builder | builder2 | builder3 | board
set -uo pipefail

SEAT="${1:-builder}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="${REPO_ROOT}/data"
LOCK_DIR="${REPO_ROOT}/locks"
mkdir -p "${LOG_DIR}" "${LOCK_DIR}"
LOG_FILE="${LOG_DIR}/watchdog_seat_runs.log"
SEAT_LOCK="${LOCK_DIR}/seat_${SEAT}.lock"

# ── Seat lock: one session per seat at a time ─────────────────────────────────
if [[ -f "${SEAT_LOCK}" ]]; then
    echo "[start_seat] $(date '+%Y-%m-%d %H:%M:%S') SKIP ${SEAT} — already running ($(cat "${SEAT_LOCK}"))" >> "${LOG_FILE}"
    echo "[start_seat] ${SEAT} already running. Exiting." >&2; exit 0
fi
printf "seat=%s pid=%s started=%s" "${SEAT}" "$$" "$(date '+%Y-%m-%d %H:%M:%S')" > "${SEAT_LOCK}"
trap 'rm -f "${SEAT_LOCK}"; echo "[start_seat] $(date +%Y-%m-%d\ %H:%M:%S) EXIT ${SEAT} pid=$$" >> "${LOG_FILE}"' EXIT

# ── Per-seat inbox + prompt ───────────────────────────────────────────────────
case "${SEAT}" in
  builder)  INBOX_DIR="${REPO_ROOT}/blender/agent_bus/builder" ;;
  builder2) INBOX_DIR="${REPO_ROOT}/blender/agent_bus/builder2" ;;
  builder3) INBOX_DIR="${REPO_ROOT}/blender/agent_bus/builder3" ;;
  board)    INBOX_DIR="${REPO_ROOT}/blender/agent_bus/builder" ;;
  *)
    echo "[start_seat] Unknown seat '${SEAT}'. Valid: builder builder2 builder3 board" >&2; exit 1
    ;;
esac

echo "[start_seat] $(date '+%Y-%m-%d %H:%M:%S') ${SEAT} — running until queue empty"

# ── Main loop ─────────────────────────────────────────────────────────────────
# No subprocess. No claude --print. The script surfaces the next FROM_BOARD
# card to the seat's existing terminal session — the seat reads it and acts.
# A card is consumed (moved to processed/) after being surfaced, so it cannot
# retrigger. Ctrl+C stops the loop. [DAVID 2026-10-10]
PROCESSED_DIR="${INBOX_DIR}/processed"
mkdir -p "${PROCESSED_DIR}"

while true; do
    # Oldest-first: tail -1 of ls -t (newest first) gives oldest
    JOB=$(ls -t "${INBOX_DIR}"/FROM_BOARD_*.md 2>/dev/null | tail -1)

    if [[ -z "${JOB}" ]]; then
        echo "[start_seat] $(date '+%Y-%m-%d %H:%M:%S') ${SEAT} — inbox empty. Waiting..."
        sleep 10
        continue
    fi

    CARD_NAME="${JOB##*/}"
    echo "[start_seat] $(date '+%Y-%m-%d %H:%M:%S') ${SEAT} — found: ${CARD_NAME}"
    echo "[start_seat] $(date '+%Y-%m-%d %H:%M:%S') DISPATCH ${SEAT} ${CARD_NAME}" >> "${LOG_FILE}"

    # Surface the job file to this terminal — seat reads and acts inline.
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    cat "${JOB}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    mv "${JOB}" "${PROCESSED_DIR}/${CARD_NAME}"
    echo "[start_seat] $(date '+%Y-%m-%d %H:%M:%S') ${SEAT} — ${CARD_NAME} moved to processed/"
    echo "[start_seat] $(date '+%Y-%m-%d %H:%M:%S') DONE ${SEAT} ${CARD_NAME}" >> "${LOG_FILE}"

    sleep 5
done
