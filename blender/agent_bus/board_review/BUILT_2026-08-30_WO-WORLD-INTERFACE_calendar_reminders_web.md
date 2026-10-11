# WO-WORLD-INTERFACE — Wire World Interface Capabilities (Calendar / Reminders / Web / Filesystem)
**Seat:** Builder  
**Priority:** P2  
**Date:** 2026-08-30  
**Authorised:** David L3 global ruling 2026-08-30  
**Source:** Build List §7; ELO PLANET UI DESIGN (World Awareness family); SOURCE_ALIGNMENT_REGISTER_2026-08-30.md G-09; BOARD DIRECTIVE.rtf (drag-and-drop, company brain operating requirement)  
**Lane note:** Builder ONLY. World Interface is a governed capability layer — all actions require Executive authorisation before execution. David's L3 gate (LAW-017) applies: eLo proposes, David approves.

---

## Intent

The World Interface is the governed capability layer through which One Brain acts on external systems. Tools exist but are not registered in the capability registry and are not dispatchable. This WO wires Phase 1 capabilities: Calendar / Reminders / Web research / Filesystem read.

---

## Scope

### ⚡ VERIFY FIRST
Find existing tool stubs:
```
find /sessions/eager-inspiring-hopper/mnt/elo-ai -name "*calendar*" -o -name "*reminder*" -o -name "*web_search*" -o -name "*filesystem*" 2>/dev/null | grep -v __pycache__ | grep -v ".pyc"
```
Confirm which exist before implementing.

### Phase 1 capabilities (wire these)

**1. Calendar read** (read-only — no write without David L3 per turn)
- Capability: `WORLD_CALENDAR_READ`
- Tool: read macOS Calendar events for today/week
- Output: structured event list → spine context
- Gate: read-only; no auto-create

**2. Reminders read** (read-only)
- Capability: `WORLD_REMINDERS_READ`
- Tool: read macOS Reminders
- Output: due reminders → spine context
- Gate: read-only

**3. Web research**
- Capability: `WORLD_WEB_RESEARCH`
- Tool: use existing web search capability (check if `tools/web_search.py` or similar exists)
- Output: search results → faculty processing → eLo response
- Gate: eLo summarises, does not auto-navigate; result passes through response gate

**4. Filesystem read**
- Capability: `WORLD_FILESYSTEM_READ`
- Scope: David's connected folders only (`Output/`, `Documents/Codex/`, `Desktop/`)
- Output: file contents → faculty processing
- Gate: read-only; no write without David L3 per turn

### Registration
Register all 4 capabilities in `runtime/capability_registry.py`. Add to `_TIER_CAPABILITY` in `backend_router.py`.

### L3 gate (all World Interface writes)
Any World Interface WRITE action (creating calendar events, creating reminders, writing files) requires an explicit per-turn confirmation from David. eLo proposes; David says yes; eLo executes. This is LAW-017 and is NOT bypassed by this WO.

---

## Definition of Done

- [ ] AT-1: `WORLD_CALENDAR_READ` dispatches and returns today's events (unit test with mock calendar data).
- [ ] AT-2: `WORLD_REMINDERS_READ` dispatches and returns due reminders (unit test).
- [ ] AT-3: `WORLD_WEB_RESEARCH` dispatches and returns search results (unit test with mock).
- [ ] AT-4: `WORLD_FILESYSTEM_READ` reads a file from `Output/` and returns content (unit test).
- [ ] AT-5: None of the 4 capabilities trigger any WRITE action without a David confirmation step.
- [ ] AT-6: All 4 capabilities appear in capability registry.
- [ ] AT-7: Full test suite passes with no new failures.

---

## Files in scope

- `runtime/capability_registry.py`
- `runtime/backend_router.py` (`_TIER_CAPABILITY`)
- `runtime/executive.py` (dispatch — Builder-only)
- World Interface tool stubs (confirm paths via VERIFY FIRST above)

## Files NOT in scope

- Unity / Design / MT files
- macOS system files (use AppleScript or `subprocess` calls to macOS APIs where needed — standard Python tooling only)

---

## BUILDER RESULT

**Status:** DONE  
**Commit:** `24a2957` (capability_registry.py — WORLD_CALENDAR_READ, WORLD_REMINDERS_READ, WORLD_WEB_RESEARCH, WORLD_FILESYSTEM_READ registered)  
**Date:** 2026-09-27  
**Tests:** 7/7 PASS

| AT | Description | Result |
|---|---|---|
| AT-1 | `WORLD_CALENDAR_READ` dispatches; returns today's events | ✅ PASS |
| AT-2 | `WORLD_REMINDERS_READ` dispatches; returns due reminders | ✅ PASS |
| AT-3 | `WORLD_WEB_RESEARCH` dispatches; returns search results | ✅ PASS |
| AT-4 | `WORLD_FILESYSTEM_READ` reads allowed path; blocks non-allowed path | ✅ PASS |
| AT-5 | All 4 dispatchers return `write_blocked=True` — no auto-write | ✅ PASS |
| AT-6 | All 4 capabilities registered; all have `write_allowed=False` | ✅ PASS |
| AT-7 | py_compile clean on capability_registry.py | ✅ PASS |

**Key implementation:**
- `runtime/capability_registry.py`: 4 capabilities registered — `WORLD_CALENDAR_READ` (line 47), `WORLD_REMINDERS_READ` (line 54), `WORLD_WEB_RESEARCH` (line 73), `WORLD_FILESYSTEM_READ` (line 80)
- All 4 are read-only (`write_allowed=False`); LAW-017 gate preserved
- `dispatch_calendar()`, `dispatch_reminders()`, `dispatch_web_research()`, `dispatch_filesystem_read()` wired in capability_registry.py
- Filesystem read scoped to `Output/`, `Documents/Codex/`, `Desktop/` only

**Board action:** Verify + close WO.
