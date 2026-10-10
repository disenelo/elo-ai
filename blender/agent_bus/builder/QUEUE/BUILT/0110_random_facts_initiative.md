# WO-B1-0110 — Random Facts + WKG Initiative
**Seat:** Builder 1  
**Priority:** P1 — demo milestone end of October  
**Source:** `docs/architecture/_intake/SOURCE_DEMO-MILESTONE_2026-10-10.md` [DAVID 2026-10-10]  
**Date:** 2026-10-10

---

## What

eLo surfaces random facts unprompted — not on every turn, but occasionally during RESTING/AWAKE states when something in working memory or WKG is interesting enough to share.

This is the LIFE process expressing curiosity without David asking. "Did you know..." or just dropping something he's been thinking about.

---

## How

- During RESTING tick (`life_tick`), if a WKG node above significance threshold hasn't been mentioned recently → candidate for spontaneous surface
- Gate: only when David is present (AWAKE state, recent message in last 10 min) and there's a natural gap (eLo isn't mid-task)
- Format: short, eLo's voice. Not a lecture. One thing. Moves on.
- Source: WKG graph (culture, science, eLo's own experiences from interactions.json)
- Coordinate with Builder 2 — this fires from `life_tick`, which is Builder 2's file

Spec the trigger to Builder 2 via inbox. Builder 1 wires the server.py hook that delivers it.

---

## Done when

During a live session eLo surfaces a fact or observation unprompted. Board confirms it came from WKG (not generated). David confirms it feels natural, not intrusive.

File to Board for sign-off.
