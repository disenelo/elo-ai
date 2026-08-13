---
chapter: 3
title: "The Perception → World-State Handoff — Producer to Holder"
volume: XII
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PENDING (contract defined; wiring to LiveWorldState domains pending)
audit_status: OPEN
received: 2026-08-10
dependencies:
  - Volume_XII/01_Perception_Faculty.md (produces PerceptionResult)
  - Volume_XV/01_Unified_World_State.md (holds the frozen LiveWorldState)
  - Volume_XV/02_Sensor_Domains.md (the domains perception populates)
  - Volume_V/CONTRACTS.md (envelope, lifecycle)
---

# Chapter 3: The Perception → World-State Handoff

## 3.0 Purpose

Volume XII **produces** understanding; Volume XV **holds** it. This chapter defines the
single seam between them: how a frozen `PerceptionResult` (Ch.1) becomes the perception-
derived fields of the frozen `LiveWorldState` (Vol XV Ch.1), and — just as importantly —
what perception does **not** do once it has produced its result.

> Perception is the transform; World State is the container. (Vol XII `00_Metadata`.)
> Two frozen objects, one handoff, no overlap.

Getting this boundary wrong is how "World State" ends up meaning two different things, or
how a sensor gets read twice per turn and drifts. This chapter makes the seam explicit so
the Architecture Agent can wire it without inventing a third object.

## 3.1 The division of labour (crisp boundary)

| | Volume XII — Perception | Volume XV — World State |
|---|---|---|
| **Role** | Producer | Holder |
| **Verb** | *interpret* raw signal → meaning | *assemble* meanings → one frozen object |
| **Object** | `PerceptionResult` (per capture/turn) | `LiveWorldState` (once per turn) |
| **Scope** | vision, window, voice, files, room | 11 domains (incl. time, weather, calendar, music…) |
| **Decides?** | never | never |
| **Owns freshness of** | its own modalities (`source_health`) | every domain (`domain_health`) |

