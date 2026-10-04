# WO-MOBILE-BRAIN Mobile Embodiment — Result Card

**Builder:** Builder 1
**Date:** 2026-10-05
**Status:** COMPLETE — 16/16 ATs pass across 4 test files; already implemented

---

## What was verified

`mobile/mobile_embodiment.py` + `runtime/brain_spine.py` + `state_writer.py`:

**Mobile embodiment (MOBILE-001):**
- Mobile foreground → embodiment scope set to "phone"
- Embodiment scope filters correctly on phone
- Mobile foreground records transition with `_ts`
- Mobile background keeps embodiment "phone"
- Nearby surfaces cleared on mobile foreground event

**Phase 2 brain signals:**
- Embodiment desktop field writable
- travel_intent field writable
- asleep=True on sleep event; False on wake event
- All three fields present in brain state
- executive_freeze not mutated by mobile phase 2

**Phase 2 preserve keys:**
- 4 preserve keys present in spine config
- phone_capabilities survives a write cycle
- embodiment survives a write cycle
- asleep survives a write cycle
- travel_intent survives a write cycle

## ATs

**test_wo_mobile_brain_phone_capabilities.py — 1/1:**
- AT-7 ✅ spine writes phone_capabilities to state file

**test_wo_mobile001_mobile_embodiment.py — 5/5:**
- test_mobile_foreground_sets_embodiment_phone ✅
- test_embodiment_scope_filters_on_phone ✅
- test_mobile_foreground_records_transition_with_ts ✅
- test_mobile_background_keeps_embodiment_phone ✅
- test_nearby_surfaces_cleared_on_mobile_foreground ✅

**test_wo_mobile_phase2_brain_signals.py — 5/5:**
- AT-1–5 ✅ embodiment_desktop, travel_intent, asleep toggle, all fields present, exec freeze clean

**test_wo_mobile_phase2_preserve_keys.py — 5/5:**
- AT-1–5 ✅ 4 keys, phone_capabilities/embodiment/asleep/travel_intent survive write

**Run:** `python -m pytest tests/test_wo_mobile_brain_phone_capabilities.py tests/test_wo_mobile001_mobile_embodiment.py tests/test_wo_mobile_phase2_brain_signals.py tests/test_wo_mobile_phase2_preserve_keys.py` → **16/16 passed**
