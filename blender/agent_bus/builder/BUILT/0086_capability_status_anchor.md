# WO-0086 — Capability Status Anchor
**Seat:** Builder 1  
**Priority:** P1  
**Date:** 2026-10-11  
**Commit:** (already in repo — see `prompt_builder.py` lines 640-649)

## What was found

Already implemented. `runtime/prompt_builder.py:640-649` contains:

```python
# ── WO-ROOT-7-B1-WIRE: live capability state ──────────────────────────
try:
    from tools.capability_status import capabilities_block as _cap_block_fn
    _cap_live = _cap_block_fn()
    if _cap_live:
        _push("capability_live_state", "\n## What I can do right now\n" + _cap_live)
except Exception:
    pass
```

Section key is `capability_live_state`, heading is `## What I can do right now`. Injected after `self_block`, before personality.

## Test
18/18 `tests/test_b3_capability_status.py` pass.

*Builder 1 · 2026-10-11*
