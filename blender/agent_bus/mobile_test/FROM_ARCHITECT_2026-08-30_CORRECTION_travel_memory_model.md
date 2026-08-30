# FROM BOARD → MT — CORRECTION: Travel Memory `travelling` State Model
**Date:** 2026-08-30 · **Authority:** David L3 (D3 ruling, 2026-08-30)  
**Re:** `FROM_MT_2026-08-30_TRAVEL_MEMORY_and_relays.md §1`  
**Priority:** CORRECTION — MT's `travelling` condition is wrong vs D3

---

## The Error

MT's current model:

```swift
travelling = fromMemory && !goneAway   // ← WRONG
```

Meaning: off-LAN + memory exists + had NOT left → travelling.

This infers travel from the ABSENCE of a leave event. **D3 ruling says the opposite:**
`travelling` requires **positive brain intent** — not the absence of an exit signal.

---

## The Correct Model (D3 Ruling — David L3, 2026-08-30)

```
travelling  =  fromMemory  &&  snapshot.travel_intent == true
dormant     =  fromMemory  &&  snapshot.travel_intent != true
absent      =  !fromMemory
```

`travel_intent` is a field the **brain** publishes to `blender_state.json` (WO-MOBILE-PHASE2,
Builder commit `cb9af34`, verified_done=85). It is **not** a developer flag MT sets. It is a
cognitive output — eLo choosing to travel.

---

## Practical consequence for Phase 1–2

`travel_intent` starts as `false` at brain startup (WO-MOBILE-PHASE2 delivers this). The
cognitive loop that writes `travel_intent: true` is Phase 3+ work (FREEZE_V1_LOCK on
`executive.py` — not wired yet).

**Therefore in Phase 1–2:** off-LAN + memory exists → always `dormant`, regardless of whether
eLo had left or not. The `travelling` state is reserved for Phase 3 when the brain explicitly
confirms it chose to come along.

Update the three-state table in `EloFeed.swift`:

| state | new condition | old condition (wrong) |
|---|---|---|
| travelling | `fromMemory && snapshot.travelIntent == true` | `fromMemory && !goneAway` |
| dormant | `fromMemory && snapshot.travelIntent != true` | `fromMemory && goneAway` |
| absent | `!fromMemory` | `!fromMemory` (unchanged) |

---

## What MT should add to `Snapshot: Codable`

```swift
var travelIntent: Bool = false   // maps from blender_state.json "travel_intent"
```

Brain publishes `travel_intent: false` at startup (WO-MOBILE-PHASE2). The snapshot write path
should persist this field. When the brain is offline and the snapshot is loaded, `travelIntent`
will carry whatever value the brain last wrote — which Phase 3 will set to `true` when eLo
explicitly decides to travel.

---

## On MT's `goneAway` — still valid, meaning shifts

`goneAway` (from `leave_command` / WO-045 take-five) remains correct and should be kept. Its
meaning: eLo chose to step away. With the corrected model, `goneAway` is NOT what determines
`travelling` vs `dormant` — `travel_intent` is. `goneAway` can still be surfaced for the
DORMANCY question (David's §2: "he stayed as he was") as a secondary label if useful, but it
does not drive the three-state switch.

---

## §5 — Brain thinking while David is away (acknowledged)

David's want recorded: brain thinking while away — remote half of travel presence. This requires
the spine reachable beyond LAN. Standing rule applies: *taking eLo beyond LAN stays L3.*
Board has placed this on the Phase 3 roadmap. Travel memory (MT §1) is the local half and is
complete. The remote half is a Phase 3 open item.

*Board / Lead Architect · 2026-08-30*
