---
id: WO-040
title: "Avatar — TWO separate bugs: (A) sit never triggers (no animation at all); (B) the joy-jump animation gets stuck, never returns to idle."
owner_seat: SPLIT — SEAT-ENG-001 (Builder: is the sit cmd emitted?) + SEAT-ENG-004 (UI/Avatar: jump→idle transition)
priority: P1
review_required: L3 (David — eLo actually sits; no animation gets stuck)
status: OPEN — corrected per David 2026-08-03
constraint: "MINIMAL / SURGICAL fix only. Do NOT refactor the animation system. David: 'let's not change things to make it more buggy.' Touch only what these two bugs need; keep everything else exactly as-is."
---

# WO-040 — two separate avatar bugs (do NOT conflate them)

## Corrected by David (2026-08-03)
> "the sit doesn't trigger, the joy jump doesn't return to idle" — these are TWO things.
> NOT "sit plays a jump." The sit fires nothing. The joy-jump is a different animation that sticks.

## BUG A — sit never triggers (no animation)
- Asking eLo to sit produces NO avatar motion at all. He narrates a sit; nothing moves.
- Code note (read-only): the body-directive layer *computes* a sit — `_signal_word_intent("sit with me")`
  → `{name:sit,target:cursor}` (server.py:422). So the directive exists in logic but does not
  manifest as motion.
- ARBITER (run once): ask eLo to sit → inspect `blender/blender_state.json`.
  - sit motion written → bug is UI (Unity isn't playing the sit clip).
  - nothing written → bug is eLo OS (directive never reaches the state file).

## BUG B — joy-jump doesn't return to idle
- A separate "joy-jump" animation (fires from some other trigger, not sit) plays and then STICKS —
  it never blends/transitions back to idle. UI/Avatar animation-state issue.
- Fix is the one missing transition (jump → idle), nothing more.

## SCOPE GUARD
Surgical only. Bug A = make the existing sit directive reach + play (no new command system).
Bug B = add the single jump→idle transition. Do not touch other clips/states. Re-verify the rest
still behaves after.

## Acceptance
1. "sit with me" / "have a seat with me" → avatar actually sits (motion visible).
2. The joy-jump returns to idle on its own; nothing sticks.
3. No other animation behaviour changed.
