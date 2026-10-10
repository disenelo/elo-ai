#!/bin/bash
SEAT="${1:-builder}"
PROMPT="${2:-Read blender/agent_bus/$SEAT/START_HERE.md. Check inbox for new FROM_BOARD files. Do one card. Commit. File to Board. Exit.}"
cd "$(dirname "$0")/.."
if ! command -v claude &>/dev/null; then echo "[start_seat] claude CLI not found" >&2; exit 1; fi
exec claude --print "$PROMPT"
