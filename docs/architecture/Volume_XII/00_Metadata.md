---
volume: XII
title: "Perception System — From Sensation to Understanding"
status: REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
source: "Cognitive Plan Architecture (19_*) Layer 2 + live code"
implementation: PARTIAL (sensors + fidelity rail live; unified Perception Faculty + World-State wiring pending)
Provenance: [ENGINEERING][CREATIVE]
audit_status: OPEN
canonical_path: docs/architecture/Volume_XII/
dependencies:
  - Volume III (runtime contracts — PerceptionResult feeds CognitiveState)
  - Volume XV (World State — Perception populates the sensor domains)
  - Volume V/CONTRACTS.md (envelope, lifecycle, base contract)
priority: "Audit Critical Gap #5 (MEDIUM)"
last_review: 2026-08-10
next_review: TBD
---

# Volume XII — Perception System

Layer 2 of the Cognitive Plan Architecture (`19_cognitive_plan_architecture.md`). The
Perception System is the transform that turns **raw sensation into context** before
anything decides — "camera sees mug" becomes "warm mug, on desk, near keyboard, 8:30,
working session."

Addresses **Audit gap #5**: today raw observations (`plugins/vision/`, `tools/vision_agent.py`,
`desktop/window_state.py`, `voice/stt.py`) feed attention directly, with no unified
perception transform. Fix: `faculties/perception/perception_faculty.py` producing one
`PerceptionResult`.

## Chapter Build Queue

| ID | Chapter | Title | Status |
|----|---------|-------|--------|
| ELO-V12-CH01 | Chapter 1 | The Perception Faculty | READY FOR REVIEW |
| ELO-V12-CH02 | Chapter 2 | The Sensation Layer — Raw Sources Before Meaning | READY FOR REVIEW |
| ELO-V12-CH03 | Chapter 3 | The Perception → World-State Handoff — Producer to Holder | READY FOR REVIEW |
| ELO-V12-CH04 | Chapter 4 | Perceptual Fidelity — Verified Perception (No Fragments, No Fabricated Links) | READY FOR REVIEW |

**Chapter set rationale (no padding):** Ch.1 defines the transform (sensation→context);
Ch.2 defines its inputs (Layer-1 sources, incl. desktop/screen + robot camera); Ch.3 draws
the crisp Vol XII↔Vol XV boundary (Perception produces, World State holds); Ch.4 is the
fidelity/honesty guard (Verified Perception — grounded in the live WO-076 PERCEPTION RAIL).
Four chapters cover the scope with no overlap.

## Relationship to Volume XV (World State)

Clear division (both spec'd this program):
- **Volume XII (Perception)** = *interpret* raw sensor input into meaning (this app = "creative work").
- **Volume XV (World State)** = *assemble* those interpretations into one frozen per-turn object.

Perception is the transform; World State is the container. Perception writes into the
`LiveWorldState` domains (desktop/user/browser/environment); it does not itself decide.

## Definition of Done

- [x] PerceptionResult object defined (raw → context) — Ch.1
- [x] Sensor sources mapped (vision, window, browser, voice, files, robot camera, spatial) — Ch.2
- [x] Sensation → Perception boundary drawn (signals, not meaning) — Ch.2
- [x] Perception → World-State handoff + Vol XV boundary defined (producer/holder) — Ch.3
- [x] Perceptual fidelity guard (no fabrication, no fragments, no fabricated links) — Ch.4
- [x] Faculty contract + lifecycle + envelope + acceptance tests — Ch.1–4
- [ ] Architecture Agent can implement without inventing (pending REVIEW)
- [ ] World-State wiring (Ch.3 §3.2 copy step) implemented — PENDING
- [ ] Unified fidelity flags on PerceptionResult (Ch.4 §4.3, beyond Chrome rail) — PENDING
- [ ] Audit can mark COMPLETE
