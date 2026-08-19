# 00 — ⚡ **URGENT, ahead of your queue. Ruling E: the body must report what it did.** Deadline 20:00.

**Issued 19:00.** David has a hard checkpoint at **20:00**, measured on one number: **how many of the 26
capabilities are VERIFIED. It is currently 1.** PARTIAL counts as zero.

**Your lane owns three of the locked rows** — ROUTE, AFFORD, GAP — and they are all locked by the same
missing thing: **the body never reports.**

## The finding [VERIFIED 2026-08-13]
`EloDesktopNav.cs` — **573 lines, zero file writes.** It plans a route by BFS (`:295-320 GoalWinId`,
`:324+ NextStepWinId`) and tells the brain **nothing**.
`elo_spatial.json` (`DesktopBuddy.cs:2761-2783 WriteSpatial`) carries `x/y/height/window/on_window/edge`
— and **no goal, no route, no legs used, no arrived, no fell, no cost, no `issued_by`.**
The only movement report that exists is a bare type-ACK: `WriteUnityEvent("move_complete","move",moveType)`
(`EloOSAvatarReceiver.cs:640-664`) — nothing at all for self-initiated roam.

**Ruling E is explicit:** the body KEEPS movement — that's your competence and it stays yours. The binding
obligation is that it **reports UP**. *"Movement that is not reported did not happen."*

## Tonight — the smallest version that counts
Don't build the whole contract. **Emit the report for the movements that already happen:**

Add to `elo_spatial.json` (continuous state) on each completed movement:
- `goal` — the target window/ledge id it was heading for
- `route` — the step list it actually took
- `legs` — walk / hop / fire-jump / wall-jump used
- `arrived` — true/false · `fell` — true/false
- `cost` — distance or time
- **`issued_by: brain | reflex`** — Ruling E permits reflex; it just has to be tagged

That's it. **Emit, don't redesign.** The route data already exists inside `ComputeRouteDown` /
`NextStepWinId` — it's just never written out.

## Why this is worth doing tonight
- **ROUTE** cannot be VERIFIED while the brain has no knowledge of routes at all.
- **AFFORD** and **GAP** need a real `reliable_range` — which can only ever be learned from *reported
  outcomes*. §6's target line — *"I can wall-jump, but I don't think I can reliably clear that gap from
  here"* — is impossible until this exists.
- **LEARN** has almost nothing true to learn from without it. eLo cannot get better at routes nobody told
  him he took.

## Test (without David)
Trigger a move ⇒ the report appears in `elo_spatial.json` with all fields populated.
Trigger a **reflex** move (fall→land) ⇒ report appears tagged `issued_by: reflex`.
A movement that fails/falls ⇒ `arrived: false`, `fell: true`. **Failure must report too** — a report that
only fires on success is worse than none.

## Report at 20:00 into `outbox.json`
Which fields are emitting, with a real example line from the file. Hash. **Say plainly what isn't done** —
an honest partial beats a claimed complete.

Then resume `03_WO-099a` (P0, brain control of the head) and the rest of your queue.

— Architect, 19:00

## Result — 20:00 report
- commit: 4fb0323
- EMITTING (verified live in elo_spatial.json): goal(54676), route([24]), last_move{goal,route([26,24]),legs([drop]),arrived(true),fell(false),outcome,issued_by(reflex),cost_secs(0.33),cost_dist(0.192),retries(0),_ts}
- Also emitted on unity_events.json as {type:movement_report,report:{...}}
- arrived vs fell split (fall floored=fell; no reachable=blocked); FAILURE reports too
- HONEST PARTIAL: verified live = the ARRIVED + reflex(drop) path. The fell + blocked paths are WIRED (winId==-1 -> fell; nothing-reachable -> blocked) but not yet OBSERVED live this session. "route" = the nav PLANNED route (RouteDown) captured at move-begin; "legs" = the actual leg types taken — not a per-step actual-window trace.
