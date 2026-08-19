# 00c — ⚖️ **RULING: the planner matches the physics gate. One rule, not two. Build it — David reviews the result.**

**Architect ruling, 20:30. Technical call — mine, not David's.** Your flag was right; the routing of it
wasn't. Owning that: I'd rather you over-flag than silently change (Rule 4d) — but *"eyeball this before I
build"* makes David a pre-gate, and he has ruled repeatedly that he isn't one. **He reviews results.**

## The finding — yours, and it's a good one
> *"Planner rejects gaps > 1.5 heights, physics hops 6 sizes — ~4× apart, so eLo routes around gaps he
> could clear."*

**Two different rules answer "can I cross this?"** — `maxJumpEloHeights = 1.5f` (`EloDesktopNav.cs:35`,
nav graph) and `MaxHopDist()` (`DesktopBuddy.cs:260-261`, the actual jump). The planner is ~4× more
conservative than the body.

**This is the same fault as two world graphs and two attention drivers** — one question, two answers, and
the one that decides isn't the one that plans. That makes it a One-Brain violation, which puts the call in
my lane, not David's.

## RULING
**`MaxHopDist()` is canonical. The planner reads it — it does not keep its own constant.**
The body's real reach is ground truth; the planner must not veto moves the body can make. A planner
rejecting reachable gaps is a **false constraint**, and it hides an entire class of route from the brain —
eLo can't learn a crossing he was never allowed to attempt.

**How to land it safely:**
1. Planner takes its gap limit **from `MaxHopDist()`**, one source.
2. Keep a **tuning multiplier** (default 1.0) so the conservatism is a dial, not a hardcoded constant —
   if the feel is wrong, it's one number, not a re-architecture.
3. **Revert-safe branch**, tight diff. List what must not regress: perch · roam · drag · click-through ·
   gun-runoff · sit-hold · seated head-track.
4. **Keep emitting `gap_distance_sizes` against the physics number** — you were right, learning stays
   honest either way.

## On the feel
It **will** change how he traverses — probably more direct, fewer detours. **That's the point**, and
David judges it at his end-of-day live test with one line from you in the outbox:
*"planner now uses the physics reach — he takes more direct routes; multiplier is `X`, one number to
retune."*

**If he doesn't like it, the multiplier moves. That's a dial turn, not a rebuild — which is exactly why
it's not worth blocking on.**

## Also — your row 17 emit
`gap_distance_sizes` + `max_hop_sizes` in the physics unit is the right shape. Builder's 7-state GAP
machine (`builder/QUEUE/05e`) swaps from **declared** to **learned** limits once enough
`arrived:false` rows exist. **Negative outcomes are the valuable ones** — make sure failed crossings report.

## Done when
Committed, hash + the "must not regress" list + the multiplier value in the outbox. **Then back to
`00` ACK / `01` One Brain.** Don't hold for David.
