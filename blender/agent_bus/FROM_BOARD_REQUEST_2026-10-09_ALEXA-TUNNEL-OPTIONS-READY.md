# Alexa permanent tunnel — all three options READY TO RUN (Builder 3 → Board / David, 2026-10-09)

Scripts: `capabilities/alexa/tunnel/` (commit c8077b3). David's one-page sheet: `MORNING.md` (copy on his Desktop: `eLo_Alexa_MORNING.md`).
David double-clicks ONE `.command`. It asks only for the strings it can't know, then runs end to end.

## ⚠️ Two corrections to the overnight brief (safety)
- **Port is 5051, never 5050.** 5050 is eLo's main server (`/chat`, everything). Exposing it would let anyone on the internet drive eLo. 5051 is the Alexa-only listener: `/alexa` plus its own short-lived voice clips, and Amazon-signed requests for this skill only. All three scripts use 5051.
- **Path is `/alexa`**, not `/api/alexa`. No handler update is needed; the listener already serves `/alexa`.

## Step 0 (before any option): Test tab
Alexa console → DISENELO Presence → **Test** → dropdown = **Development** (not Off) → type `open elo`. Most likely reason nothing reached eLo after the 16:05 restart.

## Option 1: ngrok (simplest) · `option1_ngrok.command`
David provides: **authtoken** + **free static domain** (dashboard.ngrok.com → Your Authtoken; Domains → claim).
Script: `brew install ngrok` if missing → `ngrok config add-authtoken <token>` → launchd `com.disenelo.elo-alexa-tunnel` running `ngrok http --url=<domain> 5051` (start at login, KeepAlive; asks y/N) → verify `https://<domain>/alexa` from the internet (expects 400 = listener reached, unsigned refused) → `ALEXA_TUNNEL_URL` saved in `.env` (backup) → endpoint copied to clipboard + console steps printed.
David approves: running the file; "start at login" (y/N).

## Option 2: Cloudflare named tunnel (most robust) · `option2_cloudflare.command`
David provides: a hostname on a domain **Cloudflare manages** (disenelo.com's DNS is at Oracle Cloud, so a spare/new domain is needed), e.g. `alexa.<domain>`.
Script: `brew install cloudflared` → `cloudflared tunnel login` (**browser: David picks the domain → Authorize**) → `cloudflared tunnel create elo-alexa` → `cloudflared tunnel route dns elo-alexa <host>` (creates the CNAME) → `~/.cloudflared/elo-alexa.yml` forwarding **only `^/alexa`** to 127.0.0.1:5051, everything else 404 → launchd (y/N) `cloudflared tunnel --config … run elo-alexa` → verify → save → console steps.
David approves: browser authorisation; "start at login".

## Option 3: Tailscale Funnel · `option3_tailscale.command`
David provides: Tailscale sign-in (the app opens; the script waits).
Script: `brew install --cask tailscale` if missing → sign-in → `tailscale funnel --bg 5051` (persists across restarts; Tailscale starts at login) → if Funnel isn't allowed yet, prints Tailscale's approval link and waits → reads `<mac>.<tailnet>.ts.net` → verify → save → console steps.
David approves: Tailscale sign-in; Funnel permission link.

## Common to all
- Endpoint to paste: `https://<fixed-host>/alexa`, certificate "sub-domain of a domain that has a wildcard certificate". Then Save, Test = Development.
- After that the address survives restarts. Last night's quick-tunnel Terminal can be closed.
- Checked: `bash -n` on all four files; the shared listener + internet check passed against the live quick tunnel. The options themselves are not run (David's accounts).
