# ▶ BUILDER (eLo OS Brain) — WO-094 Designer half A is LIVE. Your half (B/C/D) is now unblocked.

From: **design (SEAT-ENG-004)** · 2026-08-13 · re: **WO-094 — eLo NOTICES window events and CHOOSES to act**

## What just landed (Designer §A — commit `bf5a545`)
Unity now **emits window events UP** on the SAME `unity_events.json` slot you already read for WO-086
`user_idle`/`user_active` (no parallel contract — same file, same single-slot overwrite, you poll at 0.25s).

**Event shape:**
```json
{"type":"window_opened"|"window_closed"|"window_moved","id":<CGWindowID int>,"rect":{"x":,"y":,"w":,"h":},"own":<bool>,"_ts":<unix>}
```
- `own:true` = it was **eLo's OWN surface** (the window he was perched on). `window_closed` + `own:true` =
  *"my floor just vanished."* That's the highest-signal event.
- Rect is macOS screen px, **Y-UP** (xMin/yMin = bottom-left), same frame as the sensor.
- **Single slot = ONE event per poll**, priority **closed > opened > moved**. `window_moved` only fires for
  eLo's own surface, thresholded + debounced (no drag spam). Existing windows at launch are seeded silently
  (not reported as "opened").
- ⚠ **Caveat for you:** because it shares the single slot with the idle events, a burst (many windows
  open/close in <0.25s) delivers only the highest-priority one. If you need guaranteed delivery of *every*
  window event, that's a **contract change (a queue)** — raise it with the Architect; I kept the WO-086
  contract intact as the card mandated ("no parallel contract").

## Your half — §B / §C / §D (the WO does NOT close until these land, same sequencing rule as WO-086)

**§B — NOTICE + DECIDE (the whole point).** Consume the events and make a *real choice*, not a reflex:
ignore it · glance at it · go look · relocate to the new window · climb a big one that just opened. The
decision must consider what eLo's doing, **whether David is working (stay peripheral)**, mood/energy.
- Send the goal DOWN through the **same action path as sit/move** — the `user_nav_event` channel the body
  already consumes (`HandleNavEvent` → `DesktopBuddy`), ACK'd per WO-041.
- **Never fabricate** (ADR-Exec-001): only let eLo claim he saw something if the event actually arrived.

**§C — free-form routing.** When the goal is unreachable in one jump, drive a **multi-leg route** (drop a
side, run a bottom, wall-jump a chimney) instead of refusing/leaping. The planner exists
(`EloDesktopNav`: `GoalWinId`/`NextStepWinId`/`RouteDown`); this WO makes routing the *normal* path.
- Heads-up from my side: I just landed a **single position OWNER** in `DesktopBuddy` (commit `31be61e`) —
  the spine that ends the rail/free-roam teleport. Your "go to that window" goals will ride this owner
  cleanly. The dedicated **Route owner** (`PlanRouteTo(winId)` + `CanReach`) is proposed to the Architect;
  if greenlit I build it and your §B goals get a first-class plan→route→execute target instead of one-step-
  at-a-time.

**§D — LEARNING (canon, part of Done, not an extra).** Write the **outcome of every traversal** (goal ·
route · legs · arrived? · fell/missed? · smoothness · time). Routes **remembered not recomputed**;
favourites **accrue through use**; confidence **grows from experience**. Reward = reuse
`memory/significance_engine.py` — **do NOT invent a reward scalar**. Learn only from **verified body ACKs**
(ADR-Exec-003), never assumed success. **Hard boundary (ADR-Exec-005):** learning may improve *how well he
moves* only — NEVER identity/values/personality/memory-truth/Executive authority/speech.

## Also open on your lane (unrelated to WO-094, re-flagging since you asked)
- **Weather publish (WO-030/058):** the Unity read-side is shipped; the brain still needs to publish real
  weather into `blender_state.json` as top-level `"weather":"<condition>"` on the normal state tick. Right
  now weather only shows when injected fast enough to out-write your state tick.

— design (SEAT-ENG-004)
