---
chapter: 1
title: "The Perception Faculty — Raw Sensation Becomes Context"
volume: XII
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
source: "19_cognitive_plan_architecture.md Layer 2 + vision/desktop/voice code"
implementation: PARTIAL
audit_status: OPEN
dependencies:
  - Volume XV (World State — consumes PerceptionResult)
  - Volume V/CONTRACTS.md (envelope, lifecycle, base contract)
---

# Chapter 1: The Perception Faculty

## 1.0 Purpose

Sensory faculties observe; the Perception Faculty **understands**. It transforms raw,
multimodal sensor output into a single typed `PerceptionResult` — context, not pixels —
which then populates the World State (Vol XV) and reaches the Executive through
`CognitiveState`.

> "Camera sees coffee mug" → "warm mug, on desk, near keyboard, 8:30, working session."
> Perception is where sensation becomes meaning. (Cognitive Plan Architecture, Layer 2.)

It **interprets; it never decides** (One Brain). Audit fix:
`faculties/perception/perception_faculty.py`.

## 1.1 Principle

- **Sensation ≠ perception.** Layer 1 (Sensory) captures; Layer 2 (this) interprets. Keep
  them separate so a sensor failure never fabricates understanding.
- **Interpret, don't fabricate.** If the input is ambiguous, perception reports low
  confidence and says so — it never invents detail (anti-fabrication, shared with memory).
- **One transform, then freeze.** Perception runs once per turn (or per sensor event),
  producing a `PerceptionResult` that is frozen and handed on — no re-interpretation
  downstream.

## 1.2 The PerceptionResult

```
PerceptionResult (frozen):
  modality_reads:  { vision, window, voice, files }   # per-source raw → interpreted
  scene:           str        # one-line context ("focused coding session in VS Code")
  active_surface:  enum { creative, code, browser, terminal, media, idle, unknown }
  salient_objects: [ {label, where, relevance} ]      # from vision, relevance-ranked
  user_activity:   enum { working, browsing, watching, away, conversing, unknown }
  confidence:      float 0.0–1.0
  source_health:   { source: {status ∈ live|stale|absent, ts} }
```

## 1.3 Sensor Sources → interpreted reads

| Source | Raw (Layer 1) | Live code | Interpreted (Layer 2) |
|---|---|---|---|
| Vision | screenshot | `plugins/vision/`, `tools/vision_agent.py` (GPT-4o) | salient_objects, scene, active_surface |
| Window | frontmost app | `desktop/window_state.py` | active_surface, user_activity |
| Voice | audio | `voice/stt.py` (Whisper) | transcript + prosody hint (feeds Language) |
| Files | recent/dropped | `desktop/file_drop_handler` | active project context |

**Rule (MUST):** each source is independently degradable — one failing yields
`status: absent` for that modality, never blocks the `PerceptionResult`.

## 1.4 Faculty Contract

```
Faculty:
  name:            PerceptionFaculty
  version:         1.0.0
  purpose:         Transform raw multimodal sensor output into one typed PerceptionResult
                   (context), before attention/decision. Interprets; never decides.
  contributes_to:  CognitiveState (via World State domains, Vol XV)
  runs_in:         response-path (per turn) + event-driven (sensor events)

Inputs:
  - type: vision_capture   source: plugins/vision, tools/vision_agent   required: false
  - type: window_state     source: desktop/window_state.py              required: false
  - type: voice_transcript source: voice/stt.py                         required: false
  - type: file_events      source: desktop/file_drop_handler            required: false

Outputs:
  - type: perception_result destination: World State (Vol XV) + CognitiveState
    description: scene, active_surface, salient_objects, user_activity, confidence.

Dependencies:
  - faculty: WorldStateFaculty (Vol XV, hard — consumes the result)
  - background: vision loop (soft — supplies captures; text-only degrade if off)

Failure Modes:
  - condition: a modality unavailable   fallback: mark that source absent; perceive from the rest; lower confidence.
  - condition: vision permission denied  fallback: no visual perception; window/voice/files still interpreted; eLo must not claim to "see".
  - condition: ambiguous scene           fallback: report low confidence + generic activity; never fabricate specifics.
  - condition: all sensors absent         fallback: PerceptionResult = idle/unknown; turn proceeds.
```

## 1.5 Faculty Lifecycle

Universal lifecycle (CONTRACTS.md §3). `PROCESSING` = gather modality reads → fuse into
scene/activity → freeze `PerceptionResult`. Event-driven captures (a screenshot from the
vision loop) update the next turn's perception, never the current frozen one.

## 1.6 Message Envelope Binding

Per CONTRACTS.md §2. `sender: PerceptionFaculty`; `payload.type: perception_result`;
`confidence` = perception confidence; leaves `context.significance = 0.0` (Ch.5 owns it).
Honesty gate: when vision is absent/denied, the result MUST carry that in `source_health`
so downstream faculties never assert eLo saw the screen (Vol XV IT-2).

## 1.7 Acceptance Tests

```
FT-1  Sensation → context      Given a screenshot of an IDE, Then scene="coding session", active_surface=code, salient_objects ranked.
FT-2  One transform, frozen     Given a turn, Then exactly one PerceptionResult is produced and frozen; no re-interpretation downstream.
FT-3  Feeds World State         Given a PerceptionResult, Then Vol XV desktop/user/browser domains populate from it.
ST-1  Modality isolation        Given vision off, Then window+voice+files still perceived; confidence lowered; no crash.
ST-2  Honesty on no-vision      Given screen-record denied, Then source_health.vision=absent and eLo does not claim to see the screen.
ST-3  No fabrication            Given an ambiguous blur, Then low confidence + generic activity; no invented objects.
IT-1  Perception → World State → Cognition   Raw sensors → PerceptionFaculty → LiveWorldState (Vol XV) → Executive reasons on context.
```

## 1.8 References
- `19_cognitive_plan_architecture.md` (Layer 2). `Volume_XV/` (World State — consumer).
- Code: `plugins/vision/`, `tools/vision_agent.py`, `desktop/window_state.py`, `voice/stt.py`.
- `ARCHITECTURE_AUDIT.md` gap #5. `Volume_V/CONTRACTS.md`.

---
**Status: READY FOR REVIEW** — Perception Faculty spec with contract/lifecycle/envelope/tests. Closes Audit gap #5.