# WO-CAP-COG-002 — Result: Language Structure Understanding

**Date:** 2026-09-20
**WO:** WO-CAP-COG-002
**Source:** `docs/architecture/_intake/SOURCE_2026-09-19_eLo_KEY_CAPABILITY_MAP.md §2`
**Seat:** Builder
**Status:** CLOSED — LIVE VERIFIED 17/20 PASS · 3 PARTIAL · 0 FAIL

---

## What was done

Identified and fixed the topic-shift hallucination blocker. Ran multi-turn contextual evidence covering all 20 source §2 language structure categories across two independent sessions (H and V).

### Files changed

| File | Change |
|---|---|
| `runtime/backend_router.py` | TOPIC SHIFT SIGNAL in `_ollama_stream()` — detect explicit topic-change markers, inject directive into `_conditioned_system` |
| `runtime/backend_router.py` | TOPIC SHIFT input rewrite in `_ollama_stream()` — strip shift marker, flag as first-mention topic for 8b model |
| `runtime/backend_router.py` | TOPIC SHIFT SIGNAL in `route_streaming()` — mirrored with `_rt_` prefix |
| `engineering/evidence/CAP/COG/WO-CAP-COG-002_evidence.md` | Full evidence file |

### Root cause fixed

**Topic shift hallucination** — when user said "anyway, what about the NeoPixels," the 8b model invented prior NeoPixel history ("The NeoPixels are still a bit finicky, I've noticed") from cross-session grounding tracker state and also identity-drifted to speak as the robot. Directive alone was insufficient — 8b model ignores directives without input rewrite. Fix: detect topic-shift markers → inject TOPIC SHIFT SIGNAL → also rewrite `_ollama_user_input` to present the new topic as explicitly first-mention (`[new topic — no prior context in this conversation]`).

Original blocker (H9 pre-fix): "The NeoPixels are still a bit finicky, I've noticed. Sometimes they get stuck on a particular color or pattern."
Post-fix (V7): "NeoPixels a great topic, what's next? WS2812, APA102, or Bicolor, you got options."

---

## Source §2 coverage — all 20 categories

| Category | Verdict |
|---|---|
| nouns | ✅ PASS |
| verbs | ✅ PASS |
| adjectives | ✅ PASS |
| adverbs | ✅ PASS |
| subjects | ✅ PASS |
| objects | ✅ PASS |
| actions | ✅ PASS |
| states | ✅ PASS |
| relationships | ✅ PASS |
| tense | ✅ PASS |
| modality | ⚠️ PARTIAL |
| negation | ✅ PASS |
| conditionals | ⚠️ PARTIAL |
| questions | ⚠️ PARTIAL |
| commands | ✅ PASS (WO-CAP-KEY-001 evidence) |
| statements | ✅ PASS |
| references | ✅ PASS — it = arm, not eLo |
| implied subjects | ✅ PASS |
| implied objects | ✅ PASS |
| conversational turns | ✅ PASS |

**17/20 PASS · 3/20 PARTIAL · 0/20 FAIL**

PARTIAL types:
- modality: uncertainty register recognized; both modal options not always engaged substantively
- conditionals: if-then-but structure parsed; response engagement shallow on specifics
- questions: recognized as question type; factual retrieval inconsistent (knowledge issue, not structure)

The key §2 example (it = robot arm, not eLo) PASSES in both independent test runs.

---

## Full evidence

`engineering/evidence/CAP/COG/WO-CAP-COG-002_evidence.md`

---

## Status

LIVE VERIFIED. WO-CAP-COG-002: CLOSED.

*Builder · 2026-09-20*
