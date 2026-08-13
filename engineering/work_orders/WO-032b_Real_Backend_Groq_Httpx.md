# WO-032b — Real backend via Groq (httpx direct), retire the dumb mock

**Owner:** Builder (eLo OS) · **Priority:** P0 (Tier 0 — unblocks all conversation judgement).
**Status:** OPEN — spec'd 2026-08-07. **NO DAVID ACTION NEEDED — the key is already present.**
Verified in `.env` 2026-08-07: `GROQ_API_KEY` set (56 chars), `ELO_BACKEND=groq` pinned,
`ELO_GROQ_MODEL=llama-3.3-70b-versatile`. The fall-to-mock is a CODE issue, not a missing key.
**Canon:** ADR-Exec-001 (never a false claim) · Reality Before Narrative (the mock's flat/hallucinated
output is why "how's the company" invented "Company for Doing" on 2026-08-07).

## Problem (root causes — key is NOT one of them)
`ELO_BACKEND=groq` with a valid key present, yet the transcript fell to `MockBackend` (flat, mirrors,
invents). Two code causes:
1. **Groq SDK not installed** in the runtime → the SDK-based Groq path fails to initialise → drops to mock.
2. **Stale 429 flag:** `_groq_quota_exceeded` (backend_router.py:90) is set on the first Groq 429 and, per
   its own comment, is NOT cleared until a process restart — so one transient rate-limit pins the whole
   session to mock. Must clear on recovery (e.g. time-boxed retry), not stay latched.

## Scope (FULL build — not a half)
1. **Groq via httpx direct call** (no SDK dependency): implement a `GroqBackend` in the `backend_router`
   that POSTs to Groq's OpenAI-compatible chat endpoint using `httpx`, reading `GROQ_API_KEY` from env.
2. **Make it primary:** `ELO_BACKEND=groq` pins it; router order = Groq → (optional OpenAI if billed) →
   local fallback → mock as last resort only.
3. **Local fallback tier (retire the dumb mock as the default fallback):** if a local model endpoint is
   configured (e.g. Ollama on `localhost:11434`), use it before the mock. Mock stays only as the
   absolute last resort, and when it's used, `backend_health.json` + the honest degraded line still fire
   (existing WO-032 Part B gate at `server.py:2939` — keep it).
4. **Config surface:** document the two env vars (`GROQ_API_KEY`, optional local endpoint) in one place.

## Definition of Done (the WHOLE thing works)
- With `GROQ_API_KEY` set: a normal chat turn returns a real Groq completion; `backend_used == "groq"`
  (NOT `mock`); the honest-degraded line does NOT fire.
- With the key unset but a local endpoint up: `backend_used` == local; still not mock.
- With neither: mock + honest degraded line (unchanged) — no silent false confidence.
- eLo's voice reads as eLo on the real backend (no personality drift — ties WO-026 unification).

## Test — WITHOUT David (`tests/test_wo032b_groq_backend.py`)
- Monkeypatch/stub the httpx POST → assert `GroqBackend` builds the right request (endpoint, auth header,
  model, messages) and parses the completion; `active_backend()`/`backend_used` reports `groq`.
- Router order test: with `GROQ_API_KEY` present → groq chosen; absent + local stub → local; neither → mock
  AND `_bh_degraded` path fires. (No real network call in the test — stub the transport.)
- Existing `test_wo032_*` (health, pinned, false-degraded) still green.

David L3: talk to eLo on the real backend — it sounds like eLo, not the understudy.
Refs: `runtime/backend_router.py` · `backends/mock_backend.py` · `server.py:2933-2954` (health + degraded gate).
