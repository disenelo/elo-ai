---
id: WO-042
title: "Faculty health registry — persistent degraded/offline state per faculty; Executive routes on it."
owner_seat: SEAT-ENG-001 (Builder / eLo OS — Cognitive Core)
priority: P0
review_required: David sees consistent, non-oscillating faculty state
status: OPEN — Chief Architect diagnosis 2026-08-03
epic: "Executive Authority" (generalises WO-032 backend health to ALL faculties)
---
# WO-042 — faculty health registry
## The bug (Chief Architect)
Memory/backend/tools oscillate CONNECTED↔TIMEOUT↔fallback because the Executive doesn't track
faculty health. Backend loops (mark unhealthy → keep hitting it). Memory answers "yes/no/backup"
on consecutive turns. There is no health monitor.
## Fix (Builder Cognitive Core)
- A health registry: each faculty (reasoning, memory, tools, embodiment, backend) reports
  CONNECTED / DEGRADED / OFFLINE, persisted across turns (not recomputed blindly each call).
- Executive routes on it: mark a faculty unhealthy → stop routing to it → periodically retry →
  recover → switch back. Generalises WO-032's backend-health file to every faculty.
## Acceptance
1. Faculty state is stable across turns, not per-call oscillation. 2. A broken faculty is quarantined + retried, not hammered every turn.
