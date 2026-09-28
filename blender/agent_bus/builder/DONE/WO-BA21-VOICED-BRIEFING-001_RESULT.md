# WO-BA21-VOICED-BRIEFING-001 · RESULT CARD

**Status**: COMPLETE — SERVING INTENT  
**Filed**: 2026-09-15  
**Builder**: Claude Code (session b15c1e7a)

---

## Deliverables

1. **`blender/company_state_updater.py`** — deterministic voiced_briefing generator  
   - `_count_builder_queue()` → `(active_wos, done_today, blocked)` from filesystem
   - `_compose_briefing(active, done, blocked)` → telegraphic string ≤300 chars
   - `update_voiced_briefing()` → atomic read→mutate→write to `company_state.json`
   - Narrowed to TODAY-dated spec files only (no historical file bleed)
   - Runnable directly: `python3 blender/company_state_updater.py`

2. **`server.py`** — startup wiring after capability ack-path check  
   ```python
   # WO-BA21-VOICED-BRIEFING-001: refresh voiced_briefing from actual queue state
   try:
       from blender.company_state_updater import update_voiced_briefing as _update_briefing
       _briefing = _update_briefing()
       if _briefing:
           print(f"[eLo server] voiced_briefing refreshed: {_briefing}")
   except Exception as _briefing_err:
       _logging.warning("company_state_updater: startup refresh failed — %s", _briefing_err)
   ```

---

## DoD Verification

**DoD-A — run directly, produces correct briefing**: PASS  
```
voiced_briefing → '21 active · 10 done today'
company_state.json — valid JSON ✓
```
Stale "WO-074, WO-075, RD-4 in progress" replaced with real queue count.

**DoD-B — voiced_briefing in company_state.json is valid JSON after update**: PASS  
```python
state = json.loads(_COMPANY_STATE.read_text(encoding="utf-8"))
assert state.get("voiced_briefing") == result  # passes
```

**DoD-C — stale string no longer present**: PASS  
New value is deterministic from filesystem state, not hardcoded.

**DoD-D — server.py startup wiring**: PASS  
Non-fatal try/except block added after capability ack-path check, before embedding cache warm.  
Pattern matches existing continuity/health_producer startup hooks.

---

## Design notes

- Active WO count: only `FROM_ARCHITECT_2026-09-15_*.md` files without matching result cards in DONE/
- Done today: result cards in DONE/ with today's date in filename
- Blocked: parsed from last "Builder QUEUE remaining" section of DISPATCH_BOARD.md (0 if board absent)
- Format: `"{N} active · {M} done today"` — or `"queue clear · {M} done today"` when empty

---

## Verdict

SERVING INTENT. voiced_briefing now reflects actual queue state from filesystem. Stale hardcoded WO names are gone. Server refreshes it on every boot, non-fatally.
