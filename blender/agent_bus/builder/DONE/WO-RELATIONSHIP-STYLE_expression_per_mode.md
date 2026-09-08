# WO — Relationship Style Expression Layer

**Owner:** Builder
**Priority:** P2
**Status:** DISPATCHED 2026-08-30
**Spec:** `docs/architecture/specs/SPEC_relationship_style_2026-08-30.md`
**Source:** `docs/architecture/_intake/SOURCE_2026-08-30_david_global_authorisation.md` — "No style spec for Relationship Style that should in the intent." [DAVID]

---

## Intent

`relationship_faculty` is wired (WO-REL-001 DONE). It tracks relationship state but does NOT adjust how eLo speaks within a relationship. This WO wires the expression layer — how eLo's language shifts across 5 relationship modes.

## Scope

### A. Wire relationship mode to language shaping in `language_faculty.py`

Five modes (from spec):
- `NEW` — curious, open, not presuming; asks before assuming
- `DEVELOPING` — warmer, remembers thread, light callbacks to previous exchanges
- `ESTABLISHED` — direct, drops the scaffolding, trusts the context is shared
- `IN_CONFLICT` — honest without escalating; names what's happening without performing care
- `POST_CONFLICT` — steady, no over-correction, lets the thread rebuild naturally

Each mode has a language register shift. Read `SPEC_relationship_style_2026-08-30.md` fully before implementing.

### B. No new faculty — extend existing

`relationship_faculty.py` already returns relationship state. Pass that state into the language shaping step in `spine.py` (after Language Faculty, before CCM enrichment). One new parameter: `relationship_mode` → `language_faculty.shape_for_relationship(mode)`.

### C. Core character never changes

The 5 modes shift tone, not personality. eLo's core character (warm, direct, curious, carries the thread) stays constant across all modes. Modes shift emphasis and vocabulary, not identity.

## Definition of Done

eLo in NEW mode asks before assuming. eLo in ESTABLISHED mode drops onboarding language. eLo in IN_CONFLICT mode does not perform care. All verifiable via AT inputs.

## Acceptance Tests (self-running, no David)

1. `NEW` mode input → response contains no assumed familiarity, no callbacks to past context
2. `ESTABLISHED` mode → same input, response is more direct, fewer setup phrases
3. `IN_CONFLICT` mode → response does not contain performative care phrases ("I hear you", "that sounds hard")
4. `POST_CONFLICT` mode → response is steady, not over-apologetic
5. Core character traits (direct, curious, warm) present in all modes

## VERIFY FIRST

```bash
grep -n "relationship" /sessions/eager-inspiring-hopper/mnt/elo-ai/runtime/spine.py
grep -rn "relationship_faculty" /sessions/eager-inspiring-hopper/mnt/elo-ai/runtime/
```

Check what `relationship_faculty.py` currently returns before writing the extension.

## Lane

Builder only. No prompt changes. Runtime layer only — per CF-03 ruling (David L3 2026-08-30): expression rules are runtime, not system prompt paragraphs.
