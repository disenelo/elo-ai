# Phase 02 — Handover

**To:** Phase 2.5 / Phase 3 engineers (Claude or human)
**From:** Phase 2 (Cognitive Infrastructure)
**Date:** 2026-07-10
**Freeze status:** CONDITIONAL ⚠️ — exceptions in 10_freeze.md

---

## What Phase 2 Built

eLo's Attention Faculty now observes four registered cognitive streams (conversation, vision, memory, system), detects concept resonance between them, and produces a structured `AttentionSnapshot` that the Executive reads as ambient context. The Executive is not modified — it reads the snapshot as part of `g_ctx`.

Before Phase 2: eLo could only respond to what the user said directly.
After Phase 2: eLo's context includes what it's observing across its cognitive streams.

---

## Files Changed

| File | Status | What Changed |
|---|---|---|
| `tools/connection_surface.py` | Modified | Complete Phase 2 rewrite — AttentionSnapshot, StreamDefinition, ring buffer, multi-signal confidence (4 signals), hybrid cooldown, session references, concept clusters from JSON |
| `tools/vision_loop.py` | Modified | `description` field added to vision output and `blender_state.json["vision"]` |
| `config/concept_clusters.json` | New | 83 keyword→cluster mappings, 6 clusters: embodiment, creation, recall, synthesis, presence, universe |
| `server.py` | Modified | Connection Surface wired at ~line 800 in g_ctx assembly block (try/except, silent) |

---

## Runtime Interfaces (What Phase 2.5 and Phase 3 Consume)

```python
from tools.connection_surface import get_observation, register_stream, AttentionSnapshot

# get_observation() → AttentionSnapshot | None
# Call from server.py. Returns None if: cooldown not elapsed, confidence below
# ELO_CS_MIN_CONF (default 0.35), or no resonance found.
# Thread-safe via internal _lock.

# register_stream(name, fn, **kwargs) → None
# Registers a new cognitive stream.
# fn: Callable[[], set[str]] — returns tokens to observe
# Streams registered at module load in default _register_defaults().
# Can be called at any time to add new streams.

# AttentionSnapshot fields available for Phase 3:
#   session_reference: str | None  — "YYYY-MM-DD" from journal filename
#   memory_reference:  str | None  — RESERVED (always None in Phase 2)
#   novelty:           float       — 1.0 = first time, decays with repetition
#   concept_path:      list | None — RESERVED for Phase 3 graph traversal
```

---

## What Phase 2.5 Must Not Break

1. `AttentionSnapshot.__str__()` → `"[ATTENTION: {suggested_context}]"` — server.py injects via `str()`
2. `get_observation()` returns `AttentionSnapshot | None` — None is valid and handled silently
3. The try/except wrapper in server.py must not be changed to a hard fail
4. `blender_state.json["vision"]["description"]` — written by vision_loop.py; if removed, vision stream loses vocabulary
5. `config/concept_clusters.json` — if deleted, fallback to inline clusters is automatic

## What Phase 3 Must Not Break

Everything in Phase 2.5's "must not break" list, plus:
- `_to_concepts()` internal may change (keyword→cluster → graph traversal) but the output type must remain `set[str]`
- `_score_pair()` internal may change but must still return `(str, float) | None`
- `register_stream()` API must not change signature

---

## Known Issues

| Issue | Severity | Phase |
|---|---|---|
| No formal unit tests yet | Medium | Phase 2.5 |
| Cooldown defaults unvalidated | Low | Phase 2.5 |
| Vision vocabulary thin for non-creative apps | Low | Expected; Phase 3 adds richer tokenisation |
| `_note` key in concept_clusters.json maps to None | Cosmetic | No fix needed |

---

## Gotchas (Read These)

**Thread safety:** `_call_count`, `_last_fired`, and `_last_fired_ts` are all inside `with _lock:`. Do not add state outside the lock without thought.

**Cooldown is both calls AND time.** Both `ELO_CS_COOLDOWN` call count AND `ELO_CS_COOLDOWN_SEC` seconds must elapse. Either alone is not enough.

**g_ctx injection fails silently.** If connection_surface.py raises anything at all, the exception is swallowed. If you're not seeing observations, add a print inside the except block temporarily.

**Vision description is 5 words max.** The prompt asks for it. The model may not always comply. `_to_concepts()` handles None/empty gracefully.

**Session references come from filenames.** `_parse_session_ref()` parses the date from the journal entry filename. It reads the directory listing — it does not read file contents. If journal files don't have date-prefixed names, `session_reference` will always be None.

**`AttentionObservation` alias must remain.** Some older code may reference the original name. The alias is a one-liner but it's part of the frozen interface.

---

## Phase 2.5 Entry Point

Phase 2.5 starts here:
1. Read `engineering/Phase_025_CognitiveValidation/`
2. Write unit tests for Phase 2 components (Exception 1 resolution)
3. Run all 5 validation protocols
4. Update `Phase_02/10_freeze.md` with final freeze decision

Phase 3 does not begin until Phase 2.5 is FROZEN.
