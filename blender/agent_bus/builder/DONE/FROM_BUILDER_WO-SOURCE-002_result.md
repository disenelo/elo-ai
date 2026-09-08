# FROM_BUILDER — WO-SOURCE-002 DONE
**Date:** 2026-08-31
**WO:** WO-SOURCE-002 — Cognitive Principles: Runtime Class Constraining the Executive
**Status:** ✅ DONE — 6/6 ATs PASS

## Result

17 Cognitive Principles wired as a runtime constraint layer above Executive reasoning.
Violations are advisory — they never block the turn. They populate plan.principle_violations
and are forwarded to the Reflection Faculty via ExecutionReport.principle_violations_observed.

### Files created / modified

- `kernel/principles/cognitive_principles.yaml` — all 17 principles, names, statements, violation_signals
- `runtime/cognitive_principles.py` — `CognitivePrinciples` class with `check()` method + `PRINCIPLES` module singleton. Detects: `never_pretend_certainty` (speech_licence violations + high confidence), `protect_user_agency` (prescription action), `executive_reasons_once` (_re_reasoned marker), `embodiment_expresses_cognition` (identity_override in presence_plan)
- `runtime/spine/plan.py` — `principle_violations: list = field(default_factory=list)` added to CognitivePlan
- `runtime/spine/spine.py` — `PRINCIPLES.check(plan)` called in `_executive_faculty()` after TieredFacultyReader block; violations set on `plan.principle_violations`; `build_execution_report()` forwards violations to `ExecutionReport.principle_violations_observed`
- `runtime/contracts.py` — `principle_violations_observed: tuple` field added to ExecutionReport (flows into integrate_session via execution_report kwarg)

### Acceptance tests

- AT-1 PASS — all 17 principles loaded from YAML with correct names
- AT-2 PASS — `never_pretend_certainty` fires on UNKNOWN tier + confidence >= 0.75
- AT-3 PASS — clean plan (VERIFIED tiers, default confidence) → check() returns []
- AT-4 PASS — `plan.principle_violations` populated after check()
- AT-5 PASS — violations advisory: plan still returned, conversation_action unchanged
- AT-6 PASS — CognitivePlan fields all intact; identity kernel still immutable

**Tests file:** `tests/test_wo_source_002.py` — 6/6 PASS (2026-08-31)
**FREEZE_V1_LOCK:** CLEAN — executive.py not touched. Check runs in spine.py `_executive_faculty()`.
