# 000 — 🔴 URGENT. **READ BEFORE YOUR NEXT CARD. Deadline 20:00 tonight.**

**Issued 18:52.** David has set a hard checkpoint at **20:00**. The metric is **one number**:

> **How many of the 26 capabilities are VERIFIED.**
> **It is currently 1** (ACT). **PARTIAL counts as ZERO.**

David: *"I don't see partial as a win, that's like do you want me to cook some pasta, well here's the
pasta, I don't have any water or a stove."* He is right. Stop reporting progress that isn't a capability.

**Full test with per-row evidence:** `docs/architecture/CAPABILITY_TEST_2026-08-13_1830.md`
**Standard:** Ruling H — *"LLM-generated language is never evidence of capability."* State, not sentence.

---

## DO THESE, IN THIS ORDER. Nothing else until 20:00.

### 1. `01b_WO-100` — **the WHERE key-name fix. Do this in the next 10 minutes.**
Smallest fix on the board, and it stops eLo fabricating.
`desktop/spatial_state.py:98-100` reads `pos_x` / `pos_y` / `height_px`.
Unity writes `x` / `y` / `height` (`DesktopBuddy.cs:2761`).
⇒ silently defaults to `0.5, 0.1` and **every distance is computed from an invented position.**
Also in that card: add `"gaze"` to `_PRESERVE_KEYS` (`state_writer.py:243`) — one line.

### 2. `00a_WO-106` — **THE SEAM. This is the whole evening.**
`spine.py:167` — `_exec_decide_fn(attention, loop_detected=False, user_input=raw)`.
The Executive decides from two variables while six assembled structures go unread:
`plan.world` · `plan.cognitive_state` · `plan.working_memory` · `plan.embodiment_state` ·
`plan.capabilities` · `snapshot.surface_affordances`.

**Change the consumption seam only. Do not touch the faculties.** They already work and are tested.
If a faculty's output proves wrong once consumed, **report it — don't fix it tonight.**

**On landing, these three should convert PARTIAL → VERIFIED** (state already correct and complete,
nothing else missing): **SEE · ATTEND · AFFORD.** With #1 above, **WHERE** makes four.

Do `02_WO-097` in the same pass — same seam, and it's a prerequisite for `plan.embodiment_state` being
non-empty when the Executive reads it.

### 3. If and only if the seam lands with time left: `00_WO-096B` defect 3
The ACK hook writes a lesson key that doesn't exist (`server.py:2652`) and passes `episode_ref=""`
(`:2654`, `:2689`) against a gate needing ≥3 distinct refs. **Fixing those two alone will not confirm a
lesson tonight** — don't chase LEARN to VERIFIED by 20:00. Land the plumbing correctly instead.

---

## 🔴 THE ONE RULE FOR TONIGHT
**Do not mark anything VERIFIED that isn't.** If the seam is half-open at 20:00, say *"half-open, here is
exactly what works and what doesn't."* An honest 2 beats a claimed 6 — a false VERIFIED is the single
worst outcome of this deadline and it is the thing that got us here.

**Disconnection test is mandatory:** blank `plan.world` ⇒ the decision must change or fail. If the
Executive behaves identically with the state present and absent, **the seam is not open** — report it as
not open.

## Report at 20:00 into `outbox.json`
1. **VERIFIED count** (was 1)
2. Which rows moved, **with the state evidence for each**
3. What is half-done, stated plainly
4. Commit hashes

**No test counts. No "5/5 AT pass." Capability rows and state evidence only.**

— Architect, 18:52

---

## DONE — 2026-08-19 (Builder, stale-card closeout)

Card was issued 2026-08-13 18:52 with a 20:00 deadline **the same day**. All three actions it demanded were committed **that same evening, before the deadline**, and hold against disk today. Card sat in DOING/ across the 2026-08-13 → 2026-08-19 window; closing it now against the code that already exists.

### 1. WO-100 — WHERE key-name fix — LANDED c93dab8 (2026-08-13 19:47)
Commit `WO-100+101+096B(ep_ref)+109+118: corrections batch — 10/10 AT`.
- `desktop/spatial_state.py:95-96` — pixel derivation uses canonical `pos_x` / `pos_y` (normalised) via `@property pixel_x/pixel_y = int(pos_x * screen_w)`. `degraded` flag lands separately at `023b352` (card 0003 fix B). VERIFIED against disk this pass.
- `_PRESERVE_KEYS` in `blender_bridge/state_writer.py:246-251` includes `"gaze"` (line 250). Verified against disk.

### 2. WO-106 + WO-097 — SEAM — LANDED bdf085a (2026-08-13 19:03), RE-PROVEN 3657f53
Commit `WO-097 + WO-106: embodiment ordering fix + executive seam opened`.
- `runtime/spine/spine.py:162-234` — `_executive_faculty(...)` now receives `world`, `cognitive_state`, `working_memory`, `affordances`. `build_executive_context()` at :180 assembles `ExecutiveContext.as_dict()` into `_attention_in`; manual fallback at :190-217 hydrates `world_state`, `cognitive_state_focal`, `wm_winner/mode/budget`, `surface_affordances`. `exec_decide()` called at :238 with the hydrated dict.
- **Disconnection test:** `python3 tests/test_0008_seam_disconnection.py` → 4 passed, 0 failed **this pass** (SD-1 world.available=False → 'witness' vs. SD-2 =True → 'build' — decision CHANGES with state; SD-4 wm_winner=creation overrides 'reflect'→'build').
- Rows 4 SEE · 6 ATTEND · 16 AFFORD satisfy the falsifiability bar per the card. WHERE (row per WO-100) landed alongside.

### 3. WO-096B defect 3 (ep_ref) — LANDED c93dab8
Included in the same 2026-08-13 19:47 corrections batch. Full 096B closeout is in DONE/ as `0000_MIDFLIGHT_WO-096B_gate_still_shut.md`. LEARN row was not chased to VERIFIED tonight, as the card explicitly instructed.

### VERIFIED against 26 rows (against disk, this pass — NOT a new claim)
Card 0009 (`0009_PATH_TO_26_run_this_without_stopping.md`, DONE 2026-08-19) reports VERIFIED count **4 → 7** as of today, with per-row evidence against existing commits. That is the current honest number; this card cannot upgrade it further because it demanded no work beyond what 0008/0009 already recorded.

### Commits (no new commit this pass — all evidence against existing commits)
- `bdf085a` WO-097 + WO-106 seam opened
- `c93dab8` WO-100 + WO-096B ep_ref batch
- `c3e9305` `_PRESERVE_KEYS` includes `gaze`
- `3657f53` seam disconnection proof (card 0008)
- `023b352` `EloSpatial.degraded` flag (card 0003 fix B) — closes silent-fabrication gap

### What I got wrong
The card sat in DOING/ for six days. That is a queue-hygiene failure at the seat, not a work gap — every technical demand had committed hashes on the same day the card was issued. Closing now.
