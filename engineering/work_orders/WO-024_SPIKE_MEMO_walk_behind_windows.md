# WO‑024 — Spike memo: eLo walks BEHIND windows (A vs B) → **decision for David**

**Author:** Design/UI‑Avatar (SEAT‑ENG‑004) · **Date:** 2026‑08‑04 · **Status:** decision-gate

## The problem
eLo is one **transparent topmost overlay window** (`UniWindowController`, per‑pixel hit‑test). He already
**stands on** window top‑bars (`EloWindowSensor` gives every window's **z‑order rank + rect**, no permission).
Missing half = **depth**: when a window is in front of where he is, he should pass **behind** it (and behind
the next if stacked). Two routes were speced; this spike compares them against the real code.

## (A) URP sprite masking / clip  — **RECOMMENDED**
Keep the single topmost overlay. Each frame, from `EloWindowSensor`'s z‑ordered rects, take the **union of
windows whose z‑rank is in FRONT of eLo's current depth** (the window he's perched on / nearest) and **clip
those pixels out of his render** (stencil in URP, or a screen‑space mask texture).

- **Pros**
  - Keeps the proven overlay model — **zero risk** to click‑through / perch / drag / topmost / gun‑runoff (acceptance #4).
  - Fully controllable **in Unity** — no native OS restacking, no ObjC fragility.
  - The data is **already there** (`EloWindowSensor.z` + rects); the mask is a handful of rects → cheap per frame.
  - Degrades gracefully: worst case a few px at rounded corners, never a crash or a stuck window.
- **Cons / caveats**
  - It's a **visual** occlusion (he's still topmost, just clipped) — fine, it's indistinguishable on screen.
  - Mask is built from **rectangular** window rects → rounded corners / non‑rect windows aren't pixel‑perfect at the corner (~a few px). Acceptable; can inset slightly.
  - His **glow/shadow** must clip too (include them in the masked render).
- **Effort:** medium. URP stencil pass or a screen‑space mask RT fed by the sensor rects + a clip in eLo's shader/material.

## (B) Native window‑level restacking
Insert eLo's native window into the OS z‑order between specific app windows (window level + ordering via ObjC).

- **Pros:** true OS occlusion, pixel‑perfect incl. rounded corners.
- **Cons (blocking):**
  - macOS **can't reliably order an overlay BETWEEN two arbitrary other‑app windows** — normal windows share a
    level; cross‑app ordering within a level isn't a stable, controllable API. It fights the OS constantly.
  - **Contradiction:** eLo must be **topmost** to stay interactive (hit‑test/drag), but **behind** to be occluded — can't be both via window level.
  - High regression risk to click‑through / topmost / collection behaviour (acceptance #4, the hard constraint).
  - Needs new native code — **no window‑level plugin exists yet** (`EloWindowPlugin` only does the CGWindowList + drag overlay).

## Recommendation → **A (URP sprite masking)**
A satisfies every acceptance item (walk‑behind, stacked windows, platform+occluder unified, **no regression**)
while keeping the fragile OS‑window model untouched. B's only win (perfect corners) doesn't justify fighting
macOS window ordering + breaking eLo's interactivity. **Recommend A.**

### If David picks A — build plan
1. Per frame, from `EloWindowSensor`, pick eLo's **depth** = z‑rank of the window he's perched on / nearest under him.
2. Build the **occluder set** = windows with z‑rank in front of that depth; take their rects.
3. Render those rects to a **stencil / screen‑space mask**; **clip** eLo's body+glow+shadow where covered.
4. Verify the 4 no‑regression cases; short recording of walk‑behind + a stacked (behind‑A/in‑front‑of‑B) case.

**→ David: pick A or B. I'll build on your nod (recommend A).**
