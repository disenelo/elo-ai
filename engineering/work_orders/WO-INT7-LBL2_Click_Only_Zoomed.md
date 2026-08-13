---
id: INT7-LBL2
title: "One Brain visualiser — Label readout: click-only, zoomed-in (single change)"
status: READY → DISPATCHED (Design) — sequence AFTER M4 (don't split focus)
target_agent: UI/Avatar (Design)
priority: P2
owner: ""
depends_on: [INT7-LBL (DONE ✅ David, c11d66b)]
supersedes: INT7-LBL hover-or-click behaviour
spec_refs:
  - docs/architecture/20_one_brain_visualiser.md §6.5 #1 (FINAL rule, David 2026-07-28)
lane: Presence/Unity (EloBrainCluster) — NOT eLo OS (D-I)
created: 2026-07-28
---

# INT7-LBL2 — Label readout: ZOOM-GATED (single change)

Tightens the shipped INT7-LBL behaviour. Today the `_tip` readout appears on **hover OR click at ANY
zoom** (line ~360: pinned OR (hovering cluster AND near a node), with no zoom gate). David's final rule
(07-31, via the Designer): **the readout is gated on zoom** — no text when small; hover *or* click reveals
text once zoomed.

## 1. Objective (one change only)
Add a **zoom gate** to the readout. Small = glow only, no words. Zoomed = the existing hover-or-click
readout works.

- **Small / not zoomed:** hover does its **usual glow highlight/enlarge only** — **no `_tip` text**. No
  floating names. (This is the fix: currently text shows on hover at small size — gate it off.)
- **Zoomed in:** **hover OR click** a state → reveal its `_tip` readout (name + feeling sentence + energy%),
  exactly as it does today. Both triggers keep working *once zoomed*.
- **Hide:** move off / click empty / same state / zoom back out → hide.
- Nothing persistent; one state's readout at a time.

**The one-line shape of the fix (per the Designer's read of the code):** gate the hover/readout branch in
the `tipNode` condition on the zoom/expand level — show the readout only when `_expand` is up (zoomed);
below that, hover is glow-only. Click-when-zoomed unchanged.

## 3. Signal contract
Pure interaction/render change on `EloBrainCluster`. Reuses the existing `_tip` readout + `label`/`detail`
from `brain_state.json`. **No new state, no eLo OS change.**

## 4. Constraints (MUST)
- **One change only** — label interaction, nothing else. Motion (M1/M2/M3/C1/M4), colours (MoodPalette),
  clustering, click-pin isolate, node size, anchors all **untouched**.
- **Keep the hover glow highlight** at all zoom levels — do NOT remove it.
- **Zoom-gated readout** — below the zoom threshold, hover shows the glow but **no `_tip` text**; once
  zoomed, hover **and** click both reveal the readout (today's behaviour, now only when zoomed).
- The change is **the zoom gate only** — do not otherwise alter hover/click logic.
- Lane: `EloBrainCluster` (Presence/Unity). Do **NOT** touch eLo OS (`~/elo-ai/`) — D-I.
- **M4 is DONE** — no longer blocked; pick this up now. Baseline = M4 (`5e834f3`).

## 5. Acceptance (visual review + build gate)
- [ ] **Small / not zoomed:** hovering a state shows the **glow only — no `_tip` text**. No floating names.
- [ ] **Zoomed in:** **hovering** a state shows its `_tip` readout.
- [ ] **Zoomed in:** **clicking** a state also shows its `_tip` readout (both triggers work once zoomed).
- [ ] Move off / click empty / same state / zoom out → readout hides; nothing persistent.
- [ ] Click-pin isolate + all motion behaviours (M1–M4/C1) unchanged.
- [ ] Builds 0 compile errors; relaunch shows it live; diff is the zoom-gate only.

## 6. Build discipline
One change · exactly to spec · build (0 errors) · relaunch · **then WAIT** for review.
Baseline = M4 commit `5e834f3`.

## 7. Handback
Commit hash + one-line note → `COMPLETION_LOG.md`. David visual-reviews; Architect verifies against
§2/§5 + canon `20 §6.5 #1` → DONE. Then resume the motion queue at **M5 Memory Echo**.
