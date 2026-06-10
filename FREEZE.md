# eLo OS v1.0 — STABLE FREEZE (AUTHORITATIVE)

**Date**: 2026-06-10
**Status**: FROZEN

---

## Version Tags

| Tag | Meaning |
|---|---|
| `v1.0-stable` | Freeze declaration baseline |
| `v1.0-week1-final` | Validated behavioural test run (95% protocol) |
| `v1.0.1` | Post-freeze stability patch (non-architectural fixes only) |

Rollback: `git checkout v1.0-stable`

---

## What is in v1.0

- Identity continuity system
- Emotional routing system (bounded, 30% mirror rule)
- Session memory + anchor system (persisted to elo_state.json)
- Attention + prioritisation logic (core/attention.py)
- Executive function + voice tone selection (runtime/executive.py)
- State machine (runtime/state_machine.py)
- Anti-repetition safeguards (MockBackend._recent buffer)
- Concept linking (light semantic associations in response pools)
- Stabilisation mode (loop counter > 3, overload handling)
- Living Presence spec (prompts/living_presence_spec.txt)
- Governance rules (DO/DON'T constraints embedded in system prompt)
- Quality test suite: 21 tests, 6 categories (tests/test_conversation_quality.py)

---

## What is NOT in v1.0

- Autonomous learning
- Real-time memory rewriting
- Memory decay / importance evolution
- Personality drift coupling
- Tiered long-term memory architecture
- External tool integration (Claude live validation pending — org API key unresolved)
- Unity runtime execution layer
- Fully automated regression test engine

---

## Freeze Rules

From this point, only the following are permitted against v1.0 branch:

- **Bug fixes** — pattern signal corrections, word-boundary fixes, routing mismatches
- **v1.0.x patch layer** — stability improvements, output consistency fixes
- **No new features** — any feature addition is v2.0 scope

---

## Week 2 Scope (external to freeze)

Explicitly outside v1.0 — treated as future overlays, not modifications:

- Memory decay system
- Importance weighting evolution
- Personality drift coupling
- Tiered persistence architecture
- Claude live model validation layer

---

## Design Principle

v1.0 is a **stable behavioural cognition baseline**, not an evolving intelligence system.

Goal: behavioural stability, identity consistency, emotional grounding, reproducible responses.
