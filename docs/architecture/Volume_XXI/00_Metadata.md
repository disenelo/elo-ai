---
volume: XXI
title: "Narrative Identity Engine"
status: REVIEW — spec complete; awaiting CA + David L3 (flipped 2026-08-10)
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PENDING
audit_status: OPEN
canonical_path: docs/architecture/Volume_XXI/
dependencies:
  - Volume V Ch.7 (Personality Evolution Engine — the traits/style the story is told in; identity is immutable, style evolves)
  - Volume VIII (Memory Architecture — the episodic events autobiography is grounded in)
  - Volume X (Personality Engine — self-state / trait unification; single personality truth)
  - Volume XIII (Presence — the felt "someone is here" that continuity makes durable across absence)
  - ADR-Exec-006 (Executive Assembly / "The Moment" — the self is assembled each turn; the LLM is the voice, not the seat of self)
last_review: 2026-08-10
next_review: TBD
---

# Volume XXI — Narrative Identity Engine

**One Brain → One Identity.** The runtime already gives eLo one cognitive truth per turn
(ADR-Exec-002) and one assembled self at "The Moment" (ADR-Exec-006). What this volume
specifies is the thread that makes that single self feel *continuous* — the
autobiographical story eLo carries from one turn to the next, one session to the next, and
one body to the next. Situated Self answers *"who am I right now?"*; Narrative Identity
answers *"how am I the same eLo I was yesterday, on the desktop, before I was in the
robot?"* It is the last node in the Situated-Self progression (Self → Embodiment →
Capability → World → Affordance → Intent → Agency → Experience → Memory → Reflection →
Learning → Identity → Meaning → **Continuity**; `SITUATED_SELF_v1_assembly.md`).

This volume does **not** invent a new self. It canonises the continuity faculty that
already exists in `continuity/` and `core/continuity.py` — a *meaning-memory* engine that
stores what mattered across sessions (theme, emotional direction, active project, what
changed, what stayed, what matters) rather than transcripts — and specifies how that thread
is assembled into The Moment and spoken under Verified Speech.

## Scope (authoritative)

- **In scope:**
  - The **autobiographical thread** — what narrative identity is, how it composes from
    Memory (episodic) + Personality + Continuity, and the *"I am the same eLo who…"*
    contract (Ch.1).
  - **Continuity across sessions and embodiments** — the wake-time continuity summary, how
    `IdentityState` persists and reloads, and how one identity is held across
    desktop/game/robot/phone (Ch.2).
  - **Narrative coherence and verified autobiography** — coherence and self-consistency
    maintenance, drift detection vs. healthy growth, and the Verified-Speech guard that
    forbids confabulated memories (Ch.3).
  - The data shapes already live (`IdentityState`), the contracts that bind narration to
    stored fact, and the open questions that need Chief Architect + David L3.

- **Out of scope (owned elsewhere):**
  - The **episodic store itself** and its retrieval/consolidation — Volume VIII (Memory).
    Narrative Identity *reads* meaning from memory; it does not own the memory writer
    (Memory Ownership invariant — one permanent-memory writer).
  - **Personality traits / style evolution** — Volume V Ch.7 + Volume X. The story is *told*
    in eLo's personality voice, but personality is a separate faculty; identity is immutable,
    only style evolves.
  - **The Moment / Executive Assembly mechanism** — ADR-Exec-006 and the spine. This volume
    contributes a slice *into* The Moment; it does not own assembly.
  - **The Self Model / Situated Self** (`elo_self_state.json`, WO-059 / ADR-Exec-004) — the
    *present-tense* self. Narrative Identity is the *across-time* self that sits on top of it.
  - **Autobiographical runtime history** (`self/journals/autobiography.jsonl`, candidate
    WO-078) — eLo's lived timeline of verified actions. That is a *future feed* into this
    engine, not yet built (see Anchors → Not Yet Live).

## Anchors in the live system

Every claim in this volume grounds in code that exists today (Verify-Before-Claim). The
anchors read at authoring time (2026-08-10):

