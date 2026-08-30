# FROM BUILDER — WO-SEAM-A Executive Minimum Repair

**WO:** WO-SEAM-A — Executive intent→action minimum repair  
**Priority:** P0 · FREEZE_V1_LOCK LIFTED (David L3, 2026-08-30)  
**Date:** 2026-08-30  
**Commit:** `858db4d`

---

## Result

**7/7 AT PASS**

```
✅ AT-1: 'open Joe Budden Podcast on YouTube' → 'answer' (plain imperative command)
✅ AT-2: 'tell me the weather' → 'answer' (plain imperative command)
✅ AT-3: 'play the song again' → 'answer' (plain imperative command)
✅ AT-4: 'that's an interesting tension, isn't it' → 'reflect' [not ANSWER — correct]
✅ AT-5: 'what is done?' → extracted 'done' in ambiguous guard — Seam B active
✅ AT-6: test_wo001_faculty_bus.py PASS
✅ AT-6: test_wo006_emotional_processing.py PASS
✅ AT-6: test_wo014_spine_wiring.py PASS
✅ AT-7: both imperative inputs confirm action='answer' in routing result
```

## What changed

`runtime/executive.py`:
- Added `_IMPERATIVE_PREFIXES` tuple (module-level constant, WO-SEAM-A)
- Added check in `_conversation_action()` after CONNECT phrases, before numbered ANSWER block
- Plain imperatives starting with action verbs ("open ", "play ", "tell me", etc.) now route to `action: "answer"` regardless of intent label
- Previously, "open Joe Budden Podcast on YouTube" fell through to default → `reflect` (wrong)

`tests/test_wo_seam_a_executive_repair.py`:
- 7 ATs as specified in WO

## Routing trace sample

| Input | Before | After |
|---|---|---|
| "open Joe Budden Podcast on YouTube" | reflect (default) | **answer** (plain imperative) |
| "tell me the weather" | reflect (default) | **answer** (plain imperative) |
| "that's an interesting tension" | reflect (default) | reflect (unchanged — correct) |

## Scope compliance

Exactly as scoped — no redesign:
- Only `_conversation_action()` modified (added 4 lines)
- No changes to cognitive spine, faculty bus, provider routing, or plan/capability structure
- Seam B (routing_drift guard) unchanged
- Frozen kernel tests pass

## FREEZE_V1_LOCK status

Lifted for this WO only. `executive.py` returns to FREEZE_V1_LOCK now that this WO is closed.

*Builder / Board — 2026-08-30*
