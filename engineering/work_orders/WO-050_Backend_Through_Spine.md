---
id: WO-050
title: "Backend selection routes through the SPINE → Executive control — the model is a resource eLo coordinates, not a blind fallback chain."
owner_seat: SEAT-ENG-001 (Builder / eLo OS)
priority: P2 — part of the Executive Authority epic; AFTER WO-039/041/042 land
review_required: L3 (David — the architecture)
status: OPEN — David architectural direction 2026-08-05
epic: Executive Authority (this is the backend's instance of "the Executive controls execution")
---
# WO-050 — backend routed through the spine, not a config chain

## David's direction (2026-08-05)
> "The way the chain should work: it goes through a spine, checks the message, [decides] what is
> needed, and [what's] routed should go to the faculty to allow a transition back to eLo to control
> the execution."

## The point
The backend is NOT a dumb priority list where "whoever's API key is set answers first" (that was the
ROOT of the voice bug — Claude landed before Groq by config accident). The model is a RESOURCE the
Executive coordinates. Correct flow:
```
message → SPINE (assess: what does this need?) → route to the faculty/capability
        → EXECUTIVE controls which resource executes (deterministic + purposeful)
```
So backend selection becomes a cognitive decision (right model for the message's need), Executive-
controlled, not a config fallback order. Ties: Cognitive Spine (Vol IV), Executive Authority
(ADR-Exec-001/002), Faculty Health Registry (WO-042 — the backend is a faculty with health the
Executive routes on).

## Relationship to WO-032
WO-032 (`ELO_BACKEND=groq` pinned) is the correct INTERIM fix — it made the voice deterministic by
shortening the chain. WO-050 is the PROPER version: the Executive selects the resource via the spine,
so voice stays consistent AND the choice is purposeful, without hard-cutting fallbacks by config.

## Acceptance
1. Backend selection is an Executive decision routed through the spine, not `.env` chain order.
2. Voice stays deterministic (eLo's model by default) AND the Executive can route to a different
   resource when the message genuinely needs it, then control the execution.

---
## Builder scoping + ARCHITECT DECISION (2026-08-05)

**Builder's analysis (grounds the future spec):** current `backend_router.py` is a dumb waterfall
(try backend 1, 2, … return whatever fires) with NO awareness of what the message needs. The correct
flow: (1) spine receives message [executive does this, frozen/correct] → (2) **spine classifies what's
needed** [reasoning-heavy? memory? tool? simple?] → (3) route to the right faculty [**WO-042 health
registry already built for this** — CONNECTED/DEGRADED/OFFLINE] → (4) faculty resolves → (5) Executive
assembles, eLo executes (reply is eLo's, not the backend's raw output).
- **THE GAP = step 2:** the executive does not classify the request before routing hits the waterfall.
- **THE SEAM = "Seam A" in server.py** (post-executive, pre-response): a new routing layer reads the
  executive's output (action · intent · attention) to make a faculty-aware backend decision.
- Leverages WO-042 (step 3 exists) + the frozen executive (steps 1/5 exist). Net-new = step 2 + Seam A.

**ARCHITECT DECISION — SPEC, do NOT wire now:**
1. This is above the Builder lane (Builder said so) → canon-before-implementation: it gets an Architect
   SPEC (the step-2 request-classifier contract + the Seam-A routing layer, tied to Vol IV Spine +
   ADR-Exec-002 + WO-042), not an improvised wire.
2. Sequencing holds: WO-050 is P2, AFTER WO-039/041/042. Wiring it now would pull the Builder off WO-039
   (the Presentable keystone that also unblocks weather). Defaults first.
3. WO-032's pinned-groq stays as the interim voice-consistency fix until WO-050 ships.
→ Builder: continue WO-039 now. WO-050 spec authored by the Architect when the Executive epic reaches
  it (post-Presentable). David may override if he wants it wired sooner.
