# Board Review — WO-0105: Capability Fabric + Continuous Identity Architecture
**Date:** 2026-10-11
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

---

## Card scope

Refactor from tiered pipeline to capability fabric: SELF + LIFE + WORLD + FACULTIES
as concurrent processes. Kernel as truth boundary separating operational truth from
identity response.

Four deliverables:
1. `runtime/capability_dispatcher.py` — CLASSIFY + RESOLVE (see also WO-0104)
2. `runtime/prompt_builder.py` — typed faculty contracts (Executive/Planning/Creativity)
3. `runtime/identity_kernel.py` — four invariants + `two_truths_gate()`
4. Non-blocking capability dispatch (inner_thought not suspended during capability call)

---

## Implementation status

Already landed (commit `222be31`). Prior board filing at `59fca64`.

`two_truths_gate()` in `runtime/capability_dispatcher.py` separates definitive-macOS
results (fast answer path) from recorded/inference results (synthesis path).

Four invariants present in `runtime/identity_kernel.py`:
- INVARIANT 1: Capabilities extend perception/knowledge/action; must not replace identity
- INVARIANT 2: External tools provide results; eLo determines what they mean
- INVARIANT 3: eLo's inner life is continuous during capability invocation
- INVARIANT 4: eLo recognises a need, not a tier

---

## Tests — `tests/test_capability_fabric.py`

```
python3 -m pytest tests/test_capability_fabric.py -v
→ 25 passed in 0.16s
```

Covers: `two_truths_gate` (definitive macOS fast-answer, math, recorded/inference need-synthesis,
value-none, identity-response preserved, operational-truth-not-overridden) +
`build_faculty_prompt` (executive/planning/creativity typed packets, identity anchor,
decision/plan/ideas contracts, packet-not-raw-dump, unknown faculty, inner-life-not-suspended).

---

## Board decisions required

None. FREEZE_V1_LOCK respected — executive.py not modified.

*Builder 1 · 2026-10-11*
