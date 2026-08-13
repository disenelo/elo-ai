# ▶ DESIGNER — AUDIT FINDINGS ARE THE PRIORITY. 3 new cards in your QUEUE.

David 2026-08-13: **"the priority was the audit findings and fixing them and the gaps."**

**Work your QUEUE lowest-number-first. Cards 05, 05a already there; 06–08 are new.**

| Card | What | Why it matters |
|---|---|---|
| **05 / 05a** | **WO-090 HeadAim stack** + the HeadLook audit. Head write is `headBone.localRotation * Euler(...)` — **additive on the idle clip, never overrides it**; effective look ≈13° against ±12° random wander. Split `HeadExpression.cs` out (keep the 350 lines of micro-expressions), constraint owns rotation at ±100, re-home peek/drag/observe/sit/nod on top | why the head has never looked right |
| **06** | **WO-092 wall-jump** — the 45° arc IS built (`_wrWallJump` + `wallJumpArcMul`); it needs up-a-level + in-reach + a **40% dice roll**, so it almost never fires. Log every rejection, relax, add Inspector dials | David has never seen it |
| **07** | **WO-093 fire-jump axis** — no-gun half is **already done**; but it fires on **DOWN-jumps** (`freeroamFireJumpChance`) when David wants **LATERAL only, never forward or down**, plus a minimum distance | fires on the wrong axis |
| **08** | **Ruling E — the movement REPORT channel.** ⭐ **highest value in your queue** | see below |

## Card 08 is the important one
**You KEEP route selection** — the proposed demotion of `EloDesktopNav` was **CANCELLED** by David's Ruling E.
Nothing working gets retired. What's missing is the **report**: goal · route actually taken · legs used ·
arrived/fell · cost · `issued_by`. Reflexes report too.

> **David's rule: "movement that is not reported did not happen."**

**Without it the learning loop cannot work at all** — eLo can't get better at routes nobody told him he took.
That's the half that makes his movement *learnable* rather than merely correct.

## Also note (fixed by 05, don't rebuild)
**Peek IS built and wired** (`DesktopBuddy:1275/1459` — the sizing-up scan and the 18° look-down before a drop
→ `HeadLook:378`). It's invisible only because it's 10–18° riding on the idle clip, swamped by the ±12°
wander. **HeadAim fixes it. Do not rebuild peek.**

Canon: `docs/architecture/Volume_XI/` (body contract + movement grammar) · `Volume_XIII/` (spatial) ·
Rulings E/F in `CANON_RULINGS_2026-08-10.md`. Report each close to your outbox with the commit hash.
