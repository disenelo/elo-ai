# Phase 02 — Gap Analysis

**Phase:** Cognitive Infrastructure
**Date:** 2026-07-10

---

## What Phase 2 Does Not Do (By Design)

These are not gaps to fix — they are intentional boundaries for later phases.

| What's Missing | Planned Phase | Reason Deferred |
|---|---|---|
| Concept graph traversal | Phase 3 | Phase 2 uses flat keyword→cluster; Phase 3 builds traversable semantic families |
| Memory importance weighting | Phase 3 | `memory_importance` field reserved in AttentionSnapshot but not populated |
| Relationship strength weighting | Phase 3 | `relationship_strength` not yet computed |
| `concept_path` traversal | Phase 3 | Field reserved, always `None` in Phase 2 |
| `memory_reference` field | Phase 3 | Field reserved, always `None` in Phase 2 |
| `journal_router.py` / `recent_topics()` | Phase 3 | Session reference parsed from filename only; full journal metadata in Phase 3 |
| Embodiment routing: `get_observation(embodiment="robot")` | Phase 4 | Robot/mobile streams not yet registered |
| Stream health monitoring | Phase 4 | `_health` and `_error_count` tracked but no alerts |

---

## Real Gaps (Things That Should Work Better)

### Gap 1 — Vision stream vocabulary is thin for non-creative apps

**Problem:** When the frontmost app is something like System Preferences, Finder, or Terminal (no creative work), the `description` field carries little signal and `app` maps to no concept cluster. The vision stream contributes near-zero to resonance.

**Resolution:** Phase 2 design — concept clusters include common app terms. This is expected, not broken. Silence from the vision stream when nothing creative is happening is correct behaviour.

**Verdict:** Not a gap. Expected behaviour. Vision silence = correct.

### Gap 2 — `_note` key in concept_clusters.json maps to `None`

**Problem:** `"_note"` is a documentation key in the JSON that the cluster loader includes in the dict. It is never matched (no word tokenises to `"_note"`) but occupies one dict entry.

**Resolution:** Harmless. No fix required. Document as known quirk.

**Verdict:** Cosmetic. No Phase 3 action needed.

### Gap 3 — No formal validation before Phase 3 can begin

**Problem:** The entire Phase 2 system (ring buffer, pattern detection, multi-signal confidence, session references) was designed and implemented without a long-session validation test. If any of these components behave differently in practice than in design, Phase 3 would be built on unvalidated infrastructure.

**Resolution:** Phase 2.5 (Cognitive Validation) is the mandatory gate. Phase 3 implementation does not begin until Phase 2.5 passes all 5 validations.

**Verdict:** Critical. Phase 2.5 resolves this.

### Gap 4 — `ELO_CS_COOLDOWN` and `ELO_CS_COOLDOWN_SEC` defaults are theoretical

**Problem:** The cooldown defaults (5 calls, 30 seconds) were chosen by design reasoning, not by observing actual conversation cadence. In a fast-paced session, 5 calls might be 10 seconds. In a slow session, 30 seconds might not be long enough.

**Resolution:** Phase 2.5 Validation 3 (Silent Behaviour) will reveal if the cooldown is calibrated correctly. Tunable via env vars — no code change needed to adjust.

**Verdict:** Phase 2.5 validates this. Tunable without code change.

---

## What Phase 2 Must NOT Change Going Forward

These are the interfaces that Phase 3 and beyond depend on:

1. `AttentionSnapshot.__str__()` → `"[ATTENTION: ...]"` — server.py uses str() injection
2. `get_observation()` → `AttentionSnapshot | None` — caller interface is frozen
3. `register_stream(name, fn, **kwargs)` — registration API is frozen
4. `AttentionObservation = AttentionSnapshot` — backward-compat alias must remain
5. `g_ctx` injection is try/except wrapped, silent on failure — this must never change to a hard fail
6. `blender_state.json["vision"]["description"]` — written by vision_loop.py, read by connection_surface.py
