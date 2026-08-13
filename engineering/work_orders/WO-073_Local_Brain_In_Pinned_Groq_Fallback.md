# WO-073 — Local brain in the pinned-Groq fallback (eLo never goes mute)

**Owner:** Builder (eLo OS). **Priority:** DOWNGRADED P0→P2 (2026-08-08). **Status:** SYMPTOM RESOLVED IN
PRACTICE — remaining = confirm routing + diagnose Groq.
> **David live 2026-08-08:** the local `llama3.1:8b` is now serving — latest transcript had NO "running on
> backup" and coherent replies. So eLo has a working brain and the mute-mock is no longer happening. The
> Architect's earlier "THE gate blocking everything" framing was OVER-WEIGHTED — with a local model in the
> path, the practical blocker is gone. **Live L3 tests are now VALID (real brain).** REMAINING (P2, not a
> gate): (a) confirm HOW it's reaching llama — is the pinned-Groq fallback actually wired to Ollama, or is
> `ELO_BACKEND` set to auto/local? make it intentional, not luck; (b) the Groq live-failure diagnosis (is
> Groq even being tried, or straight to local — and is that fine since local covers it?). Original spec below.
**Canon:** the understudy should THINK when cloud is down, not go dark (Vision Spine "eLo always has a brain";
ADR-Exec-001 honesty — silence over nonsense, but a real local answer beats both).

## Problem (verified in code + live)
`ELO_BACKEND=groq` (pinned, in `.env`). Router `mode == "groq"` (backend_router.py:490–528) falls through
**Groq → Cerebras → Mock**. **Ollama is NOT in this chain** — it only appears in `auto` mode (line 530). So
when Groq + Cerebras both fail, eLo drops straight to the canned mock, SKIPPING the installed Ollama local
brain. Confirmed live: L3 tests 2026-08-07 (fresh WO-065 build, server PID 90699, restart-on-launch OK) still
showed ~6× "running on backup" → Groq failing + no local floor.
**Correction on WO-032b:** its 12/12 AT STUBBED the transport → it proved request-building, NOT live Groq
reachability. Real connectivity was never tested and is currently failing (likely 429/quota).

## Scope
1. **Add Ollama to the pinned-Groq fallback:** `Groq → Cerebras → Ollama → Mock`. Insert the `_ollama_available()`
   → `_ollama_call()` tier BEFORE `_mock_fallback` in the `mode == "groq"` block. Keeps voice consistency (still
   NO OpenAI/Gemini/Claude in pinned mode — no drift), but gives a real local brain floor.
2. **Diagnose the live Groq failure (seat, on the running instance):** read `backend_health.json` (it records
   the degrade reason) + make ONE real Groq call → capture the actual error: 429 (quota/rate-limit) vs 401/403
   (auth/key) vs network. Report which. If 429/quota → confirmed cause; the Ollama floor now covers it.
3. **Confirm Ollama serves the configured model.** David has **`llama3.1:8b`** pulled (told the Builder,
   2026-08-08) — NOT `mistral` (the router default). So **set `ELO_OLLAMA_MODEL=llama3.1:8b` in `.env`** (or
   change the router default) or the Ollama tier calls a model that isn't there and still misses. Verify the
   tier actually answers, not just responds to `/api/tags`.

## Definition of Done
With Groq unreachable (429/down) in pinned mode, eLo answers from Ollama (real local brain), NOT the mock —
so "running on backup / can't reach my thinking" only appears if BOTH Groq/Cerebras AND Ollama are down.
`backend_used` reports `ollama` in that case, not `mock`.

## Test — WITHOUT David (`tests/test_wo073_pinned_ollama_fallback.py`)
- Pinned mode, Groq stubbed to raise 429 + Cerebras stubbed to fail + Ollama stubbed available → `route()`
  returns `("...","ollama")`, NOT `mock`. (Currently returns `mock` — that's the bug this WO fixes.)
- Groq succeeds → still returns `groq` (no regression; local tier not used when cloud works).
- All three down → `mock` + honest degraded line (unchanged).
- Existing `test_wo032b_groq_backend.py` still green.

## Lane
Builder only (Python — `backend_router.py`). Small, high-leverage: it's the difference between eLo going mute
and eLo having a free local brain whenever the cloud hiccups.
