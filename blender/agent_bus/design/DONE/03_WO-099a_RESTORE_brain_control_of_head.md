# 03_WO-099a_RESTORE_brain_control_of_head.md — 🔴 P0. DAVID'S DIRECT INSTRUCTION.

**WO:** WO-099a (part 1 of WO-099) · **Seat:** design · **Priority:** **P0 — do this before anything else**
**Reserved?** no · **Full spec:** `engineering/work_orders/WO-099_Gaze_Loop_Intent_Down_Awareness_Up.md`

## David, 2026-08-13, verbatim
> **"So fix what they broke and re-trigger it back through the brain"**

You reported it honestly (`5180b0f`): to stop the stuck `HeadCueActive` freezing the head, you made
cursor-follow primary — **and the brain can no longer drive the head.** David wants that closed now.
This card is **only** that. The awareness-UP half is card `04` and comes after.

## What to build — the DOWN path, and nothing else
Replace the blunt `HeadCueActive` on/off with the **gaze intent object** you proposed (ratified):

`blender_state.json` → `gaze`:
- `mode`: `follow_cursor` | `look_at_window` | `look_at` | `rest`
- `win_id` / `point` — the target
- `weight` (0–1) — blend, not a switch
- `hold_secs` — how long to hold before releasing

`HeadLook` consumes it and aims at the brain's target **using the same aim mechanism you already built and
tuned.** Do not rebuild the aim. The brain chooses *where*; your code still does *how*.

## 🔴 THE GUARD THAT PROTECTS WHAT WORKS — non-negotiable
**When the brain is silent, stale, or sends `rest` → fall back to the cursor-follow reflex.**
The head must NEVER freeze because nothing was said. That stuck-cue freeze is the exact bug you just fixed —
this must not reintroduce it by a different route.

Ruling E permits reflex; it only requires the body report it. So tag the source: **`issued_by: brain|reflex`.**

## Why a weight and not a switch
The old failure was binary — brain ON meant body OFF, so a ~0 cue froze the head. A **weight** can't do that:
at 0 the reflex has it, at 1 the brain has it, in between they blend. **A stale or empty cue decays toward
the reflex instead of killing it.** That's the structural fix, not just a bug patch.

## Test (without David)
Brain sends `look_at_window` → head aims there · brain sends nothing for N seconds → head returns to
cursor-follow, **does not freeze** · brain sends `weight: 0` → reflex has it · brain sends `rest` → head rests,
then reflex resumes · seated + after getup still track (don't regress `5180b0f`).

## Done when
implemented + tested + committed → hash, DONE/, outbox. **Then take card 04** (gaze awareness UP), which
makes the brain *know* what he's looking at.

## Result
- commit: 4bb1f01
- gaze intent DOWN consumed in HeadLook (mode/win_id/point/weight/hold_secs); look_at_window->window centre, look_at->point, follow_cursor->cursor, rest->ease to neutral
- GUARD: silent/stale/rest/weight~0 -> cursor reflex, never freezes (state re-parses only on content change = free freshness)
- Builder WO-099b (emit) now UNBLOCKED
