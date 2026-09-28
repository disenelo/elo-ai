# FROM BUILDER → BOARD — WO-MODEL-ROUTING-001 — PLAN PATH BLOCKED
**Date:** 2026-09-14
**WO:** WO-MODEL-ROUTING-001 — content-driven model routing
**Path:** PLAN — OpenAI — BLOCKED

---

## Status

PLAN path cannot be tested. OpenAI account has no credits.

`_openai_call()` returns HTTP 429 / quota error on every attempt. The PLAN routing block in `backend_router.py` is correctly implemented — the code path exists, `_openai_available()` returns True (key is valid), but the API rejects inference requests.

## DoD status

| Path | Status |
|---|---|
| LOCAL | SERVING — result card filed |
| FAST | SERVING — result card filed |
| DEEP | SERVING — result card filed |
| PLAN | BLOCKED — OpenAI no credits |

## What Board needs to decide

One of:
1. Add OpenAI credits → Builder runs a PLAN-routed turn (`"How should I approach X"` input) and files the fourth card.
2. Authorise a PLAN substitute (e.g. Claude via `ANTHROPIC_API_KEY` already in `.env`) → Builder updates `_plan_call()` to use the substitute and retests.
3. Accept three of four paths as DoD pass for this WO, mark PLAN as a follow-on work order.

The PLAN code path in `backend_router.py` is wired and ready. Waiting on authorisation to either credit the account or substitute the model.

---
*Builder · 2026-09-14*
