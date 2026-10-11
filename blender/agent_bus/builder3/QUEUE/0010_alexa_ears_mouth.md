# WO-B3-0010 — Alexa: eLo's Ears + Mouth
**Seat:** Builder 3  
**Priority:** P0 — demo milestone end of October  
**Source:** `docs/architecture/_intake/SOURCE_DEMO-MILESTONE_2026-10-10.md` [DAVID verbatim: "Giving eLo Ears and Mouth via Alexa"]  
**Date:** 2026-10-10

---

## What

Alexa gives eLo bidirectional audio:
- **Ears** — voice input from Alexa microphone reaches eLo's server
- **Mouth** — eLo's text response is spoken back through the Alexa speaker

---

## Dependency

Tunnel must be live first. David picks one of three options from `capabilities/alexa/tunnel/`. Scripts are ready. Morning sheet is on Desktop (`eLo_Alexa_MORNING.md`). Also confirm Alexa console → Test tab is set to Development (not Off).

**This card cannot start until tunnel is confirmed live.**

Once David picks the tunnel, Builder 3 runs the setup script, verifies tunnel is reachable, then proceeds.

---

## How

**Ears (voice → eLo):**
- Alexa skill receives voice utterance → sends text to eLo's tunnel endpoint
- eLo processes as normal turn

**Mouth (eLo → voice):**
- eLo response text → Alexa TTS via `alexa_agent.py`
- Keep responses short for voice — no markdown, no lists, plain sentences
- Add voice-mode flag: `response_mode: voice` → prompt builder trims verbosity

---

## Done when

David speaks to Alexa → eLo responds through the speaker. Board tests 3 voice turns. Confirm round-trip latency is acceptable (target under 8s end-to-end).

File to Board for sign-off.

---
## LIVE VERIFIED (2026-10-11 ~23:01, David heard it)
- David → Alexa (Test tab / Echo) "open elo" → permanent Tailscale endpoint → eLo's listener → brain → reply **played on the Echo in eLo's own ElevenLabs voice** (log: `voice on echo (Alexa input)`). Mac's own output stayed on Mac Studio Speakers.
- eLo: "Hello David, good to see you again. How's your day been?"
- Timing: ~20 s from David's words to eLo's voice, of which the model took 19.4 s (mistral-nemo:12b). Latency = B1 (backend/prompt).
- Fixes that day: endpoint certificate option must be "trusted certificate authority" for the Tailscale address (exact-name Let's Encrypt cert, not wildcard); invocation stays "elo".
- Ready for Board sign-off on ears + mouth. Open: latency (B1); Designer setting UI.
