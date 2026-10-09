#!/bin/bash
# OPTION 3 — Tailscale Funnel. B3, card 0008.
# Needs: a free Tailscale account. First run of the app asks you to sign in.
# Funnel must be allowed for this Mac: the script prints the link if it isn't.
cd "$(dirname "$0")" && source ./common.sh
echo "eLo · Alexa permanent tunnel · OPTION 3: Tailscale Funnel"
need_brew
TS=/Applications/Tailscale.app/Contents/MacOS/Tailscale
command -v tailscale >/dev/null && TS="$(command -v tailscale)"
if [ ! -x "$TS" ] && ! command -v tailscale >/dev/null; then
  say_step "Installing Tailscale"; brew install --cask tailscale || die "install failed"
  open -a Tailscale
  read -r -p "Sign in to Tailscale in the window that opened, then press Enter."
fi
check_listener
"$TS" status >/dev/null 2>&1 || { open -a Tailscale; read -r -p "Sign in / connect Tailscale, then press Enter."; }
say_step "Turning on Funnel for port $PORT (persists across restarts)"
OUT=$("$TS" funnel --bg "$PORT" 2>&1); echo "$OUT"
if echo "$OUT" | grep -qi 'https://login.tailscale.com'; then
  echo "  → Open the link above, allow Funnel for this Mac, then press Enter."; read -r
  "$TS" funnel --bg "$PORT" || die "Funnel still not allowed."
fi
HOST=$("$TS" status --json 2>/dev/null | python3 -c 'import sys,json;print(json.load(sys.stdin)["Self"]["DNSName"].rstrip("."))')
[ -n "$HOST" ] || die "Couldn't read this Mac's Tailscale name."
URL="https://$HOST"
sleep 3
verify_url "$URL"
save_url "$URL"
alexa_console_steps "$URL"
echo "Funnel stays on through restarts while Tailscale is running (it starts at login)."
echo "To turn it off:  \"$TS\" funnel --bg $PORT off"
read -r -p "Done. Press Enter to close."
