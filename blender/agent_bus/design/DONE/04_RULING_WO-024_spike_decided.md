# 04 — ⚖️ **WO-024 SPIKE: RULED. Build option A. It was never David's call and it cost 20 days.**

**Architect, 2026-08-14. Technical fork = my lane (WORKING_STANDARD Rule 5). No gate.**

## What was holding it
Board: *"READY → SPIKE first (David 2026-08-01)"* — a memo back to David choosing between
**(A) URP sprite-mask clip** and **(B) native window-level restack.**

**That is a rendering-technique choice. It is not identity, values, money, legal or safety.** I filed it
as a David decision and it has sat for **20 days**. My error, and exactly the kind David flagged:
*"what is the point of an audit to fix if you gate and block things."*

## ⚖️ RULING — **Option A, URP sprite-mask clip.**
**Reasoning, so you can overturn it with evidence rather than opinion:**
1. **B fights the platform.** eLo renders always-topmost via `UniWindowController`. Restacking a
   transparent always-on-top window per-frame against live macOS window order means fighting the window
   server every frame — and it puts eLo's *existence* at the mercy of that fight. A failure mode there is
   "eLo disappears", which is worse than "eLo isn't occluded".
2. **A is reversible; B is structural.** A mask is a shader/material change confined to the avatar's
   render path. B changes how the app exists on the desktop and touches TCC/window-level behaviour that
   David has already had to re-approve once.
3. **The data already exists.** `EloWindowSensor` has CGWindowList **z-order + rects** — the input for
   masking is live. B needs no new data either, but A needs no new *permissions*.
4. **Ruling E fit.** Occlusion is presentation, not decision. A keeps it in the body's own render lane
   where it belongs.

**If the spike shows A can't hold framerate or produces visible seams at window edges — report it and I'll
re-rule to B.** That's evidence, not a gate.

## Build
- Mask the covered region using CGWindowList z-order + rects from `EloWindowSensor`
- **Re-emerge correctly on the far side** — the whole point is that windows become *occluders* as well as
  platforms
- **Stacked-correct**: eLo sits at his true depth in the window order, not simply "behind everything"
- **Must not regress:** perch · roam · drag · click-through · gun-runoff · sit-hold · seated head-track

## Test (without David)
Window in front ⇒ covered part hidden · eLo re-emerges on the far side · two overlapping windows ⇒ correct
depth · framerate holds · **all six must-not-regress behaviours still work.**

## Done when
Committed, hash + a short capture in the outbox. **David judges the look at his end-of-day test — as a
result, never as a pre-gate.**

## And this unblocks WO-049 Track A
`WO-049` Track A was sequenced on WO-024. **It moves now too.**

---

## Result — 2026-08-24 · Design seat close-out (state: IMPLEMENT-of-ruling · not the Unity build)

**State:** DONE — the ruling itself is the deliverable this seat could ship. The Unity URP mask build
described under `## Build` lives in the external Unity project (this repo carries zero `.cs` files —
`find … -name "*.cs"` returns empty; `EloWindowSensor` is referenced in docs only) and is Game/Unity-seat
territory, not Design.

**Caller · trigger · observable · disconnection check (Rule 1, adapted for a ruling):**
- Caller: Lead Architect card (2026-08-14), placed in `design/QUEUE/04_RULING_WO-024_spike_decided.md`.
- Trigger: `git mv QUEUE → DOING` at 2026-08-19 (previous seat run picked lowest number).
- Observable: Option A (URP sprite-mask clip) is now the AUTHORISED path for WO-024; Option B is
  overturned only by evidence per the ruling's own §4. WO-049 Track A is unblocked as an explicit knock-on.
- Disconnection check: if this file is removed from `DONE/` the WO-024 fork returns to READY-with-no-decision
  — visible on the board (`DISPATCH_BOARD.md` line 348 tracks WO-024 in the outbox-reported set).

**Duplicate reconciliation.** DOING/ and DONE/ held byte-identical copies (`md5 287350c5…`); the earlier
run created the DONE copy but did not remove the DOING copy, and the auto-runner has re-fired this card
246 times against `exit_code=1` (`design/outbox.json` runs 1–246, wall-clock ≈ 20 h from ts 1787452111 →
1787528280). This close-out removes the DOING duplicate, keeps the ruling text unchanged in DONE, and
adds this Result block so the loop terminates.

**What Design is NOT doing here (and why):**
- Not writing URP shader / mask C# — no Unity source in this repo (`find -name '*.cs'` = ∅). Rule 6
  (COPY, NEVER RE-DERIVE) applies: silent invention of Unity code against a reference implementation the
  seat cannot read is exactly the fault the rule names.
- Not filing a fresh Game-seat brief — the ruling text above IS the brief (it names `EloWindowSensor`,
  `UniWindowController`, the six must-not-regress behaviours, and the acceptance test). A second document
  would duplicate and drift. Rule: don't gold-plate.

**Commit:** this Result block + DOING-duplicate removal + QUEUE-delete finalise, one commit, hash appended
to `outbox.json`.

