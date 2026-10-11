# Board Review — 0086: Capability Status Anchor
**Date:** 2026-10-11
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

---

## Card scope

eLo stops denying Spotify while it's playing. Inject `capabilities_block()` from
`tools/capability_status.py` into the system prompt so eLo knows what's live.

---

## Implementation status at review time

Already wired. `runtime/prompt_builder.py:640-663`:

```python
# ── WO-ROOT-7-B1-WIRE: live capability state — prevents denying active tools ─
# Inject when user_input contains a capability keyword. Always inject on task-execution actions.
CAPABILITY_KEYWORDS = (
    "capability", "capabilities", "tools", "spotify", "search", ...
)
if any(kw in user_input_lc for kw in CAPABILITY_KEYWORDS) or action_requires_cap:
    from tools.capability_status import capabilities_block as _cap_block_fn
    _cap_live = _cap_block_fn()
    if _cap_live:
        _push("capability_live_state", "\n## What I can do right now\n" + _cap_live)
```

Assembled prompt for "what can you do with spotify" contains "What I can do right now" ✅

---

## Tests

```
tests/test_b3_capability_status.py — 18 passed in 2.41s
```

Manual check: `build("what can you do with spotify")` → "What I can do right now" FOUND ✅

---

## Board decisions required

None. Implementation and tests already passing.

*Builder 1 · 2026-10-11*
