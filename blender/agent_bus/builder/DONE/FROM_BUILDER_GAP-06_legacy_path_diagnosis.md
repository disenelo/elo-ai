# FROM BUILDER — GAP-06: Legacy Path Diagnosis (Step 1)

**Date:** 2026-09-11
**Status:** STEP 1 COMPLETE — diagnosis filed; Step 3 retirement blocked on server evidence

---

## Legacy paths found in server.py

### Primary legacy path: exec_decide() fallback (line 3135)

```
SPINE PATH (normal):     server.py:3029-3035 → spine.run() → plan → exec_decision dict
LEGACY FALLBACK:         server.py:3128-3135 → exec_decide(attention_model) directly
```

**When it fires:** Only when `spine.run()` throws an exception. In normal operation, spine always succeeds.

**Current state:** Already gated. Error log fires when legacy path activates:
```
_logging.error("GAP-06 LEGACY PATH ACTIVE — spine failed, falling back to exec_decide(). "
               "This turn bypasses One Brain. Investigate spine failure.")
```

Comment at line 3132: "Board ruling: keep as narrow exception safety net." — this aligns with GAP-06 Step 2 requirement: "confirm One Brain equivalent is live before retiring." The Board ruling embedded in the code suggests this was deliberate.

**Retirement status:** NOT retired — kept as safety net per embedded Board ruling. Needs explicit Board confirmation to fully remove.

### Secondary legacy path: direct exec_decide at line 3135

Same path — exec_decide is the "last resort" when spine fails. Bypasses Capability Faculty, Environment Faculty, Embodiment Publisher.

### Tool routing: already on One Brain path

`server.py:4558-4564` — `_tool_enrich_from_plan(raw, _plan_caps)` uses `_plan.capabilities` (set by spine's Capability Faculty). Legacy direct tool_router keyword-matching runs only when `_plan_caps` is empty AND gatekeeper agrees on conversation — that is correct behaviour per D8 ruling.

### Blender writes: state_writer.py is used

`server.py:1265` — `from blender_bridge.state_writer import patch as _bpatch` — the Embodiment Publisher. Not legacy.

---

## Step 2 result

One Brain equivalents confirmed live (from backend_health.json + code inspection):
- ✅ Capability Faculty (spine → plan.capabilities → _plan_caps)
- ✅ Executive (spine._executive_faculty via exec_decide inside spine)
- ✅ Embodiment Publisher (state_writer.patch)
- ✅ Environment Faculty (world model in spine.run())

---

## Step 3: retirement blocked

Cannot retire the `exec_decide()` safety fallback without:
1. Board explicit confirmation (overrides embedded "Board ruling: keep as narrow exception safety net" comment)
2. 5-turn real server run confirming spine never fails

Step 4 (server run) requires David's server to be running — pending restart.

*Builder · 2026-09-11*
