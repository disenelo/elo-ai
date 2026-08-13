---
chapter: 2
title: "The Sensation Layer — Raw Sources Before Meaning"
volume: XII
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PARTIAL (sensors live; unified capture contract pending)
audit_status: OPEN
received: 2026-08-10
dependencies:
  - Volume_XII/01_Perception_Faculty.md (consumer — sensation feeds the transform)
  - Volume_XV/02_Sensor_Domains.md (the world domains these sources ultimately populate)
  - Volume_V/CONTRACTS.md (envelope, lifecycle, base contract)
---

# Chapter 2: The Sensation Layer

## 2.0 Purpose

Before eLo can *understand* anything, something must *capture* it. This chapter defines
**Layer 1 — Sensation**: the raw sensor sources that produce observations for the
Perception Faculty (Ch.1) to interpret. It is the boundary at the bottom of the
perception stack — where photons, pixels, audio, and OS state become bytes eLo can reason
over, and *nothing more*.

> Sensation captures; perception interprets; the Executive decides. Keep the three
> separate so a sensor failure can never fabricate understanding, and a fabrication can
> never masquerade as a decision. (Cognitive Plan Architecture, Layers 1–2.)

Ch.1 defines the transform (`perceive()` → `PerceptionResult`). This chapter defines its
**inputs**: what each source is, where it lives in the live code, what it may and may not
emit, and how it degrades. The Perception Faculty's `perceive()` signature
(`faculties/perception/perception_faculty.py`) is the contract these sources must fill —
they supply `vision_text`, `window_app`, `window_title`, `voice_transcript`,
`file_context`, `vision_permitted`, and (optional) `spatial_data`.

## 2.1 Principle — Sensation is dumb on purpose

**2.1.1 A sensor reports; it does not conclude.** `window_state.py` returns "frontmost app
= Visual Studio Code". It does **not** return "David is coding". The classification
("code surface", "working") is a perception step (Ch.1 `_infer_surface` /
`_infer_activity`), never the sensor's job. This keeps interpretation in one place and
auditable.

**2.1.2 Every source is independently degradable.** No single sensor is required. Each maps
to a modality in `PerceptionResult.source_health` with `status ∈ {live, stale, absent}`.
A dead camera → `vision: absent`; a denied screen-record permission → `vision: absent`
with `vision_permitted=False`; the turn still proceeds on whatever remains (Ch.1 ST-1).

**2.1.3 Capture is bounded and out-of-band.** Slow captures (a screenshot + a vision-model
round trip) run in **background loops** and write to a cache; perception **reads the
cache**, it never triggers a capture inline (this mirrors World-State's read-never-trigger
rule, Vol XV §1.4). The vision loop's own cadence (`tools/vision_loop.py`: 2s fast / 6s
backoff) governs freshness — perception inherits it via `source_health[...].ts`.

**2.1.4 One capture contract across bodies.** The same `perceive()` inputs are filled
whether the source is a Mac screen (desktop eLo) or a Pi camera (robot eLo). On the
desktop, perception reads the **screen**; on the robot, it reads the **room**
(`faculties/perception/robot_vision_bridge.py`). This is One Brain at the sensor boundary:
different senses, one interpretation contract.

## 2.2 The Sensation Sources

Five source families feed perception today. Each row: the raw signal, the live-code
anchor, the `perceive()` field it fills, and its degradation.

| # | Source | Raw signal | Live code | Fills | Degrades to |
|---|--------|-----------|-----------|-------|-------------|
| 1 | Screen vision | screenshot → model description | `tools/vision_loop.py`, `tools/vision_agent.py` | `vision_text` | `vision: absent` (loop off / quota / no-perm) |
| 2 | Window state | frontmost app + title | `desktop/window_state.py` | `window_app`, `window_title` | `window: absent` |
| 3 | Browser | open tabs / bookmarks / history | `desktop/chrome_reader.py` | (screen/desktop context) | no chrome lines emitted |
| 4 | Voice | mic audio → transcript | `voice/stt.py` (Whisper) | `voice_transcript` | `voice: absent` |
| 5 | Files | dropped / recent files | `desktop/file_drop_handler.py` | `file_context` | `files: absent` |
| 6 | Robot camera | Pi camera JPEG → description | `faculties/perception/robot_vision_bridge.py` | `vision_text` (room, not screen) | `vision: absent` (no picamera2) |
| 7 | Spatial (stub) | depth/pointcloud frame | `perception_faculty._stub_spatial_frame` (`ELO_SPATIAL_SENSOR=1`) | `spatial_data` | `spatial: absent` |

