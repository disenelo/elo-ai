#!/usr/bin/env bash
# tools/start_seat.sh — WO-B1-0112: Seat session trigger script
#
# Usage: bash tools/start_seat.sh <seat> [source_file]
#
# Writes a START signal file to the seat's inbox so the seat picks it up
# at next session open. Logs the event to tools/watchdog.log.
#
# To auto-launch Claude Code sessions, add your preferred invocation below
# the "MANUAL LAUNCH POINT" comment. The watchdog calls this script but does
# not prescribe the exact claude CLI flags — those depend on your setup.
#
# Author: Builder 1 · 2026-10-11

set -euo pipefail

SEAT="${1:-}"
SOURCE_FILE="${2:-}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AGENT_BUS="$ROOT/blender/agent_bus"
LOG="$ROOT/tools/watchdog.log"

if [[ -z "$SEAT" ]]; then
    echo "Usage: $0 <seat> [source_file]" >&2
    exit 1
fi

INBOX="$AGENT_BUS/$SEAT"
mkdir -p "$INBOX"

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
TRIGGER_FILE="$INBOX/TRIGGER_$(date '+%Y%m%d_%H%M%S')_watchdog.md"

cat > "$TRIGGER_FILE" <<EOF
# Auto-trigger from watchdog
**Seat:** $SEAT
**Triggered:** $TIMESTAMP
**Source file:** ${SOURCE_FILE:-<intake drop>}

Watchdog detected a new file. Read your inbox and pick the highest-priority
unstarted card. One card. Commit. File to Board. Exit.
EOF

echo "[$TIMESTAMP] TRIGGER written → $TRIGGER_FILE" >> "$LOG"

# ── MANUAL LAUNCH POINT ────────────────────────────────────────────────────
# To auto-launch a Claude Code session, add your invocation here.
# Example (uncomment and adjust flags to your setup):
#
#   PROMPT="Check inbox at $INBOX/ for TRIGGER_* files. Pick highest-priority card. Do it. Commit. File to board_review/. Stop."
#   claude --print "$PROMPT" >> "$LOG" 2>&1 &
#   echo "[$TIMESTAMP] claude session launched for $SEAT (PID $!)" >> "$LOG"
#
# Leave commented out to rely on trigger files only (manual session pickup).
# ──────────────────────────────────────────────────────────────────────────

echo "Trigger written to $TRIGGER_FILE"
