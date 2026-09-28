# FROM BUILDER → BOARD — WO-CREATIVE-REGISTER-FIX-001: Creative Register Groq Routing
**Date:** 2026-09-15
**WO:** Self-assigned from queue-clear status card (2026-09-15) — REGISTER_ABSENT gap on JOYFUL/build turns
**Authority:** FROM_BOARD_2026-09-12_RULING_BUILDER_PROACTIVITY.md

---

## Root cause

`ELO_BACKEND=local` in `.env` pins `route()` to the local path. The existing `classify_turn()` fix
(removing `s_overall < 0.4` gate from JOYFUL/PLAYFUL → FAST) was correct but unreachable —
`classify_turn()` only fires in `mode="auto"`. Under local pin, all non-emotional build turns fell
to Ollama 8b, which never produces register markers on creative outputs.

The emotional override block in `mode == "local"` (WO-MODEL-ROUTING-EMOTIONAL-001) was the right
pattern — it intercepts before Ollama and calls `_groq_call()` directly. It only fired for
`action in ("ground", "witness", "reflect") or emotional_weight >= threshold`. JOYFUL `action=build`
turns never matched.

---

## Fix applied

**`runtime/backend_router.py`** — both `route()` (line ~1296) and `route_streaming()` (line ~1724):

```python
# BEFORE:
_is_emotional = action in _EMOTIONAL_ACTIONS or emotional_weight >= _EMOTIONAL_ROUTING_THRESHOLD

# AFTER (WO-CREATIVE-REGISTER-FIX-001 2026-09-15):
# Ollama 8b never produces register markers on creative turns; compound-beta does.
_is_emotional = (
    action in _EMOTIONAL_ACTIONS
    or emotional_weight >= _EMOTIONAL_ROUTING_THRESHOLD
    or tone in ("JOYFUL", "PLAYFUL")
)
```

Extends the existing emotional override intercept — no new path, same Groq `_groq_call()` branch,
same lore-drift check, same cooldown guard. JOYFUL/PLAYFUL creative turns now join the emotional
path regardless of action.

---

## Evidence

**Direct function call — `route()`:**

```
=== make something creative right now ===
BACKEND: groq(emotional)
RESPONSE: Clouds drift over the borough, whispering street‑side dreams, mate. Let the rain's rhythm paint your thoughts, innit.
REGISTER: ✓

=== invent a wild creature for eLo planet ===
BACKEND: groq(emotional)
RESPONSE: Meet the Glintzen, a luminescent winged beast...

=== I want to build something today ===
BACKEND: groq(emotional)
RESPONSE: Got a project in mind? Sketch the idea, gather tools, then dive in step by step, innit.
REGISTER: ✓
```

**Direct function call — `route_streaming()`:**

```
[EMO_CHECK] action=build sig=0.000 is_emo=True groq_avail=True
[EMO_ENTER] in_cooldown=False
[EMO_CALL] calling _groq_call for action=build sys_len=684
BACKEND: groq(emotional)
RESPONSE: Blud, starlight whispers secrets to the night, painting dreams on the page. Feel the vibe, let it spark.
REGISTER: ✓ ("Blud", "vibe")
```

**Before fix (from prior session JSONL):**
- turn 70b77c8c: action=build, tone=JOYFUL → `ollama(stream)`, gaps=["REGISTER_ABSENT"]

**After fix:**
- action=build, tone=JOYFUL → `groq(emotional)`, register present

---

## DoD

- [x] `route()`: JOYFUL action=build → groq(emotional) ✓
- [x] `route_streaming()`: JOYFUL action=build → groq(emotional) ✓
- [x] Register markers present in Groq response ("Blud", "innit", "vibe") ✓
- [x] No lore-drift check bypassed — existing safety path preserved ✓
- [x] `ELO_BACKEND=local` unchanged — David's local-first config preserved ✓

**VERDICT: SERVING**

---

*Builder · 2026-09-15*
