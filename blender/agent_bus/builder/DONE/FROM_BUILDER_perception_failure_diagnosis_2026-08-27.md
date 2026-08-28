# FROM BUILDER → BOARD — Perception Test Failure Diagnosis
**Date:** 2026-08-27
**Source:** `FROM_ARCHITECT_2026-08-27_test_0005_sys_exit_defect.md` (perception section)
**Action:** Diagnose only — do NOT fix without Board authorisation

---

## test_wo096_desktop_perception — AT-2 failure

**Test assertion:**
```python
assert "window_state import get" in lws_src
```

**Actual import in `world/live_world_state.py:283`:**
```python
import desktop.window_state as _ws_mod   # module-style so test patches propagate
```

**Root cause:** Import style changed to module-style (`import ... as`), which is correct for testability (patch propagation). But the test string-checks for `"window_state import get"` (function-import style). The implementation is correct; the test expectation is out of sync with the implementation.

**Classification:** Test/implementation mismatch. Fix requires updating the test assertion to match the correct module-style import pattern, OR reverting the implementation import style.

**Pre-existing:** Yes — not caused by any change in this session.

---

## test_card_0006_perception_world — AT-3 and AT-5 failures

**Test scenario:** `perceive(window_app="Chrome", window_title="A very long title that got cut…")` → expects `result_partial.partial is True`.

**Trace:**

1. `tag_partial(f"Chrome: A very long title that got cut…")` → correctly returns `"[PARTIAL: Chrome: A very long title that got cut…]"` (ends with `…]`, not `…`)
2. `modality_reads["window"]` = `"[PARTIAL: Chrome: A very long title that got cut…]"`
3. `_any_truncated = any(_is_truncated(v) for v in modality_reads.values())`
4. `_is_truncated("[PARTIAL: Chrome: A very long title that got cut…]")` checks `endswith("…")` → **False** (ends with `"]"`, not `"…"`)
5. `_any_truncated = False`
6. `partial = confidence < 0.7 or ... or _any_truncated` → if confidence ≥ 0.7 and modalities present → **False**

**Root cause:** `_any_truncated` checks `_is_truncated(v)` on values that `tag_partial()` has already wrapped as `[PARTIAL: …]`. The closing `]` breaks the endswith check. Truncation is correctly tagged but never detected by `_any_truncated`.

**Possible fixes (Board decides):**
- Option A: Add `v.startswith("[PARTIAL:")` check to `_any_truncated` alongside `_is_truncated(v)`
- Option B: Store raw (untagged) values in `modality_reads` for the truncation check, tag only for display
- Option C: Update `_is_truncated` to also detect `[PARTIAL:…]` pattern

**Classification:** Logic defect — `_any_truncated` never fires when values are tagged. Partial detection relies entirely on confidence threshold and absent modalities.

**Pre-existing:** Yes — not caused by any change in this session.

---

## Summary

| Test | AT | Root Cause | Pre-existing |
|---|---|---|---|
| test_wo096_desktop_perception | AT-2 | Test checks for function-import string; implementation uses module-style import | Yes |
| test_card_0006_perception_world | AT-3 | `_is_truncated()` called on already-tagged `[PARTIAL: …]` string — endswith check fails on `]` | Yes |
| test_card_0006_perception_world | AT-5 | Same root cause as AT-3 (AT-5 depends on AT-3 partial being True) | Yes |

**Neither failure is caused by any change in this session.**
**Builder does not fix. Board authorises fix WO if desired.**

---

*Builder · 2026-08-27*