### 2.2.1 Screen vision (desktop)

`tools/vision_loop.py` runs as a daemon, screenshots the active surface, asks the vision
model (GPT-4o / Gemini path) for a structured attention read, and writes
`blender_state.json["vision"]` (`{active, attention, focus{x,y}, app}` plus a description).
Perception reads that cache in `perceive_from_live_state()` via
`blender_bridge.state_writer.read()`. It only treats vision as present when
`vision.active` **and** `vision.description` are set — otherwise `vision: absent`.

- **Permission is a hard gate.** If screen-record permission is denied, `vision_permitted`
  is `False` and perception marks vision absent — eLo must not claim to see the screen
  (Ch.1 ST-2; enforced against `EnvironmentState.screen_record_perm`, Vol XV §2.9).
- **Cadence:** 2s active → 6s idle backoff; a 429 pauses that provider 60s
  (`_QUOTA_BACKOFF`). Perception never waits on this; it reads last-written.

### 2.2.2 Window state

`desktop/window_state.py` is a **read-only** snapshot of the frontmost app + window title
(macOS `osascript`, graceful fallback, no window manipulation — "shadow mode"). It carries
a coarse app→activity map internally, but the canonical surface/activity classification
lives in the Perception Faculty, not here (2.1.1). This is the highest-signal, cheapest
source and is read **live** at assembly.

### 2.2.3 Browser (Chrome)

`desktop/chrome_reader.observe(query)` returns open tabs, matched bookmarks, and history.
It is a **screen/desktop-context** source: it tells perception what surfaces exist, at
**domain/title granularity only** (privacy: never full page content). Its output is the
raw material the fidelity guard (Ch.4) polices — truncated titles, unrelated tabs — so it
is deliberately a *sensation* source, not an interpretation.

### 2.2.4 Voice

`voice/stt.py` (Whisper) turns mic audio into a transcript. Sensation stops at the
transcript **plus a prosody hint**; word-meaning and register (SOUTH_LDN_MODE /
PATOIS_MODE) are the Language Faculty's, carried through, never re-detected here
(Vol XV §2.2). Absent mic / STT → `voice: absent`.

### 2.2.5 Files

`desktop/file_drop_handler.py` emits dropped/recent-file events. This is event-driven
sensation: a drop produces a `file_context` string for the next turn's perception. The
*active project* truth is `project_registry.json` (Vol XV §2.5), not inferred here.

### 2.2.6 Robot camera (embodiment)

`faculties/perception/robot_vision_bridge.py` (INT-2) is the physical-body sensation path:
`picamera2 → JPEG → vision_agent.describe() → perceive()`. It has **no hard dependency on
picamera2** — the import is tried and falls back to `None` (vision absent) so the module
runs on macOS for integration testing. `robot_perceive()` fills `vision_text` from the
room, leaves `window_app/title` absent (a robot has no desktop), and routes everything
through the **same** `perceive()` as the desktop. `sensor_health()` reports
`{camera, mic}` for the robot presence engine.

## 2.3 The Sensation → Perception boundary (crisp)

```
LAYER 1  SENSATION  (this chapter)              LAYER 2  PERCEPTION (Ch.1)
─────────────────────────────────               ──────────────────────────
vision_loop   → blender_state.vision  ─┐
window_state  → app/title             ─┤
chrome_reader → tabs/bookmarks/hist   ─┼─► perceive(...)  ─►  PerceptionResult (frozen)
stt           → transcript            ─┤        (interpret: surface, activity,
file_drop     → file_context          ─┤         scene, salient_objects, confidence)
robot_camera  → room description      ─┘
```

**Boundary rule (MUST):** everything left of `perceive(...)` produces *signals*; nothing
left of it produces *meaning*. If a source ever starts emitting a conclusion
("David is focused"), that logic has leaked out of Ch.1 and must be moved back. The audit
check is mechanical: a sensation source's output must be reducible to a plain data field
in the `perceive()` signature.

## 2.4 Sub-faculty contract (Sensation Layer)

