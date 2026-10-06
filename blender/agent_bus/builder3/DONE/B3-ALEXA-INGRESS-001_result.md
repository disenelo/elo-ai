# Result — B3-ALEXA-INGRESS-001 · Job 4 Alexa ingress
**Seat:** Builder 3 · **Date:** 2026-10-06 · **Commit:** `bb92463`
**Status: BLOCKED.** The external dependency is an Amazon developer account and custom skill. The steps are David's, in `capabilities/alexa/ALEXA_SETUP.md` steps 1–5.
- The Mac side is built and wiring-tested.
- No real Alexa request has been received, so nothing is claimed as serving.

## Built
**`capabilities/alexa_ingress.py`**
- Its own listener at `127.0.0.1:5051`, serving `POST /alexa` only. It starts only when `ALEXA_SKILL_ID` is set. The tunnel never exposes `/chat`.
- Verification, all required:
  - echo.api cert URL rules;
  - chain to a trusted root, SAN `echo-api.amazon.com`;
  - Signature-256 over the raw body;
  - timestamp within ±150 s;
  - applicationId = `ALEXA_SKILL_ID`.
- Launch / Talk / Stop / Help. Talk runs the same queued turn plus `_condition_outbound` as `/chat`.
- 8 s limit: past 6.5 s eLo says "Give me a sec on that — say 'go on' and I'll tell you". The answer comes on the next utterance.

**`server.py`** — startup hook after the main server.

**`capabilities/alexa/`** — `interaction_model.json` (invocation name `elo buddy` is a **[PROPOSAL]**) and `ALEXA_SETUP.md`.

## Tests (wiring, not live evidence)
`tests/test_b3_alexa_ingress.py`: 21 passed.
- Correct signature accepted.
- Refused: tampered body, wrong skill, stale timestamp, missing headers, 6 bad cert URLs, untrusted self-signed chain.
- Handler flows covered, including held-then-delivered.

Real Amazon chain `echo-api-cert-12.pem`:
- refused today (expired 2023-12-23);
- **verified** at an in-validity date (path length 3);
- refused under a wrong hostname.

## Open
1. **Phase gate.** `PROJECT_STATE.md` lists "P3 — Alexa vertical slice" as gated on P2 acceptance. START_HERE (David L3, 2026-10-05) commissions this job. Built per START_HERE; the Board should reconcile.
2. **Duplicate audio.** An Alexa turn also speaks through the Mac's local TTS, because `voice.voice_engine.speak` has no per-turn mute. Owner: voice / runtime (Builder 1).
