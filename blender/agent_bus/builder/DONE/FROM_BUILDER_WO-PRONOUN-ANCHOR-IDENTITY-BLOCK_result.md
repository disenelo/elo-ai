# FROM BUILDER — Self-Narrative Injection Fix (identity_block source)

**Date:** 2026-09-15
**WO:** P1 dispatch 2026-09-15 — "Third-person injection fix (system prompt side)"
**Authority:** Board dispatch 2026-09-15

---

## Problem

`identity_block()` in `self/elo_self_model.py` emitted:

```
[IDENTITY — constitutional baseline, asserted from self-model every turn]
name: eLo
with: David Charles
invariants: never preachy; ...
```

`"with: David Charles"` — a key-value fact about a third party named "David Charles".
LLMs parse this as descriptive metadata about an external person and narrate about them
in third person ("his projects", "David's work", "he is building").

Prior WO-PRONOUN-ANCHOR-001 fixed this at the `prompt_builder.py` directive level
(FORBIDDEN block + rewrite anchor). The gap: the source block still emitted the
third-person-triggering label.

GAP_REGISTER T6 was marked OPEN at the narrative/identity block level.
This card closes T6.

---

## Root cause

`who_i_am_with` stores `"David Charles"` (or `"David"`). The label `with:` in the
identity block frames this as a third-party description. No inline instruction directed
the LLM to address this person as `"you"` — the FORBIDDEN block in prompt_builder.py
fires after injection, not at the source.

---

## Fix

`self/elo_self_model.py` — `identity_block()` at line 308:

```python
# BEFORE:
f"with: {state.who_i_am_with}",

# AFTER:
f"talking with: you ({state.who_i_am_with})",
"Address them directly as 'you'. Never 'David', 'he', 'his', or 'they'.",
```

Two changes:
1. Label changed from `with:` → `talking with:` — shifts framing from third-party
   description to second-person addressee
2. Inline directive added inside the block — fires immediately adjacent to the
   name reference, before any other processing

---

## Evidence

```python
from self.elo_self_model import load, identity_block
state = load()
print(identity_block(state))
```

```
[IDENTITY — constitutional baseline, asserted from self-model every turn]
name: eLo
talking with: you (David)
Address them directly as 'you'. Never 'David', 'he', 'his', or 'they'.
invariants: never preachy; never dramatic; never overly clinical; never trapped in abstraction; identity constant across backend and session
```

- Third-person trigger `"with: David Charles"` removed ✓
- Second-person framing `"talking with: you (David)"` in place ✓
- Inline directive fires adjacent to name reference ✓
- Prior WO-PRONOUN-ANCHOR-001 FORBIDDEN block still active as safety layer ✓

---

## DoD Assessment

| Item | Status |
|------|--------|
| `with: David Charles` removed from identity block output | ✅ SERVING |
| Second-person framing `talking with: you (David)` in place | ✅ SERVING |
| Inline directive `"Address them directly as 'you'..."` added | ✅ SERVING |
| `EloSelfState.who_i_am_with` field unchanged (data preserved) | ✅ SERVING |
| Prior FORBIDDEN block in prompt_builder.py still active | ✅ SERVING (additive) |
| narrative_block() unchanged (no David reference triggers found) | ✅ SERVING |

**GAP_REGISTER T6: CLOSED**

**VERDICT: SERVING**

---

*Builder · 2026-09-15*
