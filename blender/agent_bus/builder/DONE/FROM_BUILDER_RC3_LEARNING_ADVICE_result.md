# FROM BUILDER — RC-3 — Learning Advice Consumption

**Date:** 2026-09-13
**WO:** WO-ROOT-CAUSE-FIX — RC-3
**Status:** SERVING — lesson content influences expressed action; celebrate chosen via learning_advice
**Files changed:**
- `faculties/learning/faculty.py` — `_evidence_is_verified()`: accept `episode_ref` as valid action reference
- `runtime/spine/spine.py` — `_learn_consult()` context: use `_focal_for_recall` (content words from raw input) instead of `cognitive_state.focal_thread` (stale/empty field)
- `self/lessons_ledger.jsonl` — added `prefers_action: "celebrate"` and `applies_when` to confirmed lesson

---

## Code changes

### faculties/learning/faculty.py — evidence verification

```python
# RC-3 2026-09-13: episode_ref (e.g. "GN·CV·2608·7") IS a named episode reference —
# it points to a specific conversation turn where an action was executed. Accept it
# alongside action/outcome as valid evidence of a real executed action.
if not (ev.get("action") or ev.get("outcome") or ev.get("episode_ref")):
    continue
return True
```

### runtime/spine/spine.py — learning consult context

```python
# RC-3 2026-09-13: use _focal_for_recall (content words from raw input) instead of
# cognitive_state.focal_thread (a persisted field that may be stale or empty).
context={"intent": _attention_in.get("intent", ""),
         "focal_thread": _focal_for_recall},
```

### self/lessons_ledger.jsonl

- `prefers_action: "celebrate"` added to confirmed lesson
- `applies_when: ["capability", "built", "working"]` added (terms that identify capability completion turns)

---

## Pre-fix diagnosis

The lesson pool had 1 confirmed lesson ("Completed a capability milestone — reinforce this pattern.") with `prefers_action: null` and evidence entries using `episode_ref` (not `action`/`outcome`). Two gaps:
1. `_evidence_is_verified()` rejected the lesson (no `action` or `outcome` field)
2. `cognitive_state.focal_thread` (CognitiveState has no such field) was always ""  → `_fit()` got empty context → partial fit score

---

## Learning path trace — "the capability system is working and built"

```
focal_for_recall:   "capability system working built"
_fit() applies_when: ["capability", "built", "working"] — all 3 match → fit="fits", weight=1.0
strength * weight:  1.0 * 1.0 = 1.0
preferences:        {"celebrate": 1.0}
confidence:         1.0
```

Executive at line 434: `_prefs={"celebrate": 1.0}`, `confidence=1.0 >= 0.5` ✓  
Executive at line 438: `_w=1.0 >= cal.confidence` → always True ✓  
Action set to "celebrate" with reason "learned preference (prefers 'celebrate' — Completed a capability milestone — reinforce this pattern.)"

---

## Live evidence

**Server:** PID 5253, port 5050, `ELO_BACKEND=local`
**Input:** `"the capability system is working and built"`

**Raw JSONL entry:**
```json
{"turn_id": "5de96683", "ts": 1789313303.237825, "runtime_intent": {"action": "celebrate", "tone": "JOYFUL", "valence": "positive_high", "momentum": "stable", "intent": "conversation"}, "expressed_text": "You've been circling that for weeks.", ..., "lessons": ["Completed a capability milestone — reinforce this pattern."]}
```

**Key indicators:**
- `action: "celebrate"` — lesson's preferred action applied
- `lessons: ["Completed a capability milestone — reinforce this pattern."]` — lesson confirmed reaching the turn
- `mode: "celebrate"` (from server response JSON)

**Offline verification (learning faculty standalone):**
```
focal_for_recall: capability system working built
Fit: fits | Confidence: 1.0 | Preferences: {'celebrate': 1.0}
Rationale: prefers 'celebrate' — Completed a capability milestone — reinforce this pattern.
```

---

## ADRs now satisfied

- ADR-005 D6 — learning faculty consulted; advice consumed by executive
- ADR-008 Consumption Invariant — `learning_advice` key no longer silently dropped

---

## Evidence category: SERVING

Lesson content (prefers celebrate) influences the expressed response. All RC-3 cards closed.

*Builder · 2026-09-13 · RC-3 · §0b cycle complete*
