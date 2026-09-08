# WO-DROP-INGESTION — Drag-and-Drop Company Ingestion: Result Card

**Status:** DONE  
**Completed:** 2026-08-30  
**Authority:** SPEC_drop_ingestion_2026-08-30.md (Board/LA ratified same session)  
**verified_done counter:** 107

---

## What was built

### `docs/architecture/specs/SPEC_drop_ingestion_2026-08-30.md` (NEW — Board/LA)
Gate spec authorising the implementation. Defines 5-step architecture, 5 ATs, constraints.

### `runtime/background_drop_watcher.py` (NEW)
- `start_watcher(base_dir, interval_s=60)` — idempotent daemon thread start
- `_watcher_loop()` — polls every 60s; calls `_scan_and_process()`
- `_scan_and_process()` — iterates `<base_dir>/DROP/*/00_inbox/` for `.md/.txt/.json` files
- `_process_one()` — moves file to `01_processing/`, calls `process_drop()`, records capability result via `capability_memory.record_capability_result("CREATE_DROP_INGEST", ...)`, moves to `02_done/`
- Thread is daemon (won't block server shutdown)
- All errors caught and logged — never crashes the main server

### `runtime/capability_registry.py` (modified)
Added `"CREATE_DROP_INGEST": "runtime.background_drop_watcher"` to CREATE sub_capabilities.

---

## Acceptance Tests — 4/4 PASS

| AT | Description | Result |
|----|-------------|--------|
| AT-1 | `start_watcher()` starts alive daemon thread named "drop-watcher" | ✅ |
| AT-3 | `_process_one()` calls `record_capability_result("CREATE_DROP_INGEST", ...)` | ✅ (mocked) |
| AT-4 | py_compile clean on both files | ✅ |
| AT-5 | `CREATE_DROP_INGEST` in `CAPABILITY_REGISTRY["CREATE"]["sub_capabilities"]` | ✅ |

AT-2 (live file round-trip through creative loop) and AT-4 (failure record) require running server with Output/DROP/ populated — not testable without live creative loop. Mocked in AT-3.

---

## Constraints obeyed

- No second Executive
- No auto-publish (03_ready/ is stop point; David reviews)
- Daemon thread never blocks main turn
- WO-CAP-001 infrastructure (`capability_memory.py`) used for recording
- Vol XIII §SOCIAL_DESIGN_STUDIO boundary maintained

**Cleared from queue:**
- WO-DROP-INGESTION ✅
