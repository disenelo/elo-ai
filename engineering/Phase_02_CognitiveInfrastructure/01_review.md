# Phase 02 — Architecture Review

**Phase:** Cognitive Infrastructure
**Reviewer:** Claude Sonnet 4.6 / David Charles
**Date:** 2026-07-10
**Decision:** PROCEED

---

## Phase Objective

Phase 2 makes faculties speak to each other. One Brain in architecture becomes One Brain in operation. The key deliverable is the Connection Surface — a subsystem of the Attention Faculty that observes registered cognitive streams, finds concept resonance, and produces a structured `AttentionSnapshot` that the Executive reads as additional context.

---

## Architecture Constants Check

| Constant | Status | Notes |
|---|---|---|
| One Brain | ✅ COMPLIANT | Connection Surface is a subsystem of Attention — not a new faculty. No second cognitive centre created. |
| One Executive | ✅ COMPLIANT | `runtime/executive.py` was not modified. Executive reads `g_ctx` — the injection point is server.py, not the Executive itself. |
| Faculties Observe | ✅ COMPLIANT | `get_observation()` returns `AttentionSnapshot | None`. It never decides, acts, or routes. |
| FREEZE_V1_LOCK | ✅ COMPLIANT | `runtime/executive.py` and `prompts/` were not touched. |
| Silence is Valid | ✅ COMPLIANT | `get_observation()` returns `None` when cooldown hasn't elapsed, confidence is below threshold, or no resonance is found. None is handled silently in server.py. |
| Evidence Gates | ⚠️ RISK | Phase 2 was implemented before a formal validation session. Phase 2.5 (Cognitive Validation) exists specifically to retrospectively validate this phase before Phase 3 begins. This is the primary risk. |

---

## Existing System Impact

| File | Impact | Risk |
|---|---|---|
| `server.py` | Connection Surface wired at ~line 800 in the g_ctx assembly block | Low — injection is try/except wrapped; failure is silent |
| `tools/vision_loop.py` | `description` field added to vision output and `blender_state.json["vision"]` | Low — new field, backwards compatible |
| `config/concept_clusters.json` | New file loaded by connection_surface.py | Low — fallback to inline clusters if file missing |
| `blender_state.json` | `vision.description` field added | Low — additive change |

**Not touched:**
- `runtime/executive.py`
- `prompts/`
- `main.py`
- `voice/voice_engine.py`
- `ambient/`

---

## Risks

1. **No formal validation session** (PRIMARY) — Phase 2 was fully designed and built before a single long-session test. The ring buffer, pattern detection, multi-signal confidence, and session references were all designed theoretically. Phase 2.5 must validate that they behave as designed in practice. If they don't, Phase 3 would have been built on unvalidated infrastructure.

2. **Vision stream vocabulary** — The vision stream tokenises `app` + `description` (5 words). For apps that aren't creative tools (e.g. system preferences, Finder), the vocabulary is thin. This may reduce resonance quality. Mitigation: concept clusters include common app terms; Phase 3 Semantic World Model adds richer tokenisation.

3. **Concept clusters are flat** — Phase 2's `_to_concepts()` is a flat keyword→cluster lookup. Two streams sharing the cluster `"creation"` because both contain the word "build" will produce an observation — but the word "build" in the context of "Blender rigging" vs. "npm build" are semantically different. Phase 3 Semantic World Model is the designed fix.

4. **`_note` key in concept_clusters.json** — The `_note` field is harmless (it maps to `None` and is never tokenised) but represents a minor inconsistency in the JSON schema. Low risk; no fix needed.

---

## Recommendation

**PROCEED** — Phase 2 is architecturally sound. The Connection Surface correctly implements the Attention Faculty subsystem pattern. The One Brain principle is not violated. The primary risk (no formal validation) is addressed by Phase 2.5 existing as a mandatory gate before Phase 3 implementation begins.

Phase 2 moves to FREEZE after Phase 2.5 validation passes.
