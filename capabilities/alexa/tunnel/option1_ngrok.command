#!/bin/bash
# OPTION 1 — ngrok free static domain (simplest). B3, card 0008.
# Before running: sign up free at https://dashboard.ngrok.com/signup
#   → "Your Authtoken" (copy it) and → Domains → claim your free static domain.
cd "$(dirname "$0")" && source ./common.sh
echo "eLo · Alexa permanent tunnel · OPTION 1: ngrok"
need_brew
if ! command -v ngrok >/dev/null; then say_step "Installing ngrok"; brew install ngrok || die "ngrok install failed"; fi
check_listener
read -r -p "Paste your ngrok authtoken: " TOKEN;  [ -n "$TOKEN" ]  || die "No authtoken given."
read -r -p "Paste your static domain (e.g. something-calm.ngrok-free.app): " DOMAIN
DOMAIN="${DOMAIN#https://}"; DOMAIN="${DOMAIN%/}"; [ -n "$DOMAIN" ] || die "No domain given."
say_step "Saving the authtoken in ngrok's own config"
ngrok config add-authtoken "$TOKEN" >/dev/null || die "ngrok rejected the authtoken."
URL="https://$DOMAIN"
NGROK="$(command -v ngrok)"
if ask_yes "Start it at login and keep it running (recommended)?"; then
  install_launchd com.disenelo.elo-alexa-tunnel "$NGROK" http "--url=$DOMAIN" "$PORT" --log=stdout
else
  say_step "Starting ngrok in the background for this session"
  nohup "$NGROK" http "--url=$DOMAIN" "$PORT" --log=stdout > "$HOME/Library/Logs/elo-alexa-ngrok.log" 2>&1 &
fi
sleep 4
verify_url "$URL"
save_url "$URL"
alexa_console_steps "$URL"
read -r -p "Done. Press Enter to close."
