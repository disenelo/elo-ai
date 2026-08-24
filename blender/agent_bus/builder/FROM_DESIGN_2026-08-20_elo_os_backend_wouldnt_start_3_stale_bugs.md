# FROM DESIGN (SEAT-ENG-004) → BUILDER (SEAT-ENG-001) — 2026-08-20 — eLo OS backend could not start (3 stale bugs) — minimal fixes applied to unblock a live request, UNCOMMITTED, your call

**Context:** David asked me to fire up DISENELO Presence. The Unity app auto-launches the brain itself — `EloOSProcess.cs` (WO-065) spawns `~/miniconda3/bin/python -u server.py` in `~/elo-ai` on every app launch, kills any stale :5050 first, and kills the server on app close. **So auto-start is already built and working.** The brain only *looked* absent because the server it spawned **crashed instantly on import every single launch** since commit `ba03271` — so each app open produced a dead process. I applied the **minimal** fixes to the crash. These are in YOUR lane (eLo OS Python core) — flagging so you own them and decide on committing. I did NOT commit (the elo-ai tree has heavy unrelated agent_bus churn; not mine to bundle).

> **CORRECTION (same note, later in the session):** an earlier draft of this note said "this build has no EloOSLauncher, so the app doesn't auto-start the backend — start it manually." **That was wrong** — `EloOSProcess.cs` is the launcher and it works. The only defect was the crash-on-import below. Verified the fix boots clean under the app's actual python (miniconda 3.13): `/ping` ok, `/chat` returns real turns. Nothing manual is required — closing and reopening the app now loads the backend.

## Bug 1 + 2 — stale `core.attention` import (BOTH entrypoints dead)
Commit `ba03271` (WO-CANON-VI, Ruling B) renamed `core/attention.py` → `core/memory_relevance_filter.py`, but two entrypoints still imported the old name:
- `server.py:55` — `from core import attention as attn`
- `main.py:50` — `from core import attention as attn`
→ `ImportError: cannot import name 'attention' from 'core'`. **eLo OS has been unable to start from either entrypoint since ba03271.**

**Fix applied (minimal, API-verified):** changed both to `from core import memory_relevance_filter as attn`. I kept the `as attn` alias so every downstream `attn.compute(...)` and all `attention_model` locals are unchanged. Verified `core/memory_relevance_filter.py:229` still exposes `compute(...)` — the only module attribute either file uses (grep-confirmed: `attn.compute` at server.py:2546, main.py:216; everything else named "attention" is local vars/strings). Runtime-proven: a real `/chat` turn now completes ("Always here.").

## Bug 3 — ack-poller thread NameError
`server.py:1649` — `_poller_log = logging.getLogger(...)` but the module imports `logging as _logging` (line 45). Bare `logging` is undefined → the `_poll_unity_events` thread dies at startup with `NameError: name 'logging' is not defined`. Effect: Unity→backend event acks (nav/exit events from `_UNITY_EVENTS_PATH`) were never consumed — a silent degradation of the desktop loop; core chat/voice/animation were unaffected.

**Fix applied:** `logging.getLogger` → `_logging.getLogger`. Matches the line-45 import.

## Lifecycle (already correct — recording for clarity, no action)
`EloOSProcess.cs` owns it: `EnsureServerCo` checks `IsPortOpen(5050)`; if nothing's there it spawns `~/miniconda3/bin/python -u server.py` (cwd `~/elo-ai`, `DESKTOP_AVATAR=0`); on app close `OnDisable` kills the server it launched. `server.py:4912-4913`'s `_watch_parent` (getppid + `os.kill(ppid,0)`) means the brain is tied to its parent — which BY DESIGN is the app, so the brain lives exactly as long as the app. That's correct, not a bug. (`main.py` is the separate terminal REPL a human runs by hand; the app never touches it.) My earlier manual `( nohup … & )` launch was only a bring-up/test workaround while the import crash was unfixed — it is NOT needed now; the app handles it.

## OBSERVED (corrected — NOT a defect)
`/status` reports `backend: groq`; turns ran `ollama(stream)`. An earlier draft called this a "fallback from GPT-4o-mini primary" — **David has since confirmed LOCAL (Ollama) is the intended PRIMARY for speed, with the other backends called via the system as needed.** So local-first is correct behaviour, not a fallback problem. The `[eLo vision] OpenAI quota hit — backing off 60s` line is consistent with that (local-first, remote only when needed). No action; this is your One-Brain router lane, working as intended.

## One decision for you
Commit the 3 fixes? (I left them uncommitted in your repo — minimal + drop-in-verified, boots clean under miniconda 3.13.) Auto-start already works via `EloOSProcess` — nothing to build there.

— SEAT-ENG-004 (Design)
