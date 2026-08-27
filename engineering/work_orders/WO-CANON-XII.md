# WO-CANON-XII — Perception: wire perceive()→World-State copy + structured fidelity flags (all modalities)

**Owner:** Builder (eLo OS — `faculties/perception/` + `server.py` fidelity rail). **Priority:** P2 — Horizon-2
(post-Presentable v1), Tier A. **Status:** DONE — 2026-08-27 (15/15 ATs pass; copy step + fidelity flags verified). **Closes:** Architecture Audit gap #5.

**Canon refs:** Volume XII — Ch.1 `01_Perception_Faculty.md`, Ch.2 `02_Sensation_Layer.md`, Ch.3
`03_World_State_Handoff.md`, Ch.4 `04_Perceptual_Fidelity.md`. Ties WO-076 (perception fidelity), WO-038 (source
labelling). Sibling: Volume XV (World State — the handoff holder).

## Problem / Goal
Sensors + the WO-076 PERCEPTION RAIL are LIVE; `perceive_from_live_state()` exists. Two integration points are
still PENDING: (a) the **Perception → World-State copy** (Ch.3 §3.2) — faculties still read some sensors directly,
the exact drift Vol XV removes; (b) **structured per-observation fidelity flags** on `PerceptionResult` (Ch.4 §4.3),
beyond the Chrome-only prompt rail. Goal: one frozen `PerceptionResult` per turn whose fields are copied verbatim
into `LiveWorldState` domains, carrying fidelity truthfully.

## Scope to DoD (grounded in Ch.1–Ch.4)
- **Unify the transform in `faculties/perception/perception_faculty.py`** so one `perceive(...)` produces one frozen
  `PerceptionResult` per turn: `modality_reads {vision, window, voice, files}`, `scene`, `active_surface`,
  `salient_objects [{label, where, relevance}]`, `user_activity`, `confidence`, `source_health {source:{status, ts}}`.
  Interpret, never decide; **never fabricate** (ambiguous → low confidence + generic activity); confidence may only be
  **lowered** by missing modalities, never raised. Each source independently degradable (`status: absent`, never
  blocks the result). One capture contract across bodies (desktop `perceive_from_live_state()` and
  `robot_perceive()`/`robot_vision_bridge.py` route through the same `perceive()`).
- **Read caches, never trigger inline** (mirror Vol XV): consume `tools/vision_loop.py` → `blender_state.json["vision"]`,
  `desktop/window_state.py`, `desktop/chrome_reader.py`, `voice/stt.py`, `desktop/file_drop_handler.py`. Screen-record
  permission is a hard gate → `vision_permitted=False` → vision absent (checked against `EnvironmentState.screen_record_perm`).
- **Ch.3 §3.2 copy step (the core PENDING wiring):** `assemble_world_state` (Vol XV) **reads** the turn's
  `PerceptionResult` and **copies** — without re-interpreting/re-ranking — into domain slices, stamping
  `{fresh_ts, confidence, source="PerceptionFaculty", status}`:
  - `active_surface` → `DesktopState.active_surface`; `scene` → `DesktopState.window_title`/user context;
    `user_activity` → `UserState.presence`/focus; `salient_objects` → desktop (robot: room) context;
    `source_health.vision` → `EnvironmentState.vision_active` (honesty gate); `confidence` → `domain_health.desktop.confidence`
    (carried **verbatim, never inflated**).
  - Order: sensation caches → `perceive_from_live_state()` → frozen `PerceptionResult` → `assemble_world_state()`
    copies + freezes `LiveWorldState` → faculties reason. Perception is a **soft** dependency of World State; absent →
    desktop/user/environment fall to neutral defaults `status: absent`, turn proceeds.
- **Single-read / single-writer discipline:** perception is sole interpreter of its modalities; faculties read
  perception-derived fields from `LiveWorldState`, never from `PerceptionResult` directly and never from raw sensors;
  one read of each sensor per turn (no double-read, no re-classification at the seam).
- **Ch.4 §4.3 structured fidelity flags (PENDING build):** promote the WO-076 rail from prompt-only to data — add a
  per-observation `partial: bool` + explicit "no asserted relations" so the guard is data, not just a string. Keep
  `_wo76_tag()` `[PARTIAL: …]` tagging + WO-038 source labelling in `server.py` as enforcement surface; inject the
  PERCEPTION RAIL only when real observation data exists (no false rail). Treat every observation independent unless
  data shows a link (no fabricated "X is touching Y").

## Definition of Done
- One frozen `PerceptionResult` per turn; its fields populate the correct `LiveWorldState` domains via the copy step
  with `source="PerceptionFaculty"` and confidence carried verbatim.
- No faculty reads perception-derived sensors directly anymore (drift closed with Vol XV).
- `PerceptionResult` carries structured fidelity (`partial` / no-asserted-relations); no fabricated object/scene/link;
  no "sees screen" claim when vision absent/denied.
- Audit can mark Vol XII COMPLETE.

## Tests to write (`tests/test_canon_xii_perception.py`, extend `tests/test_wo076_perception_fidelity.py`)
- Ch.1: FT sensation→context, one transform frozen, feeds World State; ST modality isolation, honesty on no-vision,
  no fabrication. Ch.2: live read fills window; vision read cache-sourced not inline-triggered; robot camera absent on
  macOS still returns a result; one capture contract two bodies.
- Ch.3: FT perception fields populate right domains (`source="PerceptionFaculty"`); FT confidence carried verbatim
  (0.55 stays 0.55); ST perception-absent graceful degrade; ST honesty across the seam; IT no double-read / no
  re-interpretation.
- Ch.4 (extend AT-1…AT-8): truncated title `[PARTIAL]`, clean title untouched, rail present on real data + survives
  merge, no false rail, no fabricated link/object, fidelity survives to speech.

## Dependencies + blocked-by
- **Blocked by:** WO-CANON-XV (the `LiveWorldState` object + `assemble_world_state` must exist for the §3.2 copy).
  Build order: World State object first, then this copy step + spine top-of-turn assembly.
- **Not blocked on** an alignment ruling (program: "ruling A? no") or David L3.
- Ties: WO-076 (fidelity), WO-038 (source labelling). Depends soft on `16_runtime_contracts.md` (CognitiveState).

## Lane
Builder (Python — `faculties/perception/perception_faculty.py`, `server.py` fidelity surface, the Vol XV copy step).
Architect coordinates only.