**The one-line test:** if a field is *derived by interpreting a sensor* (this app = "creative
work"; this scene = "focused coding session"), Perception owns its computation. If a field
is *carried, timestamped, and frozen for the turn* so every faculty reads one copy, World
State owns its custody. Perception computes `active_surface`; World State stores it in
`DesktopState` with a freshness header.

## 3.2 What crosses the seam

`PerceptionResult` (Ch.1 §1.2) maps onto exactly three World-State domains. Nothing else
in `LiveWorldState` is perception-derived — the rest (time, weather, calendar, internet,
music, unity) comes from other sensors and background loops (Vol XV Ch.2).

```
PerceptionResult                         LiveWorldState domain (Vol XV)
────────────────                         ──────────────────────────────
active_surface        ───────────────►   DesktopState.active_surface
scene                 ───────────────►   DesktopState.window_title (context) / user context
user_activity         ───────────────►   UserState.presence / focus hint
salient_objects       ───────────────►   (desktop context; robot: room objects)
source_health.vision  ───────────────►   EnvironmentState.vision_active  (honesty gate)
confidence            ───────────────►   domain_health.desktop.confidence
modality_reads.*      ───────────────►   (provenance; not re-exposed raw downstream)
```

**Handoff rule (MUST):** World State's assembly (`assemble_world_state`, Vol XV §1.4)
**reads** the `PerceptionResult` for the turn and copies these fields into the relevant
domain slices, stamping each with `{fresh_ts, confidence, source="PerceptionFaculty",
status}`. It does **not** re-interpret, re-rank, or re-classify. Perception's confidence
becomes the domain's confidence — World State never inflates it.

## 3.3 Order of operations in a turn

```
top of turn
   │
   ├─ 1. Sensation caches are current (background loops, Ch.2)          [Layer 1]
   │
   ├─ 2. PerceptionFaculty.perceive_from_live_state() → PerceptionResult (frozen)   [Ch.1]
   │
   ├─ 3. WorldStateFaculty.assemble_world_state(turn_id):               [Vol XV §1.4]
   │        reads the PerceptionResult (soft dep) + other sensors
   │        → copies perception fields into desktop/user/environment domains
   │        → freezes LiveWorldState
   │
   └─ 4. Executive + faculties reason on the ONE frozen world           [Vol XV §1.5]
```

- Perception runs **before** World-State assembly and is a **soft dependency** of it
  (Vol XV §1.6: "PerceptionFaculty (soft — without it, vision-derived domains degrade").
  If perception is absent, `desktop/user/environment` fall back to their neutral defaults
  with `status: absent`; the turn still proceeds.
- Both objects are **frozen** before any faculty reads. Perception is not re-run mid-turn;
  a new capture updates the *next* turn (Ch.1 §1.5, Vol XV ST-3).

## 3.4 Single-writer & no-duplication discipline

**3.4.1 Perception is the sole interpreter of its modalities.** No faculty (and not World
State) re-derives `active_surface` from the raw app string. If two places computed it, they
could disagree — the exact drift the unified transform exists to remove.

**3.4.2 World State is the sole custodian.** Faculties read perception-derived fields **from
`LiveWorldState`**, not from `PerceptionResult` directly, and never from the raw sensors
(Vol XV §1.5 read discipline). `PerceptionResult` is an internal producer artifact; the
public surface is the World-State domain.

**3.4.3 One read of each sensor per turn.** A sensor is read once — by its Layer-1 loop or
by perception — and the value flows forward. World-State assembly "reads caches, never
triggers" (Vol XV §1.4); perception likewise reads caches (Ch.2 §2.1.3). No sensor is
touched twice in a turn.

## 3.5 Honesty carries across the seam

The anti-fabrication guarantee must survive the handoff intact:

- `PerceptionResult.source_health.vision = absent` (screen-record denied, or loop off)
  MUST land as `EnvironmentState.vision_active = false` in `LiveWorldState`, so any faculty
  checking "may I say I see the screen?" gets the truthful answer (Vol XV IT-2, §2.9).
- A low `PerceptionResult.confidence` MUST NOT be rounded up to a confident domain. World
  State carries perception's confidence verbatim into `domain_health`.
- Absent perception → absent/neutral domains, **never** a fabricated scene. The degraded
  world is honest (Vol XV IT-2: "eLo does not claim to see the screen").

This is the same discipline Ch.4 enforces *inside* perception, held now at the boundary:
truth in must equal truth out.

## 3.6 Handoff contract

```
Handoff:          PerceptionResult → LiveWorldState (perception-derived domains)
producer:         PerceptionFaculty (Vol XII Ch.1)
consumer:         WorldStateFaculty.assemble_world_state (Vol XV Ch.1 §1.4)
coupling:         soft (World State degrades gracefully if perception absent)

Copies (read-only, with freshness stamp):
  active_surface      → DesktopState.active_surface
  scene               → DesktopState / user context
  user_activity       → UserState (presence/focus hint)
  source_health.vision→ EnvironmentState.vision_active
  confidence          → domain_health.desktop.confidence

Invariants (MUST):
  - World State never re-interprets; it copies + stamps freshness.
  - Perception confidence is carried verbatim (never inflated).
  - vision-absent → vision_active=false (honesty preserved).
  - Faculties read these fields from LiveWorldState, never from PerceptionResult.
```

## 3.7 Acceptance Tests

```
FT-1  Perception fields populate the right domains
  Given:  PerceptionResult{active_surface=code, user_activity=working}
  When:   assemble_world_state reads it
  Then:   DesktopState.active_surface=code AND UserState reflects working
          AND domain_health.desktop.source="PerceptionFaculty"

FT-2  Confidence carried verbatim
  Given:  PerceptionResult.confidence=0.55
  Then:   domain_health.desktop.confidence=0.55 (not rounded up)

ST-1  Perception absent → graceful degrade
  Given:  no PerceptionResult this turn
  Then:   desktop/user/environment = neutral defaults, status=absent, in degraded[]
          AND the turn still completes

ST-2  Honesty across the seam
  Given:  PerceptionResult.source_health.vision=absent
  Then:   EnvironmentState.vision_active=false
          AND no downstream faculty asserts eLo saw the screen (Vol XV IT-2)

IT-1  No double-read / no re-interpretation
  Given:  active_surface computed once in perceive()
  Then:   assemble_world_state copies it unchanged; no second surface inference exists
```

## 3.8 Open Questions (flagged for CA / David)

- **OQ-1 — Wiring not yet built.** Today `perceive_from_live_state()` exists and
  `LiveWorldState` is spec'd, but the copy step in §3.2 is **PENDING** implementation —
  the faculties still read some sensors directly (the drift Vol XV removes). This chapter
  defines the target; it does not claim it is wired. (Verify-before-claim.)
- **OQ-2 — Robot salient_objects → which domain?** On the desktop `salient_objects` is
  screen context; on the robot it is room objects. Does the robot need a distinct
  world domain (e.g. a physical `RoomState`) or does it overload `DesktopState`? Cross-cuts
  Vol XV; flagged, not decided here.

## 3.9 References

- Ch.1 `01_Perception_Faculty.md` (`PerceptionResult`). Ch.2 `02_Sensation_Layer.md`.
- `Volume_XV/01_Unified_World_State.md` §1.4–1.6 (assembly, read discipline, soft dep).
- `Volume_XV/02_Sensor_Domains.md` §2.1 Desktop, §2.2 User, §2.9 Environment.
- Code: `faculties/perception/perception_faculty.py` (`perceive_from_live_state`),
  `world/live_world_state.py` (Vol XV, PENDING), `blender_bridge/state_writer.py`.
- `ARCHITECTURE_AUDIT.md` gaps #2 (World State) & #5 (Perception).

---

```
Chapter 3 — The Perception → World-State Handoff
Status: READY FOR REVIEW
Files: Volume_XII/03_World_State_Handoff.md
Boundary: Vol XII (producer) ↔ Vol XV (holder) drawn crisply; no third object
Handoff Contract: Included (5 field copies + 4 invariants)
Acceptance Tests: Included (FT ×2, ST ×2, IT ×1)
Open Questions: 2 flagged (wiring PENDING; robot room-domain)
```

READY FOR REVIEW
