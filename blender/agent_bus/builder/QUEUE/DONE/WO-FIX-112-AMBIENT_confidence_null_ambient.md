# BUILDER QUEUE — WO-FIX-112-AMBIENT

**From:** Board / Lead Architect — 2026-08-28
**Priority:** P2
**Full WO:** `engineering/work_orders/WO-FIX-112-AMBIENT.md`

---

## What to do

Fix `confidence: null` on ambient/bypass journal entries in `server.py`.

**The change:** At `server.py:1033-1037` (ambient daemon journal call), add:
```python
confidence=getattr(_amb_plan, "confidence", None)
```

This is a server.py-only fix. `executive.py` is UNTOUCHED — FREEZE_V1_LOCK applies to executive.py, not this.

---

## Constraints

- `executive.py` — DO NOT TOUCH
- `runtime/spine/spine.py` — DO NOT TOUCH (already fixed for main turns, commit `0653d20`)
- `alternatives_rejected` defect — still blocked by FREEZE_V1_LOCK; do not address here
- Additive only — one call site, one field added

---

## Tests

Write `tests/test_wo_fix_112_ambient.py` — 4 ATs:
- AT-1: ambient plan with confidence=0.85 → journal entry has confidence: 0.85
- AT-2: ambient plan with no confidence attr → journal entry has confidence: null, no AttributeError
- AT-3: change does not touch executive.py
- AT-4: spine002 regression still green (confirms main-turn fix intact)

Runner: `~/miniconda3/bin/python3 -m pytest tests/test_wo_fix_112_ambient.py -v`

---

## Return

Result card to: `blender/agent_bus/builder/DONE/FROM_BUILDER_WO-FIX-112-AMBIENT_result.md`
Required: AT results (X/4 PASS) + commit hash + confirmation executive.py untouched.

---

*Board / Lead Architect — 2026-08-28*
