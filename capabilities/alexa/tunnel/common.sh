#!/bin/bash
# Shared helpers for the three Alexa tunnel options (B3, card 0008).
# The tunnel exposes ONLY eLo's Alexa listener (127.0.0.1:5051, /alexa, Amazon-signed
# requests only) — never the main eLo server on 5050.
ELO="$HOME/elo-ai"
PORT="${ALEXA_PORT:-5051}"

say_step() { printf '\n\033[1m▶ %s\033[0m\n' "$*"; }
die()      { printf '\n\033[31m✗ %s\033[0m\n' "$*"; read -r -p "Press Enter to close."; exit 1; }

need_brew() { command -v brew >/dev/null || die "Homebrew isn't installed (https://brew.sh)."; }

check_listener() {
  say_step "Checking eLo's Alexa listener is up on port $PORT"
  if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "  ✓ listening"
  else
    echo "  ! Not listening yet. Open Presence (it starts eLo's server), then re-run this."
    echo "    The tunnel can still be set up; it will connect once the listener is up."
  fi
}

# verify_url https://host  → expects 400 (reached the listener, unsigned request refused)
verify_url() {
  local url="$1" code
  say_step "Testing $url/alexa from the internet"
  for _ in 1 2 3 4 5 6; do
    code=$(curl -s -m 10 -o /dev/null -w '%{http_code}' -X POST "$url/alexa" -d '{}')
    [ "$code" = "400" ] && { echo "  ✓ reached eLo's listener (unsigned test request correctly refused)"; return 0; }
    sleep 5
  done
  echo "  ! Got HTTP $code. Expected 400. Is Presence running? The tunnel may need a few more seconds."
  return 1
}

save_url() {
  local url="$1" env="$ELO/.env"
  cp "$env" "$env.bak-tunnel-$(date +%Y%m%d%H%M%S)"
  if grep -q '^ALEXA_TUNNEL_URL=' "$env"; then
    sed -i '' "s|^ALEXA_TUNNEL_URL=.*|ALEXA_TUNNEL_URL=$url|" "$env"
  else
    printf '\n# Alexa permanent endpoint (card 0008)\nALEXA_TUNNEL_URL=%s\n' "$url" >> "$env"
  fi
  echo "  ✓ saved ALEXA_TUNNEL_URL=$url in ~/elo-ai/.env (backup kept next to it)"
}

alexa_console_steps() {
  local url="$1"
  echo "$url/alexa" | pbcopy
  cat <<TXT

────────────────────────────────────────────────────────────
 ONE-TIME, in the Alexa developer console (endpoint is on your clipboard):
   1. DISENELO Presence → Build → Endpoint
   2. HTTPS → Default Region:  $url/alexa
   3. Certificate: "My development endpoint is a sub-domain of a domain
      that has a wildcard certificate from a certificate authority"
   4. Save
   5. Test tab → set the dropdown at the top to "Development" (NOT "Off")
   6. Type:  open elo
 This address never changes now: no more console edits after restarts.
────────────────────────────────────────────────────────────
TXT
}

# install_launchd LABEL "cmd arg arg…"  → starts at login, restarts if it dies
install_launchd() {
  local label="$1"; shift
  local plist="$HOME/Library/LaunchAgents/$label.plist" args=""
  for a in "$@"; do args="$args<string>$a</string>"; done
  mkdir -p "$HOME/Library/LaunchAgents" "$HOME/Library/Logs"
  cat > "$plist" <<PL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>$label</string>
  <key>ProgramArguments</key><array>$args</array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>$HOME/Library/Logs/$label.log</string>
  <key>StandardErrorPath</key><string>$HOME/Library/Logs/$label.log</string>
</dict></plist>
PL
  launchctl unload "$plist" 2>/dev/null
  launchctl load "$plist" && echo "  ✓ starts at login and restarts itself ($plist)"
  echo "    To stop it for good:  launchctl unload \"$plist\" && rm \"$plist\""
}

ask_yes() { local r; read -r -p "$1 [y/N] " r; [[ "$r" =~ ^[Yy] ]]; }
