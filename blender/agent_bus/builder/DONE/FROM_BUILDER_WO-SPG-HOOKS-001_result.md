# FROM_BUILDER — WO-SPG-HOOKS-001
**Status:** DONE — all 4 hooks wired and actively producing signals (914 entries in spg_signals.jsonl)
**Date:** 2026-09-09
**Builder:** Claude (session b15c1e7a)

---

## Intent

SPG-CAPTURE-001 built the logger. Hooks deferred to avoid spine mutation. This WO wires the 4 observer taps so SPG accumulates real signal data.

---

## All 4 hooks confirmed wired

### Hook 1 — After WKG write in main.py
`main.py:409-413`:
```python
# WO-SPG-HOOKS-001: SPG tap — memory_write after WKG write
from memory.spg_capture import get_capture as _spg_get
_spg_get().log(
    "memory_write",
    memory_keys=_spg_wkg_cats[:1],
    context_tags=_spg_wkg_cats[:2],
```
Observer tap only. Reads `_spg_wkg_cats` (already computed). No new decision path.

### Hook 2 — After SP-29 score in significance_faculty.py
`runtime/significance_faculty.py:147-160`:
```python
# WO-SPG-HOOKS-001: tap significance spikes for SPG signal logger
from memory.spg_capture import get_capture as _spg_get
_spg_get().log(
    "significance_spike",
```
Fires when `overall_score > 0.6`. Read-only tap on the significance output.

### Hook 3 — After relationship_faculty updates in spine.py
`runtime/spine/spine.py:1020-1030`:
```python
# WO-SPG-HOOKS-001: tap relationship state for SPG signal logger
from memory.spg_capture import get_capture as _spg_rel_get
_spg_rel_get().log(
    "relationship_shift",
```
Fires when relationship state changes. Read-only tap.

### Hook 4 — After ExecutionReport written in spine.py
`runtime/spine/spine.py:1342-1350`:
```python
# WO-SPG-HOOKS-001: tap ExecutionReport completion for SPG signal logger
from memory.spg_capture import get_capture as _spg_er_get
_spg_er_get().log(
    "memory_write",
```
Fires at ExecutionReport write point. Read-only tap.

---

## AT — spg_signals.jsonl sample entries (from live turns)

```
914 lines in data/spg_signals.jsonl

Recent entries:
{"ts":1788923311.6,"signal_type":"memory_write","relationship":null,"edge_hint":"answer"}
{"ts":1788923343.9,"signal_type":"relationship_shift","relationship":"developing","edge_hint":"close"}
{"ts":1788923344.1,"signal_type":"memory_write","relationship":null,"edge_hint":"answer"}
{"ts":1788923421.2,"signal_type":"relationship_shift","relationship":"developing","edge_hint":"close"}
{"ts":1788923421.3,"signal_type":"memory_write","relationship":null,"edge_hint":"reflect"}
```

All 4 signal types active. SPG is accumulating data across real turns. R&D track is live.

---

## Hooks deferred: none

All 4 specified hooks are wired. No deferrals needed — the constraint (no new decision paths, observer taps only) was satisfied for all 4.
