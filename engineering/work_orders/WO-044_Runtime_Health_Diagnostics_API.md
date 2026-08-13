---
id: WO-044
title: "Runtime /health diagnostics — expose every faculty's live state (the self-diagnosis David asked for)."
owner_seat: SEAT-ENG-001 (Builder / eLo OS — Runtime)
priority: P1
review_required: David can see a real faculty status readout
status: OPEN — Chief Architect diagnosis 2026-08-03
epic: "Executive Authority" (consumes WO-042 registry)
---
# WO-044 — runtime diagnostics API
## The bug (Chief Architect)
Asked "what thinking can't you access?", eLo answered philosophically. David wanted a concrete
readout: Memory OFFLINE, Reasoning ONLINE, Spotify ONLINE, Unity CONNECTED, Browser DEGRADED,
Embodiment FAILED-ACK, Fallback ACTIVE. The faculties exist; the runtime should expose them.
## Fix (Builder Runtime)
- A `/health` (or state-file) surface reporting each faculty's live state from the WO-042 registry.
- eLo can answer health questions from it truthfully ("memory's degraded right now"), and the
  dashboard/One-Brain can render it. Feeds the observability layer (INT7-HEAT).
## Acceptance
1. A real per-faculty status readout exists. 2. eLo answers "are you working right?" from real state, not philosophy.
