# WO-EXP-001 — storytelling_style Field in Meaning Object
**Date:** 2026-08-27
**Priority:** P2
**Authority:** SC-NEW-001 SPECIFIED + RATIFIED David L3 2026-08-24 — `docs/architecture/specs/SPEC_SC_NEW_001_storytelling_style_2026-08-24.md`
**Build List:** §5 eLo EXPRESSION — first WO

---

## Intent

Add `storytelling_style: str | None` to the Meaning Object as specified and ratified in SC-NEW-001. This is the smallest structural change that closes the storytelling CCM gap. The field does not replace CHARACTER DNA, add a narrative engine, or override Voice States.

---

## Deliverables

**D-1:** Add `storytelling_style: str | None = None` to the Meaning Object dataclass/schema. Read SPEC_SC_NEW_001 §2 for the exact field specification.

**D-2:** Conversation Faculty populates this field per-turn. Read SPEC_SC_NEW_001 §3 for population logic. Do not invent population logic — follow the SPEC.

**D-3:** Field is passed through to response generation where the SPEC specifies consumption. Do not wire into Executive directly — this is a Meaning Object field, not a CAL action.

**D-4:** If `storytelling_style` is `None`, existing behaviour is unchanged. No regression.

---

## SPEC Reference

Read `docs/architecture/specs/SPEC_SC_NEW_001_storytelling_style_2026-08-24.md` before implementing. That document is the authority. This WO is the execution directive, not a replacement for the SPEC.

---

## Acceptance Tests

**AT-1:** `storytelling_style` field present in Meaning Object with correct type annotation.
**AT-2:** Conversation Faculty populates field per SPEC §3 logic.
**AT-3:** `storytelling_style = None` → existing behaviour unchanged (regression test).
**AT-4:** Field value accessible in response generation context.
**AT-5:** No modification to Executive or CAL action routing.

Run on miniconda3. Return 5/5 PASS to Board.

---

## Constraints

- Read SPEC_SC_NEW_001 before touching any file.
- Do not modify executive.py (LAW-017).
- Do not create a new Faculty.
- Do not replace CHARACTER DNA.
- Additive change only — no existing behaviour modified.

---

*Board / Lead Architect · 2026-08-27*
