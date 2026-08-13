# WP_F — Relationship Faculty Audit

**Status:** PENDING
**Priority:** HIGH
**Depends On:** WP_C (Language), WP_D (Memory), WP_E (Attention)
**Architecture Reference:** `docs/architecture/05_relationship_faculty.md`

---

## Purpose

Audit, validate, and freeze the Relationship Faculty. The Relationship Faculty tracks the relational state between eLo and David — familiarity, trust, continuity. It shapes tone and register selection.

---

## Objective

At the end of WP_F:
- Relationship context injection is validated
- Register selection (SOUTH_LDN_MODE etc.) is validated across the full conversation flow
- The Relationship Faculty's interaction with Language and Memory is documented
- The Relationship Faculty is frozen

---

## Existing Architecture Review Required

**Files to audit:**

| File | Role |
|---|---|
| `runtime/spine/relationship_faculty.py` | Relationship context computation |
| `relationships/relationship_engine.py` | Relationship state management |
| `server.py` — `_rel_inject()` | Injection into g_ctx |
| `docs/architecture/05_relationship_faculty.md` | Architecture specification |

**Known issues to investigate:**

1. **Register persistence** — SOUTH_LDN_MODE is detected by the Language Faculty and passed to the Executive via the Relationship Faculty. Validate that register detection survives across turns (not re-detected from scratch each turn).

2. **Relationship state update** — does the Relationship Faculty update after each turn, or only on session start?

3. **Interaction with Memory** — the Relationship Faculty likely reads from the same memory stores as the Memory Faculty. Confirm there is no duplication or conflict.

---

## Freeze Criteria

- [ ] Relationship context injection validated
- [ ] Register selection validated with real South London inputs
- [ ] Relationship Faculty reads from — not writes to — Executive
- [ ] No duplication with Memory Faculty
- [ ] Regression tests pass (C, D, E regressions must still pass)
