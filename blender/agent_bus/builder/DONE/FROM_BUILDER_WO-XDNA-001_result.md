# WO-XDNA-001 — Result: Per-Turn Experience Identity (XDNA)

**Date:** 2026-09-20  
**WO:** WO-XDNA-001  
**Source:** `docs/architecture/EXPERIENCE_DNA_CANON_2026-08-23.md` · `docs/architecture/EXPERIENCE_DNA_DECISION_RECORD_2026-08-23.md`  
**Seat:** Builder  
**Status:** CLOSED — IMPLEMENTED (housekeeping card)

---

## What was done

Implemented `runtime/experience_id.py` — per-turn authoritative experience identity for eLo OS.

### Implementation

| Item | Detail |
|---|---|
| File | `runtime/experience_id.py` |
| Format | `ELO-{4 alphanum}-{4 alphanum}` (e.g. `ELO-X7K4-92A1`) |
| Charset | a-z A-Z 0-9 (62 chars). 8 random chars → ~2.8 trillion distinct values. |
| Semantics | No semantic content. Cannot be decoded. Machine-stable for full lifetime of one turn. |
| Thread safety | Single-threaded per turn (One Brain). `_CURRENT` set once at run() entry, read by all downstream writes within the same call stack. No locking required. |

### Functions

| Function | Purpose |
|---|---|
| `mint()` | Called by `spine.py` at top of every `run()` call, before any faculty processing. Sets `_CURRENT`. Returns the new ID. |
| `get()` | Called by any write site within the same turn (decision_journal, route_memory, last_significance.json, vault_layer, lessons_ledger). Returns `_CURRENT` or `""` if not minted. |
| `is_valid(xid)` | Returns True if xid matches `^ELO-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}$`. |

### Wiring confirmed

| Call site | Line | Usage |
|---|---|---|
| `runtime/wkg_faculty.py` | 161, 220 | `experience_id: str | None` param + written to WKG entries |
| `runtime/background_drop_watcher.py` | 61, 64 | `from runtime.experience_id import get as _get_xid` + passed as `experience_id=_get_xid()` |

---

## Status

IMPLEMENTED. No live AT suite run (housekeeping card — WO was already implemented when this card was written). Wiring confirmed by code inspection 2026-09-20.

*Builder · 2026-09-20*
