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

## STALE DUPLICATE — 2026-08-19 (builder autoloop pass)

This file is a duplicate of `DONE/000_URGENT_2000_VERIFIED_COUNT.md`, which already contains the full 2026-08-19 close-out.
Code state re-verified against disk on this pass:
- `desktop/spatial_state.py:122-124` reads Unity keys `x`/`y`/`height` (WO-100 landed).
- `blender_bridge/state_writer.py:246-251` includes `"gaze"` in `_PRESERVE_KEYS`.
- `runtime/spine/spine.py:160-238` — Executive receives `world`, `cognitive_state`, `working_memory`, `affordances`; `build_executive_context()` at :194 opens the seam (WO-097 + WO-106 landed).
- `python3 tests/test_0008_seam_disconnection.py` → 4 passed, 0 failed (re-run this pass).

No new commits. Moving stale duplicate → `DONE/000_URGENT_2000_VERIFIED_COUNT_dup_2026-08-19.md` to clear DOING.
