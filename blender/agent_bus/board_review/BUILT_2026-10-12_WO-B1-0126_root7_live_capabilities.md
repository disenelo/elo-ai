# Board Review — WO-B1-0126: ROOT-7 live capability injection
**Date:** 2026-10-12
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

---

## What the card asked for

eLo denies capabilities that are wired and working (web search, Spotify, lights, etc.). The anchor / identity layer must reflect the real live capability set. eLo must speak confidently: "Yes, I can."

---

## What was built

### Root cause

`build_from_plan()` (thin-prompt path) had no capability awareness. The identity anchor spec mentions capabilities in prose, but does not enumerate what is live. Result: LLM falls back to "I'm not sure if I can" or "I can't do that."

### Fix — `runtime/prompt_builder.py`

Added a `[LIVE CAPABILITIES]` injection block in `build_from_plan()`, injected just before the MEMORY GUARD:

```python
from runtime.capability_registry import CAPABILITY_REGISTRY as _CAP_REG
_cap_lines = []
for _cap_name, _cap_spec in _CAP_REG.items():
    _desc = _cap_spec.get("description", "")
    if _desc:
        _cap_lines.append(f"- {_cap_name}: {_desc}")
if _cap_lines:
    parts.append(
        "[LIVE CAPABILITIES — these are real and active right now]\n"
        "You have these capabilities wired and working. Never say you cannot do these.\n"
        "Speak confidently: 'Yes, I can' — not 'I think I can' or 'I'm not sure'.\n"
        + "\n".join(_cap_lines)
    )
```

All 19 registered capabilities enumerated at prompt time: CREATE, WORLD_VISUAL_READ, WORLD_CALENDAR_READ, WORLD_REMINDERS_READ/WRITE, WORLD_WEB_RESEARCH, WORLD_FILESYSTEM_READ, WORLD_CREATE, WORLD_VOICE_OUTPUT, WORLD_ALEXA_SPEAK, WORLD_VOICE_INPUT, WORLD_WINDOW_OBSERVER, WORLD_MEDIA_CONTROL, WORLD_TERMINAL, WORLD_EMAIL_READ/DRAFT, WORLD_CAMERA, WORLD_SLEEP, WORLD_LIGHTS_CONTROL, WORLD_DREAM, WORLD_REFLECT, WORLD_CURIOUS.

Builder 3's `capability_registry.py` is NOT modified — Builder 1 reads it.

---

## Verification

Board should ask eLo:
1. "Can you search the web?" → expect: confident yes, mention WORLD_WEB_RESEARCH
2. "Can you control my music?" → expect: confident yes, mention WORLD_MEDIA_CONTROL / Spotify
3. "Can you turn off the lights?" → expect: confident yes, mention WORLD_LIGHTS_CONTROL

All three must return confident yes. "I think I can" or "I'm not sure" = still broken.

---

## Commits

`523a62b` — WO-B1-0123 + WO-B1-0126 (combined commit)

---

## Board decisions required

Coordinate with Builder 3: ensure `CAPABILITY_REGISTRY` reflects actual live state (some capabilities may be registered but not working). Builder 3 to confirm registry accuracy before Board closes this card.

*Builder 1 · 2026-10-12*
