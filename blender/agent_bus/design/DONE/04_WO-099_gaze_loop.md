# WO-099 — The Gaze Loop: intent DOWN, awareness UP

**Owner:** Designer (emit + consume in Unity) + Builder (decide + consume in eLo OS). **Priority:** P1.
**Status:** OPEN — spec'd 2026-08-13. **Not gated.**
**Origin:** Designer relay 2026-08-13 (HeadAim built, `5180b0f`) + **David live**: the head-aim/gaze *"should
follow back to eLo OS and the awareness that he is looking at this or can see a window etc."*
**Canon:** Ruling E (body reports) · WO-086 pattern · Vol XI body contract · Vol XIII Ch.3 noticing/choosing ·
IO Contract (channels by direction + delivery-type; **topics are FIELDS, not files**).

---

## 1. What just happened (context — HeadAim is DONE)
`5180b0f` — head-aim confirmed working by David: decoupled L/R + U/D, looks at nearby cursors
(`aimResponse 0.10`), chest trails the head, tracks while seated and after getup.

**The root fix that unblocked it:** the brain's `HeadCueActive` was **stuck ON and blocking cursor-follow** —
the head was obediently following the brain's ~0 cue instead of the mouse. The Designer made **cursor-follow
primary**, which is why it works now.

## 2. 🔴 THE REGRESSION THIS CREATED — name it plainly
**The brain currently cannot drive the head.** The body owns gaze outright.

That is the mirror image of the old bug and it breaks One Brain in the other direction. It was the right call
to ship — a working head beats a correct-but-dead one — but it must not stand. David: *"the brain will need
to trigger this soon."*

**This WO closes it, without breaking what now works.**

---

## 3. ⚖ ARCHITECT RULING — the channel question the Designer asked
They asked: `unity_events.json` or a gaze field in `elo_spatial.json`? **Both — and the split is not arbitrary.**
The IO Contract separates channels **by delivery-type**: continuous state vs discrete events.

**Gaze is BOTH, so it uses both:**

| | Channel | Why |
|---|---|---|
| **Where he is looking, right now** | **`elo_spatial.json` → `gaze` field** (continuous STATE) | changes every frame; putting it on the event channel would flood it |
| **"He just looked at something new"** | **`unity_events.json` → `gaze_target_changed`** (discrete EVENT, **debounced**) | this is the *noticing* — the thing the brain reacts to |

**Debounce the event** (recommend ~250–400ms of dwell on a new target before it fires). Without that, a
cursor sweep across three windows fires three "he noticed" events and eLo looks twitchy rather than attentive.

**DOWN (brain → body): `blender_state.json` → `gaze` object.** Same DOWN channel as sit/move; a field, not a
new file.

---

## 4. Scope

### A. DESIGNER — replace the blunt on/off with a gaze INTENT (their proposal, ratified)
Retire `HeadCueActive` as a binary block. Consume a `gaze` object from `blender_state.json`:
- `mode`: `follow_cursor` | `look_at_window` | `look_at` | `rest`
- `win_id` / `point` (target) · `weight` (0–1 blend) · `hold_secs`
**Fallback rule (critical — protects what works):** when the brain is **silent or stale**, the body falls
back to the **cursor-follow reflex**. Ruling E: the body may act on reflex; it just has to report. The head
must never freeze because the brain said nothing.

### B. DESIGNER — emit gaze awareness UP
- **State:** `gaze` in `elo_spatial.json` — viewport point he's aiming at · `win_id`/owner/rect of any window
  under that gaze (reuse `EloWindowSensor` + `IsTopmostAt`) · `issued_by: brain|reflex` · confidence/weight.
- **Event:** `gaze_target_changed` on `unity_events.json` when the target changes and survives the debounce.

### C. BUILDER — the brain consumes, and can drive
- Read the gaze state + events; **eLo KNOWS what he's looking at.**
- Feed it to attention (Vol VI) and perception (Vol XII) — gaze is a strong salience signal.
- Issue gaze intent DOWN when the brain has a reason to look somewhere (composes with **WO-094** window
  events: *window opened → look at it* is the first real use).
- **Verified Speech:** he may only say he's looking at something if the gaze state says so.

---

## 5. Why this matters (the goal, not the plumbing)
**eLo has no eyes — head orientation IS his gaze.** Right now he looks at things and *the brain has no idea*.
With this loop he can say "I saw that window open" truthfully, attention can be driven by what he's actually
looking at, and *looking* becomes a thing he does on purpose rather than a reflex that happens to him.

It's the same three-part shape as WO-086 and WO-094 — **intent down, action, awareness up** — now applied to
gaze. That shape is becoming the spine of how eLo's body and brain work together.

## 6. Sequencing (asked for, ruled)
1. **A + B together** (Designer) — intent-consume and awareness-emit ship as one; the fallback keeps
   cursor-follow working throughout, so nothing regresses.
2. **C** (Builder) lands with or after B. **WO-086 is unaffected** — mouse-idle already routes UP; this is a
   sibling loop, not a dependency.
3. Diagnostic log strip (`[headaim]`/`[TELE]`/`[BASIS]`) — after David locks the feel, not before.

## 7. Test (without David)
Brain sends `look_at_window` → head aims there · brain goes silent → head falls back to cursor-follow, does
NOT freeze · gaze state reports the window under gaze · `gaze_target_changed` fires once per settled target,
not per frame · Builder: injected gaze state is readable and drives attention.

## Done when
both halves land, tests green, committed. **David's bar:** eLo looks at something *and eLo OS knows he did.*

## Result
- commit: 582dd10 (Part B) + 4bb1f01 (Part A = WO-099a)
- STATE elo_spatial.json gaze{x,y,win_id,window,on_window,issued_by} — VERIFIED live (win_id 54676 = Code, issued_by reflex)
- EVENT unity_events.json gaze_target_changed (debounced 0.3s) — VERIFIED firing
- FEEL: head eases off cursor while moving (moveAimScale 0.2) per David
- Builder Part C (consume + drive) relayed via WO-099a note; awareness now available
