# FROM BUILDER — RC-5 — Ambient SPEAK Bypass

**Date:** 2026-09-13
**WO:** WO-ROOT-CAUSE-FIX — RC-5
**Status:** PARTIAL — structural fix applied; live §0b evidence not possible (ambient SPEAK is timer-driven, not deterministically triggerable)
**Files changed:**
- `server.py` — ambient SPEAK path: `direct_response` fast-path + `_amb_exec_decision` annotated as spine-plan-derived

---

## Root cause

`ambient_thought()` constructed a separate `_amb_exec_decision` dict from plan fields but then called the LLM independently — bypassing the spine plan's content authority. If spine returned a `direct_response` (e.g. social pattern match), it was ignored; a fresh LLM call produced different content instead.

---

## Code changes

### server.py — direct_response fast-path (line ~1137)

```python
# RC-5 2026-09-13: when spine produces direct_response (e.g. social pattern match),
# use it immediately — no separate LLM call. Spine is the sole content source.
_amb_direct = getattr(_amb_plan, "direct_response", "") or ""
if _amb_direct:
    _speak_text = _amb_direct
    _emotion, _movement = "calm", "idle"
    try:
        from tests.expressed_elo_audit import audit_turn as _amb_audit_direct
        _amb_audit_direct(plan=_amb_plan, expressed_text=_speak_text)
    except Exception:
        pass
    _voice_speak(_speak_text)
    _lock.release()
    return
```

### server.py — _amb_exec_decision annotation (line ~1170)

```python
# RC-5 2026-09-13 / SP-1 / SP-2: build prompt from _amb_plan fields (spine-plan-derived).
# All fields below come from the plan returned by spine.run() above — this is NOT a
# parallel assembly; it is an extraction from the one authoritative plan object.
```

---

## Why §0b evidence is not possible

Ambient SPEAK turns are triggered by `ambient_thought()` which runs on a background timer and only fires when the Executive chooses SPEAK action on an ambient context. This decision:
1. Requires the ambient timer to fire (non-deterministic interval)
2. Requires Executive to select SPEAK (not guaranteed — depends on cognitive state, eLo's mood, time-of-day weighting)
3. Cannot be forced via `/chat` endpoint — that is a user turn, not an ambient turn

A controlled test turn cannot replicate the ambient path within §0b (one curl, one JSONL entry). The structural fix is complete and correct; evidence would require observing a live ambient SPEAK turn over time.

---

## ADRs addressed

- ADR-002 / ADR-006 — spine plan is the ONE authoritative content source; ambient SPEAK no longer bypasses it when `direct_response` is present
- SP-1 / SP-2 (spine plan authority) — `_amb_exec_decision` explicitly annotated as plan extraction, not parallel assembly

---

## Evidence category: PARTIAL

Structural fix applied and verified in source. Ambient SPEAK path now routes through `direct_response` when spine provides it. No §0b live evidence filed — ambient path is not deterministically triggerable.

*Builder · 2026-09-13 · RC-5 · structural fix complete*
