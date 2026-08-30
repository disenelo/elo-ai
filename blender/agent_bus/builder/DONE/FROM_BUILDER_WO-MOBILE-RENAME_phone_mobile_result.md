# FROM BUILDER — WO-MOBILE-RENAME phone → mobile

**WO:** WO-MOBILE-RENAME — Rename embodiment label `phone` → `mobile`
**Priority:** P1 · **Authority:** David L3 (2026-08-30)
**Date:** 2026-08-30
**Commit:** `14d1958`

---

## Result

**AT-1: PASS** — zero `"phone"` embodiment value strings in `runtime/mobile_embodiment.py`
**AT-2: PASS** — 16/16 tests pass (WO-MOBILE-001 × 5, nav-005 × 10, mobile-brain × 1)
**AT-3: PASS** — no other spine file or test broken
**AT-4: PASS** — `executive.py` not touched; FREEZE_V1_LOCK intact

---

## What changed

**`runtime/mobile_embodiment.py`:**
- `state.embodiment = "phone"` → `"mobile"` (D-SPINE-1 foreground)
- `"to": "phone"` → `"mobile"` (foreground transition record)
- `"from_": "phone" / "to": "phone"` → `"mobile"` (background transition record)
- Comments/docstrings referencing the embodiment value updated to `"mobile"`

**`runtime/capabilities/registry.py`:**
- `{"phone"}` → `{"mobile"}` in `embodiment_scope` loop (line 489) — critical:
  capabilities now correctly match `current_embodiment="mobile"` at runtime

**Tests updated:**
- `tests/test_wo_mobile001_mobile_embodiment.py`: 5 assertions + error messages
- `tests/test_wo_nav_005.py`: docstring + `_check_any_cap_visible("phone")` call

## Note on registry.py

`_PHONE_CAPABLE` frozenset name preserved (variable identity unchanged). The embodiment scope
filter `{"phone"}` → `{"mobile"}` is the runtime-critical fix: without it, capability
filtering would have silently returned 0 caps for the mobile embodiment despite the rename.

*Builder / Board — 2026-08-30*
