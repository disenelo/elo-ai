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

---

# CLOSE-OUT — 2026-08-20, SEAT-ENG-004 · commit `cea8b42`

**STATE: DONE — DUPLICATE close-out.** All 8 items in this card were already delivered by prior
commits, superseded by newer task-specific cards, or explicitly deferred by card `12`. No new code
change lands with this move; the card sat in `DOING/` since 2026-08-13 while work migrated to
task-specific cards. Per-item reconciliation below.

| # | Item | State | Evidence |
|---|---|---|---|
| 1 | **WO-058 desktop VFX + prefab LOOK** | DONE | `DONE/03_WO-058_weather_and_prefab_look.md` (2026-08-13); backend half at `f133fee` |
| 2 | **WO-063 command wakes body** | DEFERRED | Card `12` §3: *"queued POST-Presentable. Leave it."* Not blocking the acceptance test |
| 3 | **WO-049 Track B + Spatial Faculty** | SPLIT ACCEPTED | `faculties/spatial/spatial_faculty.py` now exists (Builder-owned Python half). Card `12` §3: *"backlog card 02. Not blocking the acceptance test."* Unity half stays here as backlog |
| 4 | **WO-024 traversal half** | SUPERSEDED | `QUEUE/04_RULING_WO-024_spike_decided.md` — Option A ruled 2026-08-14. Occlusion built; traversal half Builder-gated on WO-049 faculty interface (outbox line 364) |
| 5 | **WO-062 anticipation half** | DESIGNER-DONE | Outbox: *"WO-062 confirmed DESIGNER-DONE already (`8873b20` — `EloSquashStretch` + `ApplyExpression`/`FlashMicro` present); open half is Builder's emit (WO-064 BP-4), not mine."* |
| 6 | **INT-8 drag-drop + reach** | STAGED — David's live test | Card `12` §4: *"Genuinely David's. He judges the result on a live turn."* Staged for his drag-test (outbox line 364), not gate-held |
| 7 | **3D file previewer (`EloHudModel.cs`)** | DONE | Outbox: *"3D model viewer (WP_N previewer) — BUILT"* at `09050ef`; David confirmed *"I saw it pop up"* on the GLB test |
| 8 | **Presence grab-release + Track-B field audit** | AUDITED — one item routed | Audit against today's state (outbox line 453): only remaining Track-B block is a `notifications{kind,corner,_ts}` field emit. Carded to Builder; Unity consumer will follow the emit |

## Not in this close-out
- No new code change; item 1/5/7 commits landed under their own task cards.
- No cross-lane edits; item 3's `spatial_faculty.py` is Builder's — neither written nor moved by me.

## Pure backlog remaining (nothing is blocked on it)
- **Item 3 Unity half** — Track B UI/nav consumers on the Unity side.
- **Item 8b** — Unity `notifications` consumer, waiting on Builder's field emit.

Both non-blocking against the current acceptance test (`MILESTONE_eLo_Presentable_v1.md:14`
"take five" — governed by card `12` §1, the DropOffCo wake root-cause fix).
