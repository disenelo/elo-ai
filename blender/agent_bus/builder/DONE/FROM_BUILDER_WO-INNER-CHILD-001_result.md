# FROM_BUILDER — WO-INNER-CHILD-001 DONE
**Date:** 2026-08-31
**WO:** WO-INNER-CHILD-001 — Inner Child / Moon Runtime Behavioural Mode
**Status:** ✅ DONE — 4/4 ATs PASS

## Result

Inner Child / Moon cognitive mode wired as a per-turn behavioural gate in `_executive_faculty()`.
Source: eLo INTENT RECOVERY §8 §16 — "Move first, understand after." / "Try it once."

### Files created / modified

- `runtime/spine/plan.py` — `cognitive_mode_inner_child: bool = False` added to CognitivePlan
- `runtime/spine/spine.py` — Inner Child activation block after vessel phase: fires when curiosity_score > 0.7, mode is PLAY/EXPLORE, or intent is dream/explore/ambient_curiosity. When active: capabilities capped at 1 (anti-fragmentation). Logged at DEBUG level.
- `server.py` — `cognitive_mode_inner_child` forwarded in exec_decision dict from plan
- `runtime/prompt_builder.py` — directive block: `"mode: inner-child — express curiosity, move toward the thing, small action first. Try it once."` injected when cognitive_mode_inner_child=True. Also D-4: `"mode: builder — structure, steps, sequence…"` injected when mode is BUILD/STUDIO/BUILDER.

### Acceptance tests

- AT-1 PASS — cognitive_mode_inner_child field present on CognitivePlan, default=False
- AT-2 PASS — curiosity > 0.7 → inner_child=True, capabilities capped to 1
- AT-3 PASS — 'mode: inner-child' in directive when cognitive_mode_inner_child=True
- AT-4 PASS — fresh CognitivePlan = False (no persistence across turns)

**Tests file:** `tests/test_wo_inner_child_001.py` — 4/4 PASS (2026-08-31)
**FREEZE_V1_LOCK:** CLEAN — executive.py not touched.