Sensation is not itself a decision-making faculty; it is a set of capture sources feeding
`PerceptionFaculty`. Its collective contract:

```
Component:       SensationSources (Layer 1)
feeds:           PerceptionFaculty.perceive()  (Ch.1)
runs_in:         background loops (vision) + live reads (window/browser) + events (files/voice)

Inputs (from the environment / OS / hardware):
  - screen pixels           → tools/vision_loop.py         (cached, 2s/6s)
  - frontmost window        → desktop/window_state.py      (live)
  - browser surfaces        → desktop/chrome_reader.py     (live, on query)
  - mic audio               → voice/stt.py                 (event)
  - file drops / recents    → desktop/file_drop_handler.py (event)
  - camera frame (robot)    → robot_vision_bridge.py       (on demand)

Outputs (all consumed by perceive()):
  - vision_text, window_app, window_title, voice_transcript, file_context,
    vision_permitted, spatial_data

Failure Modes:
  - condition: a source unavailable   → that modality absent; perception lowers confidence; turn proceeds.
  - condition: screen-record denied    → vision_permitted=False; eLo must not claim to see the screen.
  - condition: capture slow/timeout     → perception reads last cache with an older ts; never blocks the turn.
  - condition: all sources absent (cold start) → perceive() yields idle/unknown; turn proceeds.
```

## 2.5 Acceptance Tests (sensation-level)

```
FT-1  Live read fills window modality
  Given:  window_state returns app="Visual Studio Code"
  When:   perceive_from_live_state() runs
  Then:   window_app is populated, source_health.window=live

FT-2  Vision read is cache-sourced, never inline-triggered
  Given:  blender_state.vision.active=true with a description
  When:   perception runs
  Then:   vision_text is read from cache; no screenshot is taken inside perceive()

ST-1  Missing source is absent, not faked
  Given:  no mic / STT unavailable
  Then:   source_health.voice=absent; no transcript is invented

ST-2  Robot camera absent on macOS
  Given:  picamera2 not installed
  When:   robot_perceive() runs
  Then:   capture_frame() returns None → vision absent → confidence lowered → PerceptionResult still returned

IT-1  One capture contract, two bodies
  Given:  desktop perceive_from_live_state() and robot robot_perceive()
  Then:   both return a structurally identical, frozen PerceptionResult (Ch.1 contract)
```

## 2.6 Open Questions (flagged for CA / David)

- **OQ-1 — Capture-contract formalisation.** Today the sources fill `perceive()` args
  ad hoc from `perceive_from_live_state()`. Should Layer 1 gain a single typed
  `SensationBundle` object so new sources register uniformly? (PENDING — not invented here.)
- **OQ-2 — Prosody hint.** Ch.1 mentions a voice "prosody hint" feeding Language, but
  `stt.py` currently emits transcript only. Is prosody in scope for Sensation, or does it
  belong to a dedicated audio faculty? (PENDING.)
- **OQ-3 — Spatial sensor.** `spatial_data` is a **stub** gated by `ELO_SPATIAL_SENSOR=1`
  (`_stub_spatial_frame`, WO-025). Real depth/pointcloud hardware is unspecified; the
  domain shape is provisional and must not be treated as live capability. (PENDING.)

## 2.7 References

- Ch.1 `01_Perception_Faculty.md` — the transform these sources feed.
- `Volume_XV/02_Sensor_Domains.md` — the world domains perception ultimately populates.
- Code: `tools/vision_loop.py`, `tools/vision_agent.py`, `desktop/window_state.py`,
  `desktop/chrome_reader.py`, `voice/stt.py`, `desktop/file_drop_handler.py`,
  `faculties/perception/robot_vision_bridge.py`, `blender_bridge/state_writer.py`.
- `ARCHITECTURE_AUDIT.md` gap #5. `CO_WORKING_GUIDE.md` §6 (background loops).

---

```
Chapter 2 — The Sensation Layer
Status: READY FOR REVIEW
Files: Volume_XII/02_Sensation_Layer.md
Sources: 7 mapped (vision, window, browser, voice, files, robot camera, spatial-stub)
Boundary: Sensation → Perception drawn crisply (signals, not meaning)
Acceptance Tests: Included (FT ×2, ST ×2, IT ×1)
Open Questions: 3 flagged (capture contract, prosody, spatial hardware)
```

READY FOR REVIEW
