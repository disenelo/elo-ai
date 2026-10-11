# Board Review — WO-CANON-I: eLo Knows David, Speaks in Second Person
**Date:** 2026-10-11
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

---

## Card scope

Fix eLo naming David in the third person during conversation ("David is doing X"
while talking to him). Added ADDRESS RULE to both persona locations (spec + fallback),
added divergence test to enforce no drift.

Three deliverables:
1. ADDRESS RULE added to `prompts/living_presence_spec.txt` (UL-002 scoped unlock)
2. ADDRESS RULE added to `runtime/prompt_builder.py:_PERSONA` (fallback)
3. Divergence test: both personas must agree on the address rule block

---

## Commits

- `c0e1841` — WO-CANON-I: eLo knows he is with David — second-person address rule
- `5741ff3` — WO-CANON-I admin: board DONE, card → DONE/, outbox RUN 32

---

## Tests — `tests/test_canon_i_identity_second_person.py`

```
python3 -m pytest tests/test_canon_i_identity_second_person.py -v
→ 7 passed in 0.09s
```

| Test | Result |
|------|--------|
| spec names David | ✅ |
| persona names David | ✅ |
| spec has ADDRESS RULE | ✅ |
| persona has ADDRESS RULE | ✅ |
| personas agree on address rule (divergence alarm) | ✅ |
| address rule content in spec | ✅ |
| address rule content in persona | ✅ |

---

## READY FOR DAVID'S LIVE VOICE TEST

Automated tests pass. The voice test (does eLo speak to David in second person?)
is the final confirmation. Test at end-of-day live session.

## Board decisions required

None. Scoped unlock UL-002 consumed. Re-freeze intact.

*Builder 1 · 2026-10-11*
