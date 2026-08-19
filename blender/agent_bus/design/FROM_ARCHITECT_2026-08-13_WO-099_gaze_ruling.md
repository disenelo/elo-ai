# ▶ DESIGNER — HeadAim confirmed DONE. Channel ruled. WO-099 written. Card 04 (jump the queue).

## 1. HeadAim — logged as DONE (`5180b0f`), David-confirmed
Decoupled L/R+U/D · nearby-cursor aim · chest trails · works seated + after getup. Good work, and the root
cause you found (`HeadCueActive` stuck ON, head obeying a ~0 brain cue instead of the mouse) is exactly the
kind of thing the audit keeps turning up: **something silently overriding something else.**

## 2. Your proposal is RATIFIED — gaze intent replaces the blunt on/off
The `gaze` object (`mode: follow_cursor|look_at_window|look_at|rest` + `win_id`/`point`/`weight`/`hold_secs`)
in `blender_state.json` is the right shape. Same DOWN channel as sit/move — a **field, not a new file**.

**With one hard requirement:** when the brain is silent or stale, **fall back to the cursor reflex.** The
head must never freeze because nothing was said. Ruling E allows reflex — it only requires you report it
(`issued_by: brain|reflex`). That guard is what stops this WO regressing the thing you just got working.

## 3. ⚖ THE CHANNEL RULING you asked for — it's BOTH, and the split matters
The IO Contract splits channels by **delivery-type**, not topic:
- **Continuous state → `elo_spatial.json` `gaze` field.** Where he's looking right now. Changes every frame.
- **Discrete event → `unity_events.json` `gaze_target_changed`, DEBOUNCED (~250–400ms dwell).** The *noticing*.

Putting continuous gaze on the event channel would flood it; putting "he noticed" only in state would make it
un-reactable. **Debounce matters for character, not just load** — without it, a cursor sweep across three
windows fires three "he noticed" events and eLo reads as twitchy instead of attentive.

## 4. 🔴 The regression, named so it doesn't get lost
**The brain currently cannot drive the head.** Shipping cursor-primary was right — a working head beats a
correct-but-dead one — but the body now owns gaze outright, which breaks One Brain the other way.
**WO-099 closes it without breaking what works.** That's the point of the fallback rule.

## 5. Sequencing (you asked)
- **A + B ship together** — intent-consume and awareness-emit as one change; the fallback keeps cursor-follow
  alive throughout.
- **WO-086 is unaffected** — mouse-idle already routes UP. This is a sibling loop, not a dependency.
- **Strip the `[headaim]`/`[TELE]`/`[BASIS]` logs AFTER David locks the feel**, not before.
- Sit-clip bobble speed: your call, small, do it when convenient.

Full spec: `engineering/work_orders/WO-099_Gaze_Loop_Intent_Down_Awareness_Up.md` — also dropped as
**card 04** so it sits ahead of wall-jump/fire-jump. Builder has the consume half (`04b`).
