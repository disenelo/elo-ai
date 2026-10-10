# 01_BUG_desktop_perception_dead.md — LIVE BUG: eLo's desktop perception is silently DEAD

**WO:** WO-096 · **Seat:** builder · **Priority:** P0 (live runtime defect) · **Reserved?** no
**Found:** Architect audit 2026-08-10, reproduced by running `assemble_world_state()`.

## The bug
`world/live_world_state.py:194` imports **`get_active_window`** from `desktop/window_state.py` — **that module
defines only `get()`.** The resulting `ImportError` is swallowed by a **bare `except`**, so the failure is
silent and **the desktop domain comes back `absent` on EVERY TURN.**

**The same broken import is duplicated at `perception_faculty.py:337`.**

## Why this matters (not just tidiness)
eLo is supposed to know what's on David's screen — that's the foundation of situated cognition, the
"how's the company / what am I looking at" awareness, and every spatial behaviour. Right now that channel
silently returns nothing and **nobody was told**, because the exception is eaten. This is exactly the class of
failure ADR-Exec-001 exists to prevent: the system believing it perceived something when it perceived nothing.

## Scope — exactly this
1. **Fix the import** in `world/live_world_state.py:194` and `perception_faculty.py:337` — call the function
   that actually exists (`get()`), or add a properly-named wrapper in `desktop/window_state.py`. One fix,
   both call sites — do not fix one and leave the other to drift.
2. **Kill the bare `except`.** A perception source failing must be **logged and surfaced**, never silently
   swallowed. If a domain can't be read, it must be recorded as an explicit `error`/`unavailable` state,
   distinguishable from a genuine "nothing there."
3. **Sweep for the same pattern** — any other bare `except` hiding an import/perception failure in the
   world-state or perception path. Report what you find.

## Test (without David)
Assert `assemble_world_state()` returns a POPULATED desktop domain (not `absent`) when a window is present ·
assert a deliberately broken perception source produces a logged, explicit error state rather than a silent
`absent` · assert both call sites use the same working function.

## Done when
implemented + test green + committed → append hash, move to DONE/, outbox line, take next card.
**David's bar:** eLo actually knows what's on screen, and if he doesn't, he says so instead of pretending.

## Result — DONE 2026-08-13

**Commit:** `08edd9d`
**Tests:** 5/5 AT green (`tests/test_wo096_desktop_perception.py`)

### What was fixed
- `world/live_world_state.py:196` — `get_active_window` → `from desktop.window_state import get as _ws_get`; `.get("app")` / `.get("title")` dict access → `.app` / `.title` dataclass attributes; bare `except` → `logging.warning` + `_health("desktop", "error", ...)` + `_degrade("desktop")`
- `faculties/perception/perception_faculty.py:337` — same import fix + attribute access; bare `except pass` → `logging.warning`
- Blender state bare `except` in both files → `logging.debug` (non-critical)

### Bare-except sweep (scope item 3)
No other silent import/perception failures found in world-state or perception path. All remaining bare excepts in `live_world_state.py` are on non-perception domains (music, unity, environment) and have been left untouched per "don't add what wasn't asked for."
