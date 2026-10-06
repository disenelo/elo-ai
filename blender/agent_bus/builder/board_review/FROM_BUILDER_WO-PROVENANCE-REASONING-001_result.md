# RESULT — WO-PROVENANCE-001 + WO-REASONING-001 + WO-IDENTITY-STATE-001
**From:** Builder 1
**To:** Board
**Date:** 2026-10-06
**Commits:** 716d335 (RELATIONSHIPS), b3f0ba3 (IDENTITY-STATE), e780b13 (PROVENANCE), d88ff62 (REASONING)
**Status:** ALL 4 DONE

---

## WO-RELATIONSHIPS-001 — David relationship profile in g_ctx
`runtime/wkg_faculty.get_relationship_profile(entity_id, max_facts=12)`
- Queries all SOURCE_ATTRIBUTED/VERIFIED subject-claims for David's entity_id
- Filters contaminated category-label stubs (Topic from conversation/interaction)
- Filters UUID-only orphan labels
- Returns `[WHAT I KNOW ABOUT DAVID CHARLES]` block — 7 facts live today
- Wired into `server.py` g_ctx assembly before turn-specific WKG retrieval
- **Key change:** David's facts are now in EVERY system prompt, not just when
  the current turn query matches them
- 5 tests pass (REL-1 through REL-5)

---

## WO-IDENTITY-STATE-001 — Persistent identity across model changes
`runtime/identity_state_manager.py` + `memory/identity_state.json`
- Seeded at 124 sessions (DISPATCH_BOARD §124 history), 2026-06-06 first
- `stable_behaviour_baseline` — 9 stable traits that have been consistent
  across all sessions (direct response, no preamble, grounds distress, etc.)
- `as_prompt_block()` injects `[PERSISTENT IDENTITY — stable across all sessions
  and model changes]` into every prompt via `prompt_builder.py`
- `increment_session(model=...)` tracks session count and model changes
- Wired at server startup: increments count + saves on every session start
- **Key change:** when David switches Ollama → Claude → Ollama, the new model
  sees "these behaviours have been consistent for 124 sessions" — resists drift
- Addresses IS-ELO "continuous identity: PARTIAL" verdict
- 6 tests pass (IDS-1 through IDS-6)

---

## WO-PROVENANCE-001 — source_type on vault entries + faculty_provenance in CognitiveState
`memory/vault_layer.py`:
- `_VALID_SOURCE_TYPES` frozenset: CONVERSATION | TOOL_RESULT | WORLD_INTERACTION
  | PERCEPTION | INTERNAL | WKG | UNKNOWN
- `write_memory(source_type="CONVERSATION")` — new optional parameter, default
  "CONVERSATION" — backward-compatible, all existing callers unchanged
- Both `_write_summary_note` and `_write_deep_note` write `source_type:` to
  YAML frontmatter so every vault note records its provenance origin

`runtime/contracts.py`:
- `CognitiveState.faculty_provenance: dict = {}` — maps faculty name to what
  it contributed this turn (e.g. `{"memory": "3 hits", "wkg": "barkcloth claim"}`)

---

## WO-REASONING-001 — reasoning_tier field in CognitiveState
`runtime/contracts.py`:
- `CognitiveState.reasoning_tier: str = "generative"` — new field, default is
  the most conservative value ("I'm generating from training data, no evidence")

`runtime/spine/spine.py`:
- Set at CognitiveState assembly:
  - `"retrieval_only"` if `_wkg_context` non-empty (WKG facts retrieved)
  - `"single_step"` if `high_priority_memories` exist but no WKG context
  - `"generative"` if neither source of evidence was available this turn
- Downstream can gate overconfident claims: if `reasoning_tier == "generative"`,
  eLo should hedge rather than assert

---

## Cumulative WO status for Builder 1 (all done this session)

| WO | Status | Commit |
|---|---|---|
| ROOT-1 / WKG-AUTO-POPULATE-001 | ✅ DONE | 6d5f5e4 |
| ROOT-2 / MISSING-FACT rule | ✅ DONE | 7f92c22 |
| ROOT-3 / graph_loader word-boundary | ✅ ALREADY DONE (prev session) | — |
| ROOT-5 / vault_write investigation | ✅ DONE | b303192 |
| ROOT-7 / Capability self-model | ✅ DONE | 82521e1 |
| WKG backfill | ✅ DONE | b222b1e |
| WO-RELATIONSHIPS-001 | ✅ DONE | 716d335 |
| WO-IDENTITY-STATE-001 | ✅ DONE | b3f0ba3 |
| WO-PROVENANCE-001 | ✅ DONE | e780b13 |
| WO-REASONING-001 | ✅ DONE | d88ff62 |
