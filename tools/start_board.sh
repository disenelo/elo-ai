#!/usr/bin/env bash
# tools/start_board.sh — WO-B1-0121: Board gate session trigger script
#
# Usage: bash tools/start_board.sh <review_file_path>
#
# Called by watchdog Path 4 when a seat files a BUILT_* review to board_review/.
# Writes a BOARD_TRIGGER file to blender/agent_bus/board/ for pickup by a waiting
# Board session, and optionally auto-launches a Claude Code Board session.
#
# Board session rules (Board CLAUDE.md): LANE, VERIFY-BEFORE-CLAIM, no code edits.
# One card review. File gate decision back to seat inbox. Exit.
#
# Author: Builder 1 · 2026-10-12 (WO-B1-0121)

set -euo pipefail

REVIEW_FILE="${1:-}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AGENT_BUS="$ROOT/blender/agent_bus"
BOARD_INBOX="$AGENT_BUS/board"
LOG="$ROOT/tools/watchdog.log"

mkdir -p "$BOARD_INBOX"

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
STEM=$(basename "${REVIEW_FILE%.md}")
TRIGGER_FILE="$BOARD_INBOX/BOARD_TRIGGER_${STEM:0:50}_$(date '+%Y%m%d_%H%M%S').md"

cat > "$TRIGGER_FILE" <<EOF
# BOARD_TRIGGER — Auto-gate request
**Triggered:** $TIMESTAMP
**Review file:** ${REVIEW_FILE:-<unknown>}

A seat filed a board review. Read the review at \`${REVIEW_FILE}\`, gate it
(sign off or send back with specific reasons), file the gate decision to the
seat's inbox under \`blender/agent_bus/<seat>/\`, then exit.

Board rules: LANE — no code edits. VERIFY-BEFORE-CLAIM — read the file first.
One card only. Commit decision. Exit.
EOF

echo "[$TIMESTAMP] BOARD_TRIGGER written → $TRIGGER_FILE" >> "$LOG"

# ── MANUAL LAUNCH POINT ────────────────────────────────────────────────────
# To auto-launch a Claude Code Board session, add your invocation here.
# Example (uncomment and adjust flags to your setup):
#
#   BOARD_CLAUDE="$ROOT/blender/agent_bus/board"
#   PROMPT="You are the Board (Lead Architect). Check $BOARD_INBOX/ for BOARD_TRIGGER_* files. Read the review, gate it, file decision to seat inbox. One card. Commit. Exit."
#   claude --print "$PROMPT" >> "$LOG" 2>&1 &
#   echo "[$TIMESTAMP] Board session launched (PID $!)" >> "$LOG"
#
# Leave commented out to rely on trigger files only (manual Board pickup).
# ──────────────────────────────────────────────────────────────────────────

echo "BOARD_TRIGGER written to $TRIGGER_FILE"
