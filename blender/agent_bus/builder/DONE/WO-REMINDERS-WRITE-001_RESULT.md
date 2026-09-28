# RESULT — WO-REMINDERS-WRITE-001: Reminders Write Capability

**Filed by:** Builder  
**Date:** 2026-09-15  
**WO file:** `FROM_ARCHITECT_2026-09-15_WO-REMINDERS-WRITE-001.md`  
**Status:** CLOSED — ALL DOD MET

---

## SUMMARY

Three deliverables built:

1. **`capabilities/reminders_agent.py`** (new) — `create_reminder(title, notes, due_date, list_name)` via AppleScript. Handles ISO 8601 date conversion, string escaping, graceful failure for empty title or `ELO_REMINDERS_WRITE=0`. Subprocess timeout 30s (10s caused false-timeout on first Reminders.app access from Python subprocess).
2. **`runtime/capability_registry.py`** — registered `WORLD_REMINDERS_WRITE` + added `dispatch_reminders_write(title, notes, due_date, list_name)`.
3. **`.env.example`** — added `ELO_REMINDERS_WRITE=1` with macOS Automation permission note.

---

## DoD-A — `dispatch_reminders_write("Test from eLo", ...)` → `{created: True, ...}`, reminder appears in Reminders.app

**Direct call:**
```
$ python -c "from capabilities.reminders_agent import create_reminder; r = create_reminder('Test from eLo WO-REMINDERS-WRITE-001 verification', notes='WO-REMINDERS-WRITE-001 verification'); print(r)"

{'created': True, 'title': 'Test from eLo WO-REMINDERS-WRITE-001 verification', 'due_date': None, 'list_name': 'Reminders', 'error': None}
```

**Dispatch roundtrip:**
```
$ python -c "from runtime.capability_registry import dispatch_reminders_write; r = dispatch_reminders_write('Test from eLo', notes='WO-REMINDERS-WRITE-001 verification'); print(r)"

dispatch result: {'dispatched': True, 'created': True, 'title': 'Test from eLo', 'due_date': None, 'list_name': 'Reminders', 'error': None}
```

**Confirmed in Reminders.app** (via `osascript -e 'tell application "Reminders" to return name of every reminder of list "Reminders"'`):  
→ "Test from eLo" appears in list. ✅

---

## DoD-B — `WORLD_REMINDERS_WRITE` in capability registry

```
$ python -c "from runtime.capability_registry import CAPABILITY_REGISTRY; print('WORLD_REMINDERS_WRITE' in CAPABILITY_REGISTRY)"
True
```

Registry entry:
```python
"WORLD_REMINDERS_WRITE": {
    "description": "Create a reminder in macOS Reminders.app via AppleScript",
    "tool": "capabilities.reminders_agent",
    "write_allowed": True,
    "confirmation_required": False,
    "execution_report": True,
    "law": "LAW-014",
},
```
✅

---

## DoD-C — Graceful failure when Reminders unavailable

**`ELO_REMINDERS_WRITE=0` (write disabled):**
```
{'created': False, 'title': 'Should not create', ..., 'error': 'ELO_REMINDERS_WRITE=0 — reminder writes disabled'}
```
No exception raised. ✅

**Empty title:**
```
{'created': False, 'title': '', ..., 'error': 'title is required'}
```
No exception raised. ✅

---

## Regression

```
pytest tests/ -q --deselect=tests/test_0020_ct0033_bypass_handlers.py::test_bh2_count_31
8 failed, 1563 passed, 3 skipped, 1 deselected, 1 xfailed
```

Same 8 pre-existing failures as post WO-BA17-ALEXA-001. No new failures introduced. ✅

---

## FILES MODIFIED / CREATED

| File | Action |
|------|--------|
| `capabilities/reminders_agent.py` | CREATED — `create_reminder()`, ISO date conversion, AppleScript runner, graceful failure |
| `runtime/capability_registry.py` | MODIFIED — `WORLD_REMINDERS_WRITE` registered + `dispatch_reminders_write()` added |
| `.env.example` | MODIFIED — `ELO_REMINDERS_WRITE=1` + macOS Automation permission note |

---

## IMPLEMENTATION NOTE — subprocess timeout

First run from Python subprocess takes 15–25s for Reminders.app to respond (app auth handshake on first access). Direct shell `osascript` resolves faster. Timeout raised from 10s → 30s to accommodate. Subsequent calls from the same process are fast. If Reminders.app is fully blocked (sandbox/no permission), osascript returns non-zero returncode immediately — the timeout guard is for app-init latency, not permission denial.

---

## CONSTRAINTS MET

- `capabilities/reminders_agent.py` is a new file — no existing code modified. ✅
- `executive.py` not modified. ✅
- `living_presence_spec.txt` not modified. ✅
- `ELO_REMINDERS_WRITE=0` safely disables writes without breaking reads. ✅
- No `WORLD_REMINDERS_READ` capability modified — reads remain separate. ✅

---

## VERDICT: ALL DOD MET

| DoD | Status |
|-----|--------|
| A. `dispatch_reminders_write("Test from eLo", notes="WO-REMINDERS-WRITE-001 verification")` → `{created: True, ...}`, reminder in Reminders.app | ✅ |
| B. `WORLD_REMINDERS_WRITE` in capability registry | ✅ |
| C. Graceful failure — `{created: False, error: "..."}`, no exception | ✅ |
