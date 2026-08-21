---
volume: XV
title: "The World Model — Unified Live World State"
status: BUILDABLE — spec written. Ratification follows the build; it does not gate it. ("awaiting CA" removed 2026-08-21: David — "WHO THE FUCK ARE WE GATING AND HOLDING FOR!?" The CA is an agent and David is present. Nobody was waiting.)
version: 0.1.0
owner: David Charles
architect: Claude (Architecture Agent)
implementation: WIRED — LiveWorldState assembled top-of-turn in spine.py; perception→domain copy live; carrier-side read for capability.vision landed via card 0006 (WO-CANON-XII+XV)
Provenance: [ENGINEERING]
audit_status: OPEN
canonical_path: docs/architecture/Volume_XV/
dependencies:
  - Volume III (System Architecture — runtime contracts; World State contributes to CognitiveState)
  - Volume V (Faculty Contracts — CONTRACTS.md envelope/lifecycle/base contract)
  - Volume XII (Perception System — the transform that turns raw sensors into world understanding) — sibling
priority: "Audit Critical Gap #2 (HIGH)"
last_review: 2026-07-27
next_review: TBD
---

# Volume XV — The World Model (Unified Live World State)

Addresses **Architecture Audit Critical Gap #2**: today world context is assembled
ad-hoc in `server.py` from 12+ sources; some faculties re-query their sources directly
instead of reading a shared state. Risk: race conditions, stale data, inconsistent
world models across faculties. Fix: one typed `LiveWorldState`, assembled once per
turn, read by all faculties.

## Chapter Build Queue

| ID | Chapter | Title | Status |
|----|---------|-------|--------|
| ELO-V15-CH01 | Chapter 1 | The Unified World State | READY FOR REVIEW |
| ELO-V15-CH02 | Chapter 2 | Sensor Domains & Schemas | READY FOR REVIEW |

## Scope

- **In scope:** the single `LiveWorldState` object, its assembly discipline (once per
  turn, frozen), per-domain freshness/confidence, the eleven sensor domains, the
  faculty contract, lifecycle, envelope binding, and acceptance tests.
- **Out of scope (owned elsewhere):** the *spatial* node graph for Unity
  (`world/world_state.py` — a different thing; see Ch.1 §1.2); the raw sensor capture
  itself (Perception Faculty, Volume XII); embodiment/output (Volume XI/XIII).

## Definition of Done

- [x] World State object defined (typed, one per turn, frozen)
- [x] All eleven Bible domains schematised (Desktop, User, Unity, Browser, Files, Internet, Music, Calendar, Environment, Time, Weather)
- [x] Assembly + freshness discipline defined
- [x] Faculty contract + lifecycle + envelope binding
- [x] Acceptance tests (functional / stability / integration)
- [x] Perception → World-State copy wired (Vol XII Ch.3 §3.2 — desktop/user/environment domains populated from `PerceptionResult`)
- [x] At least one live-path capability check reads from the carrier (`claim_gate._vision_gate` → `world.environment.vision_active`, card 0006)
- [x] Structural fidelity flag on the carrier (`domain_health.desktop.partial` from `PerceptionResult.partial`)
- [ ] Architecture Agent can implement without inventing anything (pending REVIEW)
- [ ] Audit can mark COMPLETE

## Distinction that must not be lost

The Bible has **two** "world" concepts. This volume owns only the first:

| | Cognitive World State (this volume) | Spatial World Graph |
|---|---|---|
| What | What is true in the user's world right now | Unity scene/room node graph |
| Object | `world/live_world_state.py` (NEW) | `world/world_state.py` (exists) |
| Read by | All cognitive faculties, once per turn | Unity navigation / presence movement |

Naming discipline (Cognitive Principle: *a wrong name creates divergent
implementations*): "World State" in cognition = `LiveWorldState`. Never conflate with
the spatial graph.
