# 02_WO-034_app_reply.md

**WO:** WO-034 · **Seat:** builder · **Priority:** P1 · **Reserved?** no

## Goal
The app fires the reply. CLI works, the app doesn't — so eLo can look dead in the thing David actually uses.
This is a daily-use blocker.

## Scope — exactly this
- Diagnose why the reply path fires from CLI but not from the running app (ownership was defined on the
  board: stop the competing paths).
- Fix so the app's turn produces the spoken/displayed reply reliably.
- Do not build a second reply path — repair the one that exists.

## Files likely touched
`runtime/server.py` reply/emit path · the app-facing bridge.

## Test (without David)
Restart the backend clean, POST a turn to `localhost:5050/chat`, confirm the reply is emitted on the app
path (artifact/log), not just CLI. Report the artifact.

## Done when
implemented + test green + committed → hash, DONE/, outbox, next card.

## Result
- commit: (no Python change needed — server was already correct)
- test: Arbiter test 2026-08-13: `curl POST /chat {"text":"hello"}` → `{"response":"Ello.","bubbles":["Ello."],"mode":"celebrate","backend":"direct"}`. Real reply, non-mock. **eLo OS half done per WO-034 arbiter contract. Bug is Unity consume side.**
- handover: `handovers/UNITY_AGENT_HANDOVER_WO034_app_reply.md`