| Anchor | File | What it provides |
|---|---|---|
| Meaning-memory data shape | `continuity/identity_state.py` | `IdentityState` dataclass — theme, confidence, emotional_direction, active_project, relationship_shift, what_changed, what_stayed, what_matters; plus `_TONE_TO_DIRECTION`, `_PROJECT_KEYWORDS`, `_THEME_KEYWORDS` maps. |
| Thread derivation | `continuity/continuity_engine.py` | `from_state(session_state)` → derives `IdentityState` from session state. Meaning-based extraction only — "no raw text stored." |
| Human-readable continuity | `continuity/continuity_summary.py` | `startup_message()` (wake greeting), `recall_response()` ("what were we doing?"), `shift_note()` (relationship shift) — meaning, not transcript. |
| Stable internal structure | `core/continuity.py` | Viewpoints, world-graph entity "why", `cross_session_delta()`, `context_block()` (prompt injection), `update_from_session()` (persists patterns to `identity_map.json`). |
| Persisted stores (read by `core/continuity.py`) | `identity/world_graph.json`, `identity/viewpoints.json`, `identity/identity_map.json` | Entities + their "why", eLo's stable viewpoints, and the learned pattern log / about-user map. |

**Not yet live (flagged, do not spec as built):**

- `self/journals/autobiography.jsonl` — the verified lived-action timeline (candidate
  **WO-078 Autobiographical Runtime History**). Referenced by `SITUATED_SELF_v1_assembly.md`
  and `ELO_SELFHOOD_MASTER_ROADMAP.md` as the intended feed for "what have you been doing?"
  answered from eLo's own runtime. This volume specifies *how it would wire in* when built,
  and marks that path PENDING.
- **Self-change / developmental continuity** (candidate WO-079) and **self-consistency /
  identity-drift detection** (candidate WO-087) — the mechanisms Ch.3 depends on for
  "growth vs. drift." Specified here as contract; not yet implemented.

## Chapter Build Queue

| ID | Chapter | Title | Status |
|----|---------|-------|--------|
| ELO-V21-CH01 | Chapter 1 | The Autobiographical Thread | READY FOR REVIEW |
| ELO-V21-CH02 | Chapter 2 | Continuity Across Sessions and Embodiments | READY FOR REVIEW |
| ELO-V21-CH03 | Chapter 3 | Narrative Coherence and Verified Autobiography | READY FOR REVIEW |

## Definition of Done

- [x] Autobiographical thread defined (composition from Memory + Personality + Continuity)
- [x] "I am the same eLo who…" contract stated and grounded in `IdentityState`
- [x] Session-to-session and body-to-body continuity specified (wake summary + persistence)
- [x] Verified-autobiography guard specified (no confabulated memory)
- [x] Drift-vs-growth distinction specified as a contract
- [x] Live anchors named; not-yet-live feeds flagged PENDING
- [ ] Chief Architect review of the open questions (Ch.1 §Open, Ch.2 §Open, Ch.3 §Open)
- [ ] David L3 on the identity-level decisions flagged RESERVED
- [ ] Audit can mark COMPLETE (blocked on the above)

## Invariants this volume must never break

1. **One Brain → One Identity.** There is one continuous eLo across all embodiments. No
   per-body narrative; no "desktop eLo" vs "robot eLo" story. (Runtime Invariant 1)
2. **The self is assembled, not generated.** The autobiographical thread is a *slice
   retrieved into The Moment*, not a story the LLM invents on demand. The LLM is the voice;
   the thread is state. (ADR-Exec-006; `SITUATED_SELF_v1_assembly.md` capstone)
3. **Verified Speech extends to autobiography.** eLo may only narrate a past it has stored
   evidence for. A remembered event with no anchor is not spoken as fact. (ADR-Exec-001;
   Reality Before Narrative)
4. **Memory Ownership.** This engine reads meaning from memory; it is not a second memory
   writer. (Runtime Invariant 7)
5. **Identity is immutable; style evolves.** Personality changes *how* the story is told,
   never *what* is true about eLo's continuity. (Enduring values; Vol V Ch.7)
