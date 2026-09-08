# WO-RELATIONSHIP-STYLE — Relationship Style Runtime Wiring
**From:** Board / Lead Architect  
**Date:** 2026-08-31  
**Priority:** P2  
**Authority:** David L3 global ruling 2026-08-30 + SPEC_relationship_style_2026-08-30.md  
**RTR:** Relationship mode → expression path  
**Spec:** `docs/architecture/specs/SPEC_relationship_style_2026-08-30.md` (read fully before starting)  
**Depends on:** WO-REL-001 ✅ DONE (relationship_faculty wired), WO-SC-NEW-001 ✅ DONE (storytelling_style field)  
**Lane:** Builder (Python). No executive.py. No contracts.py.

---

## Problem

`relationship_faculty.py` is wired and computes a relationship mode per turn. That mode is NOT used downstream in the prompt builder or the response gate. eLo's expression style does not shift across the five relationship modes (NEW / DEVELOPING / ESTABLISHED / DEEP / CREATIVE_PARTNER) despite the spec defining exact language register changes for each.

## What to build

### 1 — Read relationship mode from CognitiveState

`relationship_faculty` already writes its output to `CognitiveState`. Confirm which field (inspect `relationship_faculty.py` — if it writes `relationship_mode` or similar, use that directly).

### 2 — Wire mode into prompt builder

In `runtime/prompt_builder.py`, read `cognitive_state.relationship_mode` (or equivalent field). Map each mode to its language register instruction from the spec:

| Mode | Prompt injection key |
|---|---|
| NEW | "NEW mode: shorter turns, genuine open questions, do not claim shared history" |
| DEVELOPING | "DEVELOPING mode: begin threading references, humour may surface, can disagree without walkback" |
| ESTABLISHED | "ESTABLISHED mode: shorthand, anticipatory, casual and warm, banter register open" |
| DEEP | "DEEP mode: existential questions welcome, David's inner state is fair territory, full honesty" |
| CREATIVE_PARTNER | "CREATIVE mode: David leads direction, eLo produces without hedging, co-builds not assists" |

These are NOT new system prompt paragraphs — they are per-turn register injections in the [RELATIONSHIP CONTEXT] block already present in server.py. If no such block exists, add it adjacent to [STORYTELLING FRAME].

### 3 — Do not override CHARACTER DNA or FREEZE_V1_LOCK content

The relationship mode adjusts register. It does NOT change CHARACTER DNA. It does NOT modify `living_presence_spec.txt`. It does NOT touch executive.py.

### Acceptance tests

1. `relationship_mode` field is read from CognitiveState without error in each of the 5 mode states
2. Prompt builder includes a [RELATIONSHIP CONTEXT] block per turn containing the correct mode instruction
3. Switching from NEW to ESTABLISHED in CognitiveState changes the injected register instruction
4. [RELATIONSHIP CONTEXT] block is present in system prompt output (verify via prompt_builder unit test)
5. No executive.py changes. No contracts.py changes. No living_presence_spec.txt changes.
