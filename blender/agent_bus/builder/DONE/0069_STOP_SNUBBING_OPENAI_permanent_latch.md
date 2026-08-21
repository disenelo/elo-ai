# 0069 — OpenAI is permanently snubbed after one 429. David says don't snub.

**Seat:** builder · **Priority:** P2 · **Reserved?** no
**STATE: AUTHORISED — implements David's decision 2026-08-21**

> **David:** *"Until I get OpenAI Groq and Gemini working again -- do not snub them out we are just going to
> use what is available which allows for us to feel out fail safes"*

## The fault
`backend_router.py:1014-1018` — a single 429 sets `_openai_quota_exceeded = True` and OpenAI is skipped for
the **rest of the session**. No retry, no recovery, and **the path is never exercised again** — which is
exactly the opposite of "feel out the failsafes."

## The fix already exists in the same file — copy it, don't invent one
`WO-032b` solved this for Groq: `_groq_quota_cooldown_until`, a **60-second cooldown that clears on
success** (`:215`, `:929-932`). Give OpenAI and Gemini the same treatment.
🔴 **Same pattern, same duration, same clear-on-success. Do not design a new backoff.**

## Scope
1. `_openai_quota_exceeded` (bool) → `_openai_quota_cooldown_until` (timestamp), mirroring Groq.
2. Clear it on a successful call, as Groq does.
3. Check Gemini for the same latch; give it the same treatment if present.
4. Confirm `_fh_degraded("reasoning", ...)` does not itself suppress a retry — **degraded must mean
   "reported", not "removed".**
5. 🔴 **Do not remove any provider from any chain**, however unreachable it currently is.

## Test — `tests/test_no_permanent_backend_snub.py`
1. A 429 does **not** permanently disable OpenAI — after the cooldown it is retried. **RED today.**
2. A success clears the cooldown.
3. **No provider is ever removed from `_TIER_PROVIDER_ORDER` or the auto chain at runtime.**
4. With every cloud key invalid, eLo still answers (Ollama floor) **and every cloud provider was attempted at
   least once** — that is the failsafe actually being felt out.

## Done when
Committed · tests green · a run with all cloud keys dead shows each provider attempted, then Ollama serving.

## Result
- commit: · openai latch → cooldown:
- gemini checked:
- providers attempted per turn with dead keys:
