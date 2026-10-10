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

if ! command -v claude &>/dev/null; then
    echo "[start_seat] claude CLI not found" >&2; exit 1
fi

# ── Seat lock: one session per seat at a time ─────────────────────────────────
if [[ -f "${SEAT_LOCK}" ]]; then
    echo "[start_seat] $(date '+%Y-%m-%d %H:%M:%S') SKIP ${SEAT} — already running ($(cat "${SEAT_LOCK}"))" >> "${LOG_FILE}"
    echo "[start_seat] ${SEAT} already running. Exiting." >&2; exit 0
fi
printf "seat=%s pid=%s started=%s" "${SEAT}" "$$" "$(date '+%Y-%m-%d %H:%M:%S')" > "${SEAT_LOCK}"
trap 'rm -f "${SEAT_LOCK}"; echo "[start_seat] $(date +%Y-%m-%d\ %H:%M:%S) EXIT ${SEAT} pid=$$" >> "${LOG_FILE}"' EXIT

# ── Per-seat inbox + prompt ───────────────────────────────────────────────────
case "${SEAT}" in
  builder)
    INBOX_DIR="${REPO_ROOT}/blender/agent_bus/builder"
    PROMPT="You are Builder 1. Read ${INBOX_DIR}/START_HERE.md. Pick the highest-priority card in QUEUE/ that is not already in DOING/ or BUILT/. Move it to DOING/. Follow the FILE LOCK PROTOCOL (create <filepath>.lock before editing any shared file, delete after commit). Build it. Commit. Move card to BUILT/. File board_review/ summary. EXIT — one card only."
    ;;
  builder2)
    INBOX_DIR="${REPO_ROOT}/blender/agent_bus/builder2"
    PROMPT="You are Builder 2 (Inner Thought / Cognitive). Read ${INBOX_DIR}/START_HERE.md. Check your inbox for FROM_BOARD assignments. Pick the highest-priority spec or cognitive work. Follow the FILE LOCK PROTOCOL (create <filepath>.lock before editing any shared file, delete after commit). Build it. Commit. File board_review/ summary. EXIT — one card only."
    ;;
  builder3)
    INBOX_DIR="${REPO_ROOT}/blender/agent_bus/builder3"
    PROMPT="You are Builder 3 (Integrations). Read ${INBOX_DIR}/START_HERE.md. Check your inbox for FROM_BOARD assignments. Pick the highest-priority integration card (Spotify, Alexa, Search). Follow the FILE LOCK PROTOCOL (create <filepath>.lock before editing any shared file, delete after commit). Build it. Commit. File board_review/ summary. EXIT — one card only."
    ;;
  board)
    INBOX_DIR="${REPO_ROOT}/blender/agent_bus/builder"
    PROMPT="You are the Board. Read ${REPO_ROOT}/blender/agent_bus/builder/board_review/ for new submissions. Process each: close completed WOs, write new cards to appropriate QUEUE/, commit. EXIT — one pass only."
    ;;
  *)
    echo "[start_seat] Unknown seat '${SEAT}'. Valid: builder builder2 builder3 board" >&2; exit 1
    ;;
esac

echo "[start_seat] $(date '+%Y-%m-%d %H:%M:%S') ${SEAT} — running until queue empty"

# ── Main loop ─────────────────────────────────────────────────────────────────
while true; do
    # Check for pending work: FROM_BOARD files not yet processed
    PENDING=$(ls "${INBOX_DIR}"/FROM_BOARD_*.md 2>/dev/null | head -1)

    if [[ -z "${PENDING}" ]]; then
        echo "[start_seat] $(date '+%Y-%m-%d %H:%M:%S') ${SEAT} — queue empty, waiting 30s..."
        sleep 30
        continue
    fi

    echo "[start_seat] $(date '+%Y-%m-%d %H:%M:%S') ${SEAT} — card found: ${PENDING##*/}" >> "${LOG_FILE}"
    cd "${REPO_ROOT}"
    claude --print --dangerously-skip-permissions --add-dir "${REPO_ROOT}" --output-format text "${PROMPT}" >> "${LOG_FILE}" 2>&1
    echo "[start_seat] $(date '+%Y-%m-%d %H:%M:%S') ${SEAT} — card done, checking for more..."
    sleep 5
done
