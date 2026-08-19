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
