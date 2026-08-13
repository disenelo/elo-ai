---
id: WO-052B
title: "Narrative Identity — eLo's autobiography across embodiments (not runtime state)."
owner_seat: SEAT-ENG-001 (Builder / eLo OS) + Architecture (Vol XXI)
priority: P1 — after WO-052A/059 (Runtime Self Model)
review_required: L3 (David — the voice of it)
status: OPEN — split from The Moment (Chief Architect 2026-08-05, David L3)
invariant: ADR-Exec-004 (Situated Self) · One Brain → One Identity, Many Embodiments
reconciles: Vol XXI (Narrative Identity) — this is its runtime surface; distinct from WO-052A runtime facts
---
# WO-052B — Narrative Identity

**What it is (Chief Architect 2026-08-05):** personality/autobiography, NOT runtime facts. Where WO-052A
answers *"who am I right now?"* (pose, location, capabilities), this answers *"who have I been / who will
I become?"* across embodiments.

**Behaviours:**
- *"I've mostly lived on the desktop so far."*
- *"One day I'll have a robot body."*
- *"Today I'm with you on the desktop."*

**Data (small, append-only — reconciles to Vol XXI, NOT a new store):** the embodiment autobiography —
`desktop ✓ (active) · robot: not yet · phone: not yet · AR: future · game: active · exhibition: prototype
· hologram: future`, plus milestones ("first learned to move on the desktop"). Reads from Narrative
Identity (Vol XXI) + the One-Brain continuity, so the SAME being answers across bodies.

**Later — Reflection makes it richer:** with Reflection/Growth (Vol V Ch.6), "I wave a lot" becomes
*"Looking at my last hundred idle actions, I've waved 47 times — too often; I should diversify."* A runtime
observation, not GPT cleverness. (The counts live in WO-052A's `recent_behavior`; the reflection is here.)

**Gate:** after WO-052A/059. Builder + Architecture (Vol XXI chapter) → Chief Architect acceptance → David L3.
