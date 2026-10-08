# WO-B1-0105 — Capability Fabric — Board Review

**Moved by**: Builder 1  
**Date**: 2026-10-08  
**Commit**: 222be31

---

## What was built

### `runtime/identity_kernel.py`

**Four INVARIANTS** — enforced as module-level `_CAPABILITY_INVARIANTS` tuple:

1. Capabilities may extend eLo's perception/knowledge/reasoning/memory/imagination/action. They must not replace eLo's identity.
2. External tools provide results. eLo determines what those results mean to eLo and how eLo responds.
3. eLo's inner life is continuous and is not suspended merely because a capability is being invoked.
4. eLo does not select a tier. eLo recognises a need and uses the capability appropriate to that need.

**`two_truths_gate(operational_result, identity_response=None)`** — separates the two truth streams before any faculty synthesises a response:
- `operational_result = None` → `synthesise=True` (fall through to executive)
- `authority == "definitive"` AND `source == "macOS"` → `fast_answer = str(value)`, `synthesise = False` (no LLM)
- `authority == "recorded"` or `"inference"` → `synthesise = True` (voice synthesis needed)
- `value = None` → `synthesise = True`

Returns: `{operational, identity, synthesise, fast_answer}`

### `runtime/prompt_builder.py`

**`build_faculty_prompt(faculty, packet)`** — new function at module end. Typed packet enforcement for three faculties:

| Faculty | Packet keys | Contract output |
|---------|-------------|-----------------|
| executive | goal, facts, state, constraints, options | decision, rationale, confidence, next_action |
| planning | goal, current_state, constraints | plan, sequence, dependencies, blockers |
| creativity | intent, constraints, reference_context | ideas, variations, rationale |

- Identity anchor always injected first (INVARIANT 1 + 2)
- Faculty receives only its declared packet fields — not the full context dump
- Full `build()` function is untouched (FREEZE_V1_LOCK compliant)

### `tests/test_capability_fabric.py`

25 tests, all passing:
- `TestIdentityKernelInvariants`: all four invariants present + singleton loadable
- `TestTwoTruthsGate`: all routing branches (definitive/recorded/inference/None/value=None)
- `TestBuildFacultyPrompt`: three faculty contracts, identity preserved across all, no suspension keywords, no raw context dump

---

## What's NOT done (blocked on other seats)

- LIFE process (Builder 2, card 0010) — `two_truths_gate` + `build_faculty_prompt` are ready to integrate once B2 delivers working_memory
- system_primitives battery/disk/uptime (Builder 3, B3-0007) — two_truths_gate will route those results correctly once they arrive
- Non-blocking async capability dispatch (0106 daemon prerequisite) — structural work done here; true concurrency requires the daemon architecture in 0106

---

## Status

✅ Four invariants in identity_kernel.py  
✅ two_truths_gate() — operational truth separated from identity response  
✅ build_faculty_prompt() — typed contract enforcement, all three faculties  
✅ 25/25 tests passing  
⏳ LIFE process integration — waiting on B2-0010  
⏳ battery/disk/uptime — waiting on B3-0007  
⏳ True async non-blocking dispatch — waiting on 0106 daemon
