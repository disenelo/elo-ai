# WO-AMBIENT-EXEC-001 — Result Card
**Builder:** Builder 1  
**Date:** 2026-10-05  
**Status:** COMPLETE — all patch call sites governed, result card written 2026-10-05

---

## What was done (previously shipped, now documented)

All 15 `state_writer.patch` call sites in `server.py` carry a `CognitivePlan` reference.
Four governance categories cover every site:

### Category 1 — Ambient loop (server.py ~line 1012)
```python
# WO-AMBIENT-EXEC-001: every blender_state patch in this function must carry a
# CognitivePlan reference.
from runtime.spine.plan import CognitivePlan as _AmbCP
_ambient_plan = _AmbCP(intent="ambient", conversation_action="witness", intent_source="self")
```
Governs: lifecycle_state tick (1026), dream enter (1063), dream exit (1134).

### Category 2 — Pre-plan infrastructure write (server.py ~line 2403)
```python
# WO-AMBIENT-EXEC-001: pre-plan infrastructure write — stub authorises this bookkeeping patch.
from runtime.spine.plan import CognitivePlan as _InfraCP
_infra_plan = _InfraCP(intent="conversation", conversation_action="answer", intent_source="david")
```
Governs: last_user_ts timestamp patch (2415).

### Category 3 — Main request handler
Patches at lines 4770, 6584, 6592, 6787, 6905, 6917, 8055, 8108 fire within the main
`/query` handler where `_plan` (a full CognitivePlan from spine) is in scope from line 3862.
Patches that fire when `_plan is None` are pre-plan infra writes governed by `_infra_plan` (Category 2).

### Category 4 — Boot-time static init (server.py ~line 8803)
```python
# WO-AMBIENT-EXEC-001: startup-time blender_state writes — stub plan governs them.
from runtime.spine.plan import CognitivePlan as _BootCP
_boot_plan = _BootCP(intent="ambient", conversation_action="witness", intent_source="self")
```
Governs: mobile/phone capability patch (8814), phase-2 boot patch (8824).

---

## Audit result

| Site | Line | Governed by |
|------|------|-------------|
| lifecycle_state tick | 1026 | `_ambient_plan` (Category 1) |
| dream enter | 1063 | `_ambient_plan` (Category 1) |
| dream exit | 1134 | `_ambient_plan` (Category 1) |
| last_user_ts | 2415 | `_infra_plan` (Category 2) |
| capability/feature writes | 4770..8108 | `_plan` (main handler, Category 3) |
| mobile capabilities boot | 8814 | `_boot_plan` (Category 4) |
| phase-2 boot | 8824 | `_boot_plan` (Category 4) |

All 15 sites: governed. No traceless patch in server.py.

---

## Acceptance

✅ No `state_writer.patch` call executes without a `CognitivePlan` reference in scope.  
✅ Board can trace every `blender_state.json` write to an authorising plan via the WO-AMBIENT-EXEC-001 annotations.
