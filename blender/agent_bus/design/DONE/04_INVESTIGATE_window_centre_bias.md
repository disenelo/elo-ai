# 04_INVESTIGATE_window_centre_bias.md

**WO:** WO-089 (new) · **Seat:** design · **Priority:** P2 · **Reserved?** no
**Type:** INVESTIGATION first (read-only), then a fix card

## David (live 2026-08-10)
> "He still stays in the centre of most of the windows — that's something else that should be pushed for
> investigation."

## The symptom
eLo settles at/near the **centre** of a window instead of using it as terrain — on its top edge, at a corner,
on a ledge, off to one side. Centre-parking reads as "sprite pinned to a rect," not a character inhabiting a
place. It also fights the whole roam×OS intent (edges are ledges, tops are walkable, corners are perch spots).

## Step 1 — INVESTIGATE (read-only, report before changing anything)
Find WHY the centre wins. Candidates to check and rule in/out:
- Does the perch/target resolver pick a window's **centre point** (rect centre) rather than a **surface**
  (top edge / ledge from the `EloDesktopNav` surface graph)?
- Is roam's `roamTarget` defaulting to window centre when no graph waypoint is available (the fallback path)?
- Is the placement/re-attach after drag/drop/warp snapping him to rect centre?
- Is there a screen-position bias rule (an older WO wanted him top-biased / not blocking buttons) that now
  resolves to centre?
- Does the occlusion/"behind window" logic force a centre anchor so he reads as inside the window?

**Deliver:** which mechanism is actually doing it (file + line), and whether it's ONE cause or several paths
all landing on centre. Report to your outbox. **Do not change behaviour in this step.**

## Step 2 — the fix (only after the report; can be the same run if the cause is obvious and small)
Target behaviour: eLo prefers **surfaces and edges** — window top edge, ledges, corners, sides — and centre
is at most a rare choice, never the default. Use the existing surface graph as the source of perch targets;
don't invent a parallel placer. Keep it Inspector-tunable so David can bias it at end-of-day test.

## Test (without David)
Inject a multi-window layout → confirm chosen perch/roam targets land on graph SURFACES (top edges/ledges),
not rect centres, across repeated picks. Log the chosen target + why. No regressions: perch · roam · drag ·
click-through · gun-runoff.

## Done when
investigation reported + (if fixed) test green + committed → hash, DONE/, outbox line, next card.
Ties: WO-049 / 049-A roam×OS (desktop as terrain) · WO-074 C edge-roam · WO-075 landing.

## Result
- cause found:
- commit:
- test:

## Result (WO-089)
- cause: uniform Random.Range(wrPatrolRange) rest target clusters mid-window (DesktopBuddy.cs:1755 & 1826); full-width ledge makes mid=centre
- fix commit: f5ebefc (bias rest/patrol to outer bands 0.01-0.28 / 0.72-0.99 -> ends/corners)
