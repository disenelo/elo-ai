#!/bin/bash
# launch_orchestrator.sh — launchd wrapper for seat_orchestrator.py
#
# Called by com.disenelo.elo-orchestrator.plist every 5 minutes.
# Uses a PID file to prevent overlapping instances — exits cleanly if already running.
# No external dependencies (no flock, no brew packages required).

PID_FILE="/tmp/com.disenelo.elo-orchestrator.pid"
LOG_FILE="$HOME/elo-ai/engineering/orchestrator_schedule.log"
ORCHESTRATOR="$HOME/elo-ai/engineering/seat_orchestrator.py"

# Locate python3 — try homebrew first (launchd PATH is minimal)
for PYTHON in /opt/homebrew/bin/python3 /usr/local/bin/python3 /usr/bin/python3; do
    [ -x "$PYTHON" ] && break
done

ts() { date '+%Y-%m-%dT%H:%M:%S'; }

# Check if another instance is still alive
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE" 2>/dev/null)
    if [ -n "$OLD_PID" ] && kill -0 "$OLD_PID" 2>/dev/null; then
        echo "[$(ts)] SKIP — orchestrator already running (PID $OLD_PID)" >> "$LOG_FILE"
        exit 0
    fi
    # Stale PID file — previous run exited without cleanup
    rm -f "$PID_FILE"
fi

# Write our PID so future invocations see us
echo $$ > "$PID_FILE"
# Remove PID file on any exit (normal, signal, or error)
trap 'rm -f "$PID_FILE"' EXIT

echo "[$(ts)] START — launchd invocation  python=$PYTHON  pid=$$" >> "$LOG_FILE"

"$PYTHON" "$ORCHESTRATOR" loop builder,design >> "$LOG_FILE" 2>&1
EXIT_CODE=$?

echo "[$(ts)] EXIT  code=$EXIT_CODE" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
exit $EXIT_CODE
