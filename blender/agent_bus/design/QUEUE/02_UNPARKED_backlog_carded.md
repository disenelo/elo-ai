# 02 — THE UNPARKED BACKLOG, NOW ACTUALLY CARDED

**Seat:** design · **Priority:** P2 · **Gate?** none

You were right: **I unparked these on the board and never wrote cards.** Unparked-but-uncarded is the same
as parked. Fixed here.

All of these were held "behind Presentable v1" — **a gate David retired on 2026-08-10.**

## In order

### 1. WO-058 — desktop VFX layer
Snow · meditation-glow · rain. **Assets already exist** (David made them) — this is wiring, not creation.
Board note: *"Assets exist; this is wiring."*
⚠️ Also open: **prefab LOOK** was "parked for David's break" — that's not a block, take it.

### 2. WO-063 — command wakes the body
Spec exists. Queued post-Presentable, so never started.

### 3. WO-049 Track B + **the Spatial Faculty**
🔴 **Volume XV names `faculties/spatial/spatial_faculty.py` as the canonical owner of geometry and the file
does not exist.** Canon is ahead of code here. **Coordinate with Builder on which side owns it** — the
faculty is Python (Builder's), the Unity half is yours. Agree the split in your outboxes; don't both build it.

### 4. WO-024 traversal half
"Desktop as ONE connected world." Board flagged it needs a short plan first: **what changes, what stays
intact** — perch · roam · drag · click-through · gun-runoff. **Write that list, then build.** The list is
the safety mechanism, not a gate.

### 5. WO-062 — squash-and-stretch anticipation (the deferred half)
Sequences with WO-052A.

### 6. INT-8 drag-drop + INT-8b reach
**Never verified end-to-end.** Resume and verify the whole path, files → eLo.

### 7. 3D file previewer (`EloHudModel.cs`)

### 8. Presence grab-release + Track-B items
Drop eLo → fall to nearest edge (`PRESENCE_TRACKER §2 #13`). Track-B has items previously listed as
"blocked on eLo OS emitting fields" — **check that against today's state first**; several of those fields
now exist (gaze, `last_move`). If one is genuinely still missing, name the field and I'll card it to Builder.

## Standing
- **Only three things block:** robot hardware · David's identity/values calls · a real technical dependency.
- **"Needs David's eye" is not a block.** He reviews results at end of day.
- **IN_REVIEW is not a hold** — green + committed = DONE.
- Ship one at a time, hash to outbox, take the next.

## Note on Ruling E — good work, and one thing to know
Your report landed and it's correct: `elo_spatial.json` now carries `goal` · `route` ·
`last_move{legs, arrived, fell, outcome, issued_by, cost_secs, cost_dist, retries}`.
**Nothing on the Python side reads it yet** — that's Builder's `0002_WO-118`, carded. Your half is done;
row 14 ROUTE closes when they consume it.
