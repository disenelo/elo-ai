#!/bin/bash
# OPTION 2 — Cloudflare named tunnel (most robust). B3, card 0008.
# Needs: a free Cloudflare account with a domain on it (Cloudflare manages its DNS).
# disenelo.com's DNS is at Oracle Cloud, so either move a spare domain to Cloudflare
# first, or add a new one. This script uses a sub-domain like alexa.<your-domain>.
cd "$(dirname "$0")" && source ./common.sh
echo "eLo · Alexa permanent tunnel · OPTION 2: Cloudflare named tunnel"
need_brew
command -v cloudflared >/dev/null || { say_step "Installing cloudflared"; brew install cloudflared || die "install failed"; }
check_listener
read -r -p "Hostname to use (e.g. alexa.yourdomain.com — the domain must be on Cloudflare): " HOST
HOST="${HOST#https://}"; HOST="${HOST%/}"; [ -n "$HOST" ] || die "No hostname given."
if [ ! -f "$HOME/.cloudflared/cert.pem" ]; then
  say_step "Log in to Cloudflare (a browser window opens — pick the domain, Authorize)"
  cloudflared tunnel login || die "Cloudflare login failed."
fi
NAME=elo-alexa
if ! cloudflared tunnel info "$NAME" >/dev/null 2>&1; then
  say_step "Creating tunnel '$NAME'"; cloudflared tunnel create "$NAME" || die "create failed"
fi
ID=$(cloudflared tunnel info "$NAME" 2>/dev/null | awk '/^ID:/{print $2}')
[ -n "$ID" ] || ID=$(cloudflared tunnel list 2>/dev/null | awk -v n="$NAME" '$2==n{print $1}')
[ -n "$ID" ] || die "Couldn't read the tunnel ID."
say_step "Pointing $HOST at the tunnel"
cloudflared tunnel route dns "$NAME" "$HOST" || echo "  (route may already exist — continuing)"
CFG="$HOME/.cloudflared/elo-alexa.yml"
cat > "$CFG" <<YML
tunnel: $ID
credentials-file: $HOME/.cloudflared/$ID.json
ingress:
  - hostname: $HOST
    path: ^/alexa
    service: http://127.0.0.1:$PORT
  - service: http_status:404
YML
echo "  ✓ config $CFG (only /alexa is forwarded)"
CF="$(command -v cloudflared)"
if ask_yes "Start it at login and keep it running (recommended)?"; then
  install_launchd com.disenelo.elo-alexa-tunnel "$CF" tunnel --config "$CFG" run "$NAME"
else
  nohup "$CF" tunnel --config "$CFG" run "$NAME" > "$HOME/Library/Logs/elo-alexa-cloudflared.log" 2>&1 &
fi
sleep 6
URL="https://$HOST"
verify_url "$URL"
save_url "$URL"
alexa_console_steps "$URL"
echo "Note: you can now close the old quick-tunnel Terminal window (the trycloudflare one)."
read -r -p "Done. Press Enter to close."
