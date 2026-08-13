---
id: WO-032
title: "LLM backend down — eLo silently serving MockBackend canned lines for every conversational turn"
owner_seat: SEAT-ENG-001 (Builder)
occupant: Builder (Python)
priority: P0
reason: "Live incident (David 2026-08-02): every conversational reply is generic ('That sounds like a good move', 'the beginning of something', 'Keep what resonates'). Confirmed = MockBackend fallback (prompt_builder FORBIDS the real LLM from these phrases). The real model is producing NOTHING; only canned greeting pool / weather tool / mock are answering. Backend chain is failing to all cloud providers → _mock_fallback."
review_required: L1 → L3 (David confirms real replies live)
risk: ops + code — this is why eLo 'works but is hollow'
status: DISPATCHED → Builder (David relayed the diagnosis 2026-08-02)
created: 2026-08-02
---

# WO-032 — LLM backend down (silent mock fallback)

## Diagnosis (grounded)
- `runtime/backend_router.route()` chain: OpenAI → Gemini → Groq/Cerebras → Claude → `_mock_fallback`.
- `.env`: OPENAI_API_KEY present (164ch), CEREBRAS present; ANTHROPIC/GEMINI empty. `ELO_BACKEND` unset → "auto".
- Every conversational turn returns MockBackend text → **all cloud calls are failing** (invalid/expired
  key, quota/billing, OR outbound network breaking HTTPS — same fault sending weather to random South
  American cities).
- **Silent failure is the real danger:** eLo *looks* like it's working (canned affirmations + greeting
  pool + weather tool all answer) so the outage is invisible. David couldn't tell it was degraded.

## Fix
### A. Restore the cloud LLM (the outage)
1. Verify the OpenAI key live: `curl -s -o /dev/null -w "%{http_code}" https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY"`.
   - 401 → key invalid/expired → new key. 429 → out of credit/quota → add billing. 200 → key fine, chase network.
2. If network: check outbound HTTPS works and `curl https://ipinfo.io/country` isn't returning AR/PY/BR
   (traffic exiting through South America would break both API auth and weather geolocation).
3. Confirm a real backend answers: after fix, a plain "how are you" gives a non-canned, contextual reply.

### B. Make degradation VISIBLE (so a silent outage never fools us again)
1. When the chain falls to `_mock_fallback`, **flag it**: set a `backend_health` field (live backend name
   or `MOCK`) into `blender/company_state.json` / a trace, so the dashboard shows **"LLM: MOCK ⚠"**.
2. eLo should NOT pass off mock lines as normal conversation when the model is down — either say it plainly
   ("I can't reach my thinking right now — running on backup") or visibly mark degraded mode. Silent
   canned affirmations that impersonate real replies are the bug that hid this for hours.
3. Optional: a lightweight startup + periodic backend health-check that logs which providers are reachable.

## Acceptance
1. A plain conversational turn returns a real, contextual LLM reply (not a mock affirmation).
2. Kill the key on purpose → eLo/ dashboard clearly shows degraded/MOCK, does NOT silently fake replies.
3. `backend_health` visible in state + dashboard. py_compile clean. David confirms live.

---

## ROOT-CAUSE ELEVATION (Architect, 2026-08-03) — this is bigger than "visibility"

Live `backend_health.json` = `{backend: cerebras, expected: openai, degraded: false}`.
Primary (OpenAI) has been out of quota since ~Jul 25, so **eLo runs on the Cerebras backup
full-time.** From a long live transcript (David 2026-08-03), the backup causes TWO distinct harms:

1. **VOICE CHANGE (the important one).** The backup model speaks in a different voice —
   heavy reflective mirroring ("I notice you…", "I hear you…") on nearly every turn. David:
   "it's not formed in the way you normally speak, as if there is another thing pushing your
   chat." His ear is correct — the personality shift IS a model shift, not a router/prompt bug.
   **VERIFIED NOT THE ROUTER:** behaviour_eval GS-ROUTE-01/02/03/04 all PASS — the CAL decide()
   routes casual/factual to ANSWER correctly. So do NOT "fix the router." The over-reflection is
   the backup model's voice (+ the REFLECT/CONNECT prompt directives → see WO-036).
2. **INTERMITTENT HARD-FAIL.** ~6 turns returned "Can't reach my thinking — running on backup,
   give me a sec" — the fallback itself fails some turns even though Cerebras is generally up.

### Fix direction (Builder) — pick ONE stable path, tune voice:
- Either restore a primary (David's call on OpenAI credit — he's said optional), OR
- **Pin a chosen, voice-matched backup as the de-facto primary** (Groq llama-3.3-70b or Cerebras),
  tuned to eLo's intended voice, so the voice is CONSISTENT and doesn't drift model-to-model.
- Fix the per-turn hard-fail: a failed provider call must fall through to the next live provider,
  not return the "can't reach my thinking" line while other providers are up.
- Keep "running on backup" honesty, but it should be RARE, not every third turn.

### Acceptance (add)
1. eLo's voice is consistent turn-to-turn (no model-driven personality drift).
2. "Can't reach my thinking" appears only if EVERY provider truly fails, not intermittently.
