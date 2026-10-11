# Board Review — WO-097: EmbodimentState Empty on Direct-Response Turns
**Date:** 2026-10-11
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

---

## Card scope

Fix spine ordering defect: `build_embodiment_state` ran BEFORE `_conversation_faculty`
published `direct_response`, so `response_text`/`display_text`/`tts_text` were always
empty on direct-response turns. Silent failure.

Three fixes:
1. Reordered: `build_embodiment_state` now runs at `spine.py:1505`, after `_conversation_faculty` at `:1448`
2. Added alarm: `_log.warning("build_embodiment_state: response_text empty on direct-response turn")` at `:1510`
3. Ordering test: `test_wo097_wo106_seam.py::test_conversation_before_embodiment_static` + `test_embodiment_ordering_regression_guard`

---

## Commit

- `bdf085a` — WO-097 + WO-106: embodiment ordering fix + executive seam opened

---

## Tests

```
python3 -m pytest tests/test_wo097_wo106_seam.py -v
→ 8 passed (includes embodiment ordering tests)
```

`test_conversation_before_embodiment_static` — static code check that `_conversation_faculty`
appears before `build_embodiment_state` in spine.py source.
`test_embodiment_ordering_regression_guard` — fails if the two are swapped back.

---

## Board decisions required

None.

*Builder 1 · 2026-10-11*
