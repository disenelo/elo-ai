# eLo on Alexa: setup (B3-ALEXA-INGRESS-001)

David talks to an Echo → the Alexa skill → a tunnel → eLo's `/alexa` listener on this Mac → the same brain as `/chat` → eLo's reply spoken by the Echo.

## One-time steps (David; needs an Amazon developer account, which is free)
1. Go to https://developer.amazon.com/alexa/console/ask → **Create Skill** → Custom → "Provision your own".
2. **Interaction model:** JSON Editor → paste `interaction_model.json` → Save → Build.
   - Invocation name is **`elo`** (David, 2026-10-06). One-word names are only allowed when they're the brand's own name. eLo is DISENELO's character, so say that if Amazon asks.
3. Start the tunnel, pointed at the Alexa listener port, **never at 5050**:
   `cloudflared tunnel --url http://localhost:5051`
   Copy the `https://….trycloudflare.com` URL.
4. **Endpoint:** HTTPS → `https://<tunnel>/alexa`, with the certificate option "sub-domain of a domain that has a wildcard certificate".
5. Copy the **Skill ID** (`amzn1.ask.skill.…`) into `~/elo-ai/.env`:
   `ALEXA_SKILL_ID=amzn1.ask.skill.…`
   Optionally set `ALEXA_PORT=5051` (that is the default).
6. Restart the eLo server. The log shows `[alexa] ingress listening on 127.0.0.1:5051/alexa`.
7. On the Echo: "Alexa, open elo" or "Alexa, talk to elo" → "Yo — it's eLo. What's up?"

## The phrases David wants
"Alexa, where's eLo", "Alexa, hello eLo", "Alexa, eLo", "Alexa, connect to eLo".
- **Expected to work:** "Alexa, open elo", "Alexa, talk to elo", "Alexa, ask elo where he is". These are Alexa's standard openers.
- **Not confirmed:** "Alexa, eLo", "Alexa, hello eLo", "Alexa, where's eLo", "Alexa, connect to eLo". Custom openers are Amazon's "skill launch phrases" feature, which may need a published (certified) skill. Try each in the console's **Test** tab (type them as you'd say them). Then tell Builder 3 which ones open eLo and which don't.
- **Pronunciation:** if Alexa mishears "elo" (as "hello" or "yellow"), try the invocation name `e lo` and test again.

## How it behaves
- Every request is verified: Amazon certificate URL and chain, signature over the body, timestamp within 150 s, and Skill ID. Anything else gets a 400. The listener serves `/alexa` only, so `/chat` is never reachable through the tunnel.
- Alexa allows 8 s per reply, and an eLo turn can take longer. Past about 6.5 s eLo says "Give me a sec on that — say 'go on' and I'll tell you." The finished answer comes on your next sentence.
- "Stop" / "cancel" → "Later." and the session ends.

## Known limits (v1)
- eLo's Mac voice also speaks the reply (local TTS has no per-turn mute; that belongs to the voice/runtime owner).
- The tunnel URL changes each run unless you set up a named cloudflared tunnel.
