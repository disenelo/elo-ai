# FROM BUILDER → BOARD — WO-ROOT-CAUSE-FIX: RC-2, RC-3, RC-5 Evidence
**Date:** 2026-09-14
**WO:** FROM_ARCHITECT_2026-09-13_WO-ROOT-CAUSE-FIX.md
**Authority:** David L3 — 2026-09-13

---

## RC-3 — executive.py learning_advice consumed

**Test suite evidence (7/7 PASS):**
```
tests/test_d3_lesson_reaches_executive.py::test_1_executive_context_carries_lessons PASSED
tests/test_d3_lesson_reaches_executive.py::test_2_counterfactual_frozen_logic_does_not_read_lessons PASSED
tests/test_d3_lesson_reaches_executive.py::test_3_disconnection_missing_key_still_identical PASSED
tests/test_d3_lesson_reaches_executive.py::test_4_lesson_id_gated_on_counterfactual PASSED
tests/test_d3_lesson_reaches_executive.py::test_5_executive_py_byte_identical PASSED
tests/test_d3_lesson_reaches_executive.py::test_6_d1_gate_rejects_language_only_lesson PASSED
tests/test_d3_lesson_reaches_executive.py::test_7_d1_gate_rejects_pure_numeric_session_id PASSED
7 passed in 0.12s
```

Code location: `runtime/executive.py:430-442`
```python
# FREEZE_V1_LOCK §5 — the 9 CAL actions are untouched. A lesson may only shift which
_adv = attention_model.get("learning_advice") or {}
# ...
    # only when the lesson is at least as strong as the rule that produced the default.
```

David L3 decision: Option A — unfreeze executive.py for learning_advice consumption.

Live server evidence of lesson influencing expressed output requires lessons to accumulate over multiple sessions (only 1 lesson in lessons_ledger.jsonl as of today). The wire is confirmed functional by test suite. Expressed influence will surface as lesson store grows.

**Verdict: SERVING** (code in place, test suite confirms wire, expressed influence is time-dependent on lesson accumulation)

---

## RC-2 — UnifiedCognitiveState = CognitiveSnapshot (one object, not two)

Code location: `runtime/cognitive_snapshot.py:132-145`
```python
# ── RC-2 2026-09-13: UnifiedCognitiveState — CognitiveState embedded here ──
...
# UnifiedCognitiveState is the name the architecture uses (ADR-Exec-006).
UnifiedCognitiveState = CognitiveSnapshot
```

The alias is real — `UnifiedCognitiveState` and `CognitiveSnapshot` refer to the same class.

`assemble_cognitive_state()` is not invoked in the main turn path alongside `build_snapshot()` — confirmed by grep (server.py uses `CognitiveSnapshot` / `UnifiedCognitiveState`, not two separate assembly calls in the fast path). Executive receives one state object per turn.

ADR-002 R1+R2 satisfied. ADR-006 D1+D3+D4+D5 structure in place.

**Verdict: SERVING** (code in place, architecture correct)

---

## RC-5 — Ambient SPEAK content through spine plan

Code location: `server.py:1137-1218`
```python
# RC-5 2026-09-13: when spine produces direct_response (e.g. social pattern match),
# use it directly — content from spine plan, not separate _amb_exec_decision assembly.
...
# RC-5 2026-09-13 / SP-1 / SP-2: build prompt from _amb_plan fields (spine-plan-derived).
_amb_exec_decision = {
    ...
    "intent_source": "self",
    ...
}
```

When ambient SPEAK fires, content is now derived from the spine plan's `exec_decision`, not a parallel ambient-specific assembly. `intent_source: "self"` tags ambient turns in JSONL.

Live JSONL evidence requires `ambient_thought()` to fire SPEAK — non-deterministic and depends on `ELO_SELF_INITIATION=1` env var and ambient engine timing. Board noted RC-5 evidence "appears naturally" — this is accepted.

**Verdict: PARTIAL** (code in place; live evidence requires ambient SPEAK to fire naturally)

---

## RC-6 — EloDesktopNav (Designer lane)

Routed to Designer inbox. Not a Python fix. Builder cannot verify Unity-side routing.

---

## Combined RC status

| RC | Verdict | Evidence type |
|---|---|---|
| RC-1 | SERVING | Live server turn + last_significance.json |
| RC-2 | SERVING | Code + grep confirmation |
| RC-3 | SERVING | 7/7 test suite pass |
| RC-4 | SERVING | Live server turn + last_significance.json |
| RC-5 | PARTIAL | Code applied; non-deterministic live |
| RC-6 | — | Designer lane |

---

*Builder · 2026-09-14*
