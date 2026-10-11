# WO-MOBILE-BRAIN — Builder half: `phone_capabilities` field in state file

**Full WO:** `engineering/work_orders/WO-MOBILE-BRAIN_slim_faculty_mock_brain.md`
**Priority:** P1 · **Authority:** David L3 (D1b ruling, 2026-08-29)
**Owner:** Builder (spine-side)

---

## What to build

Write the spine's `_PHONE_CAPABLE` list into `blender_state.json` (or the companion state
file the probe serves) as a top-level `phone_capabilities` key.

```json
{
  "phone_capabilities": ["time", "timer", "calculator", "weather", "translate", ...]
}
```

The probe serves it unchanged. MT reads it, caches it in travel memory, uses it as the
authoritative list of what the mock brain is permitted to attempt. If the field is absent,
MT falls back to Tier 1 only.

---

## Constraint

**No new endpoint.** The field rides the existing state file payload. Ruling 006 (probe
surface) is untouched. This is a single write-side addition to the state file only.

`executive.py` — MUST NOT TOUCH (FREEZE_V1_LOCK).

---

## Acceptance Test

**AT-7:** Spine writes `phone_capabilities` to state file. Field is an array of strings
matching `_PHONE_CAPABLE`. Probe serves it unchanged. MT (or a test reader) can read and
parse it from the served payload.

---

## Return

`DONE/FROM_BUILDER_WO-MOBILE-BRAIN_slim_faculty_result.md` · AT-7 pass · commit hash

*Board / Lead Architect · 2026-08-29*
