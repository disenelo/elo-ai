# Board Review — WO-106: THE SEAM — Executive Reads the Assembled Plan
**Date:** 2026-10-11
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

---

## Card scope

Open the seam: change Executive input from `(attention, user_input)` to the assembled
plan/UnifiedCognitiveState so eLo decides from real world/working-memory/cognitive
context (Ruling H, ADR-Exec-006, ADR-Exec-002).

Five changes:
1. `exec_decide` takes assembled state
2. Working-memory competition winner drives attention (not raw `attention_model`)
3. `build_prompt` reads `plan.world` (one source of truth per turn)
4. `plan.capabilities` gates execution — no keyword re-decision downstream
5. Affordances reach the Executive

---

## Implementation status

Already landed. `runtime/spine/spine.py` now passes `world`, `cognitive_state`,
`working_memory`, `affordances`, `embodiment_state`, `execution_report`, `identity`,
`temporal` to `_exec_decide_fn`. `ExecutiveContext.as_dict()` bridges the frozen
executive.py boundary.

`significance_score` forwarded to top-level of `as_dict()` (commit `b61a2b6`).

---

## Commits

- `b61a2b6` — WO-106: seam — forward significance_score to top-level of as_dict()
- `7ec7fd6` — WO-106: BUILT card + board filing

---

## Tests — `tests/test_wo097_wo106_seam.py`

```
python3 -m pytest tests/test_wo097_wo106_seam.py -v
→ 8 passed in 0.47s
```

| Test | Result |
|------|--------|
| test_conversation_before_embodiment_static | ✅ |
| test_embodiment_ordering_regression_guard | ✅ |
| test_executive_faculty_call_site_passes_assembled_state | ✅ |
| test_world_absent_logs_warning | ✅ |
| test_world_state_reaches_enriched_attention | ✅ |
| test_wm_winner_reaches_enriched_attention | ✅ |
| test_executive_faculty_accepts_new_params | ✅ |
| test_significance_score_at_top_level | ✅ |

---

## Capability rows moved (Ruling H requirement)

`plan.world`, `plan.cognitive_state`, `plan.working_memory`, `plan.embodiment_state`,
`plan.capabilities`, `snapshot.surface_affordances` — all now consumed by the Executive
via `ExecutiveContext`. Previously assembled and discarded; now VERIFIED as input to
`exec_decide`. Capability Truth Matrix rows for spatial awareness, working memory
competition, and affordance-based gating move from PARTIAL → WIRED.

---

## Board decisions required

None. FREEZE_V1_LOCK respected — `executive.py` not modified; seam bridged through
`ExecutiveContext.as_dict()`.

*Builder 1 · 2026-10-11*
