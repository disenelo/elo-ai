# WO-B3-0008 — Alexa persistent tunnel (named cloudflared)

**Seat:** Builder 3  
**Priority:** P1  
**Status:** QUEUE  
**Source:** [VERIFIED] `capabilities/alexa/ALEXA_SETUP.md` §"Known limits (v1)" — "The tunnel URL changes each run unless you set up a named cloudflared tunnel." [DAVID] David set up the Alexa skill. Skill ID confirmed in `.env`. Ingress code built and wired into server.py (lines 9761-9771). What is missing is a persistent tunnel so the endpoint URL doesn't change on every restart.  
**Date added:** 2026-10-08

---

## What

Set up a named cloudflared tunnel so the Alexa skill endpoint URL is permanent. Currently the tunnel URL changes every run — meaning the Alexa developer console endpoint must be manually updated after every server restart. That makes Alexa unreliable in practice.

---

## Current state (verified)

- `ALEXA_SKILL_ID=amzn1.ask.skill.eace8b39-18f0-4a20-adb9-320ae94b4be2` — set in `.env`
- `capabilities/alexa_ingress.py` — complete, verified
- `capabilities/alexa/ALEXA_SETUP.md` — setup guide written
- `server.py` lines 9761-9771 — ingress started on server boot
- Listener: `127.0.0.1:5051/alexa`
- **Missing:** named tunnel with fixed URL registered in Alexa developer console

---

## What to build

### 1. Named cloudflared tunnel

```bash
# One-time setup (Builder 3 runs this on David's Mac):
cloudflared tunnel login
cloudflared tunnel create elo-alexa
cloudflared tunnel route dns elo-alexa <your-domain-or-trycloudflare>

# Config file: ~/.cloudflared/config.yml
tunnel: elo-alexa
credentials-file: /Users/Disenelo/.cloudflared/<tunnel-id>.json
ingress:
  - hostname: alexa.elo.local  # or whatever domain David has
    service: http://localhost:5051
  - service: http_status:404
```

If David doesn't have a domain: use `cloudflared tunnel --url http://localhost:5051 --name elo-alexa` — the URL from a named tunnel is stable across restarts even with trycloudflare.

### 2. Start tunnel on server boot

Add to the server startup script or launchd plist so `cloudflared` starts with the server and keeps the tunnel alive.

Document the fixed URL in `capabilities/alexa/ALEXA_SETUP.md`.

### 3. Register fixed URL in Alexa console

Once the fixed URL is confirmed:
- Alexa developer console → eLo skill → Endpoint
- Set to `https://<fixed-url>/alexa`
- Certificate: "My development endpoint is a sub-domain of a domain that has a wildcard certificate from a certificate authority"

Document the registered URL in `.env` as `ALEXA_TUNNEL_URL=https://...` for reference.

---

## Tests

- Start server, stop server, start server again — tunnel URL is the same both times
- Send a test request from Alexa developer console Test tab — receives valid response
- `[alexa] ingress listening on 127.0.0.1:5051/alexa` appears in server log on boot

---

## Live turn needed

David: "Alexa, open elo" → eLo responds in his voice through the Echo. Works after a server restart without touching the Alexa console.

---

## Related

- `capabilities/alexa_ingress.py` — the ingress code (complete)
- `capabilities/alexa/ALEXA_SETUP.md` — update with fixed URL once confirmed
- Builder 3 Track E in START_HERE

---
## Result (Builder 3, 2026-10-11): permanent tunnel LIVE (Tailscale Funnel)
- David signed in to Tailscale and approved Funnel; B3 ran `tailscale funnel --bg 5051`.
- Permanent endpoint: **https://davids-mac-studio.tail3da1cb.ts.net/alexa** → 127.0.0.1:5051 (Alexa-only listener). Saved as `ALEXA_TUNNEL_URL` in `.env`.
- Verified from the public route (Google DNS → Tailscale relay 176.58.90.x): `/alexa` → 400 (listener reached, unsigned refused); `/chat` → 404 (main server not exposed).
- `--bg` persists across restarts while the Tailscale app runs (it starts at login).
- Remaining for David: (1) paste the endpoint into Alexa console → Endpoint → Save (one time); (2) Tailscale admin → Machines → davids-mac-studio → Disable key expiry (currently "in 5 months"); (3) then the old cloudflared Terminal can be closed.

## LIVE VERIFIED 2026-10-11 ~23:01: Amazon reached eLo through the Tailscale endpoint (LaunchRequest accepted). Alexa console certificate option = "trusted certificate authority". The old cloudflared quick tunnel can be closed.
