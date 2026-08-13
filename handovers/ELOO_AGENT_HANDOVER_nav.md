# eLo OS Agent Handover — Navigation Event Emission

## What Unity already does

`EloOSAvatarReceiver.cs` polls `blender_state.json["user_nav_event"]` every 250ms. When it detects a new `_ts` (newer than last seen), it calls `DesktopBuddy.ExecuteNav(type, target)`. Unity then executes the jump/shift/wander/come-back.

**Nav types Unity understands:**
- `shift_left`, `shift_right` — slide along the current window edge
- `wander` — pick a random position on the current edge
- `come_back` — re-attach to the nearest window
- `jump_top`, `jump_bottom`, `jump_left`, `jump_right` — jump to an edge of the current window
- `jump_to_app` + `target` — jump to the named app's window (e.g. `target="Finder"`)
- `move_screen` + `target` — move to another monitor

Unity side is complete.

---

## Current eLo OS state

`tool_router.py` already implements nav:
- `_parse_nav(user_input)` → `(nav_type, target)` 
- `_write_nav_event(nav_type, target)` → writes `user_nav_event: {type, target, _ts}` to blender_state.json
- Triggered by `_MOVEMENT_COMMAND_PHRASES` match in `enrich()`

This is working. The gaps are coverage and coherence.

---

## What eLo OS must fix / extend

### 1 — Extend `_MOVEMENT_COMMAND_PHRASES` in `runtime/executive.py`

Current list misses natural David phrasings. Add:

```python
_MOVEMENT_COMMAND_PHRASES = (
    # existing phrases ...
    # new:
    "wander about", "wander around", "go for a wander",
    "come here", "get over here", "come over here",
    "go over there", "move over there", "go to the other side",
    "tuck yourself in", "tuck in",
    "go sit on", "perch on", "sit on top of",
    "move yourself over", "shift yourself",
    "go to the other screen", "other monitor", "other display",
    "move to another screen", "go to screen",
    "other window", "go to the other window",
)
```

### 2 — Extend `_parse_nav()` in `tool_router.py` to cover the new phrases

Add patterns for natural commands that don't currently map cleanly:

```python
# after existing patterns in _parse_nav():
if "wander" in t or "go for a wander" in t:
    return "wander", ""
if "come here" in t or "come over here" in t or "get over here" in t:
    return "come_back", ""
if "other screen" in t or "other monitor" in t or "other display" in t:
    return "move_screen", "next"
if "other window" in t or "go to the other window" in t:
    return "jump_to_app", ""   # Unity will pick nearest if target is empty
if re.search(r"sit on(?:\s+top of)?\s+(.+)", t):
    m = re.search(r"sit on(?:\s+top of)?\s+(.+)", t)
    return "jump_to_app", m.group(1).title() if m else ""
```

### 3 — Nav events must survive a full state write

**Problem**: `_write_nav_event` does a read-merge-write. Then when the next response fires `_state_write()`, it overwrites blender_state.json entirely, dropping `user_nav_event` before Unity polls it.

**Fix**: Unity's `EloOSAvatarReceiver.cs` polls at 250ms. A nav event written at T=0 may be overwritten at T=100ms (the server's write after generating the response). Unity may miss it.

The existing workaround: Unity checks `_ts` — as long as the event timestamp changes, Unity fires. But if the state write happens faster than the poll, the event is lost.

**Reliable fix**: nav events should NOT be overwritten by subsequent `_state_write` calls. Add to `state_writer.py`:

```python
_PRESERVE_KEYS = {"user_nav_event", "exit_event"}   # these are consumed by Unity, never overwritten by eLo OS

def _write(payload: dict) -> bool:
    # Preserve keys that Unity consumes on its own cadence
    try:
        with open(_STATE_PATH, encoding="utf-8") as f:
            prev = json.load(f)
        for k in _PRESERVE_KEYS:
            if k in prev and k not in payload:
                payload[k] = prev[k]
    except Exception:
        pass
    # ... existing tmp write ...
```

This means nav events persist until Unity increments its `_ts` reader past them (which happens on the next poll after the event fires — Unity then clears the consumed state).

Actually simpler: Unity clears the event on consumption by checking if `_ts` > `_last_nav_ts`. It doesn't re-write. So the preserve is one-directional — eLo OS must not drop the key until Unity has polled at least once.

The `_PRESERVE_KEYS` approach above is the correct solution. Add it to `state_writer._write()`.

---

## Verify

```bash
cd ~/elo-ai
python3 -c "
import json, time, os
from tools.tool_router import _write_nav_event, _parse_nav
nav, target = _parse_nav('hey can you shift left')
print('parsed:', nav, '|', target)
_write_nav_event(nav, target)
with open('blender/blender_state.json') as f: s = json.load(f)
print('event:', s.get('user_nav_event'))
"
```

Expected: `parsed: shift_left |  | event: {'type': 'shift_left', 'target': '', '_ts': ...}`

---
Architecture authority: `17_behaviour_faculty.md`, `09_executive_faculty.md`
Written: 2026-07-05
