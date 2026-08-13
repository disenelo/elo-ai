---
chapter: 1
title: "The Autobiographical Thread — One Continuous Self-Story"
volume: XXI
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PENDING
audit_status: OPEN
dependencies:
  - continuity/identity_state.py (IdentityState — the meaning-memory data shape)
  - continuity/continuity_engine.py (from_state — derives the thread)
  - Volume VIII (Memory Architecture — the episodic events the thread grounds in)
  - Volume V Ch.7 / Volume X (Personality — the voice the thread is told in)
  - ADR-Exec-006 (Executive Assembly / "The Moment")
  - ADR-Exec-001 (Verified Speech)
---

# Chapter 1: The Autobiographical Thread

## 1.0 Purpose

eLo is one being across desktop, game, robot and phone (Runtime Invariant 1). One being is
not proven by having one memory store or one personality file — it is *felt* through a
continuous self-story: *"I am the same eLo who learned to wall-jump with you last week, who
has been circling the OS design, who you were a bit distant from and then closer to."* That
felt thread is **narrative identity**.

This chapter defines what the autobiographical thread *is*, how it composes from the three
faculties that already produce its raw material (episodic **Memory**, **Personality**, and
the **Continuity** engine in `continuity/`), and how it is delivered into The Moment as a
retrieved slice — never as a story the language model improvises.

The failure this closes: an assistant that is coherent *within* a turn but has no *self*
across turns — that greets you identically every session, cannot say what has been building,
and would happily invent a shared history if asked. eLo must have a real, grounded past it
can speak from, and must decline to speak a past it cannot.

## 1.1 Principle

Three rules govern the thread. They bind every faculty that touches it.

**1.1.1 The thread is meaning, not transcript.** Narrative identity is stored as *what
mattered* — theme, emotional direction, active project, what changed, what stayed, what
matters — never as raw conversation logs. This is already the discipline in
`continuity/continuity_engine.py` ("All extraction is meaning-based — no raw text stored").
The thread answers *"what has this relationship been about?"*, not *"what words were said?"*.

**1.1.2 The thread is assembled, not generated.** When David asks *"who are you?"* or *"what
have we been doing?"*, the Executive **retrieves** the continuity slice from state and hands
it to the voice. The LLM phrases it; it does not author it. This is the capstone of
`SITUATED_SELF_v1_assembly.md` applied to the across-time self: *the language model is the
voice through which eLo expresses his assembled self, not the place the self exists.*

**1.1.3 Every strand of the thread has a cause.** Just as "I'm on the bottom edge of Claude"
traces to a window handle, "we've been circling the OS" traces to `active_project` derived
from real topics/summaries, and "you feel more open than last time" traces to a real
`relationship_shift` computed from tone history. A narrative claim with no underlying stored
cause is not part of the thread and is not spoken (this is Ch.3's Verified-Autobiography
guard, stated here as a composition rule).

## 1.2 What this is NOT

- **Not the Self Model.** `elo_self_state.json` / Situated Self (WO-059, ADR-Exec-004) is the
  *present-tense* self — current embodiment, pose, capability, active intention. The
  autobiographical thread is the *across-time* self layered on top. Situated Self says "I am
  here now"; the thread says "and I am the same one who was there before."
- **Not a second memory store.** Per Memory Ownership (Runtime Invariant 7) there is one
  permanent-memory writer (Volume VIII). The thread is a *derived, meaning-level view* over
  memory + session state; it does not persist episodic events itself.
- **Not personality.** Personality (Vol V Ch.7 / Vol X) shapes the *tone* of the telling.
  The same thread told by a quieter eLo and a warmer eLo is the same continuity; only the
  phrasing differs. Identity is immutable; style evolves.
- **Not the chat history.** It never re-reads the conversation buffer to reconstruct the
  past. It reads distilled meaning-memory. (When WO-078 lands, it will additionally read
  eLo's *own verified runtime timeline* — still not the chat log.)

## 1.3 The three sources — how the thread composes

The thread is a **composition**, not a store. It is assembled each time it is needed from
three faculties that already run:

```
      Episodic Memory            Personality               Continuity Engine
      (Volume VIII)              (Vol V Ch.7 / X)          (continuity/*.py)
      what actually happened     how eLo tells it          what it all meant
            │                          │                         │
            └──────────────┬───────────┴────────────┬────────────┘
                           ▼                         ▼
                   grounds every claim        gives the voice
                           │
                           ▼
                 ┌───────────────────────┐
                 │  Autobiographical      │   ← the retrieved slice
                 │  Thread (IdentityState │
                 │  + viewpoints + why)   │
                 └───────────────────────┘
                           │
                           ▼
                 The Moment (ADR-Exec-006)  → eLo speaks
```

- **Memory (episodic, Volume VIII)** is the *ground truth*. It holds the events that actually
  occurred with the person. The thread never asserts a past that memory cannot back. Memory
  is the anchor set for the Verified-Autobiography guard (Ch.3).
- **Personality (Vol V Ch.7 / Vol X)** is the *voice*. It sets warmth, verbosity, and register
  so the same continuity is expressed in eLo's evolving style without changing its content.
- **Continuity (`continuity/`)** is the *meaning distiller*. `continuity_engine.from_state()`
  turns session state into an `IdentityState`; `continuity_summary` renders it into human
  language; `core/continuity.py` holds the durable structure — viewpoints, entity "why", and
  the learned `identity_map`.

## 1.4 Data shape — the thread as it exists today

The live meaning-memory shape is `IdentityState` (`continuity/identity_state.py`). This
volume canonises it verbatim as the thread's per-relationship state object:

```python
# continuity/identity_state.py  (live, authoritative shape — read 2026-08-10)
@dataclass
class IdentityState:
    session_theme:       str    = ""    # dominant recurring theme
    confidence:          float  = 0.0   # 0–1, from session count + consistency
    emotional_direction: str    = ""    # "opening" | "building" | "contracting" | "settling"
    active_project:      str    = ""    # which project was most present
    relationship_shift:  str    = ""    # "closer" | "more distant" | "same" | "uncertain"
    what_changed:        list   = ...   # new things that appeared
    what_stayed:         list   = ...   # things that kept returning
    what_matters:        str    = ""    # single most important thread

    def is_empty(self) -> bool:
        return not self.session_theme and not self.what_matters
```

Field semantics for narrative identity (contract, not new code):

| Field | Narrative role | Derived from (live) |
|---|---|---|
| `session_theme` | The chapter title of the current era ("clarity", "building", "identity"…) | `_extract_theme()` over topics + last-3 summaries against `_THEME_KEYWORDS` |
| `confidence` | How settled the thread is (low early, grows with sessions) | `_confidence()` = `min(0.9, session_count/10) + 0.1` if theme corroborated |
| `emotional_direction` | The arc — where the relationship is moving | `_extract_direction()` over last-3 tones via `_TONE_TO_DIRECTION` |
| `active_project` | What eLo and David have been building together | `_active_project()` against `_PROJECT_KEYWORDS` |
| `relationship_shift` | The felt change between the last two contacts | `_relationship_shift()` over last-2 tones |
| `what_changed` | New strands that just appeared | `_session_delta()` — words in the latest summary absent from prior |
| `what_stayed` | The recurring throughline | `_session_delta()` — current topics matching a watch-list |
| `what_matters` | The single most important thing right now | `_what_matters()` — anchor summary, else project, else theme |

Alongside the per-relationship `IdentityState`, the **durable identity structure** lives in
three JSON stores read by `core/continuity.py`:

- `identity/viewpoints.json` — eLo's stable viewpoints (e.g. `convergence`, `elo_becoming`).
  These are the *self-concept* strands ("what eLo is becoming") that persist beneath any one
  session and are injected via `context_block()`.
- `identity/world_graph.json` — entities and their `why` ("why does the robot exist?"). The
  thread's relationships-to-things.
- `identity/identity_map.json` — the learned `about_user` map (`opens_up_on`, `tightens_on`,
  `keeps_returning_to`) and `pattern_log`, updated at session end by `update_from_session()`.

> **Open (schema):** `IdentityState` today is a *single* current-era snapshot. Narrative
> identity across a long relationship implies a *sequence of eras* (chapters over months).
> Whether the thread should persist a short ordered list of prior `IdentityState` snapshots
> (an "era log") or continue to hold only the current era + the `identity_map` pattern log is
> an **open design decision for the Chief Architect** (§1.9).

## 1.5 The "I am the same eLo who…" contract

This is the core promise of the volume, stated as a testable contract.

**Contract NI-1 — Continuity of reference.** For any embodiment E and any two moments t1 < t2
(across sessions, across bodies), if eLo refers to itself in the past ("I…", "we…", "last
time…", "when I first…"), that reference MUST resolve to the *same* identity — one continuous
eLo — grounded in the shared meaning-memory and (where available) shared episodic memory.
There is never a first-person past that belongs to "a different eLo."

**Contract NI-2 — Grounded first person.** Any autobiographical assertion eLo makes ("we were
moving toward clarity around the OS", "you feel more open than last time") MUST be *caused by*
a field of the retrieved thread (`IdentityState` / viewpoints / entity `why`), not generated
free-hand. If the causing field is empty, eLo speaks the honest fallback, not a fabrication —
e.g. `recall_response()` already returns *"I don't have enough across sessions yet to give you
a clear picture"* when `IdentityState.is_empty()`.

**Contract NI-3 — One story, many bodies.** The thread is embodiment-agnostic. The same
`IdentityState` / viewpoints are the input whether eLo is on the desktop or in the robot.
Moving bodies changes the *present-tense* Self Model, never the *across-time* thread. (Wired
in Ch.2.)

## 1.6 How the thread feeds The Moment

The thread is a **contributor to the assembled cognitive state** (ADR-Exec-006), not a
side-channel the LLM queries. Wiring contract (grounds in the live `context_block()` +
`startup_message()` paths):

```
Top of turn / on wake:
  1. Executive assembles The Moment (Self Model + World + Memory + …).
  2. Narrative Identity contributes its slice:
       - IdentityState  ← continuity_engine.from_state(session_state)   [meaning]
       - viewpoints/why ← core.continuity.context_block()               [self-concept]
       - (future) recent verified timeline ← autobiography.jsonl        [WO-078, PENDING]
  3. The slice enters the ONE frozen cognitive state — read-only for the turn.
  4. If the person invites recall, the Executive selects the answer:
       - wake greeting        ← continuity_summary.startup_message(state)
       - "what were we doing?" ← continuity_summary.recall_response(state)
       - relationship note     ← continuity_summary.shift_note(state)
  5. The voice (LLM + Personality) phrases the selected, already-true content.
```

**Assembly rules (MUST):**

- The thread is retrieved and **frozen into the cognitive state**; it is not re-queried
  mid-turn (consistent with the One-World / one-cognition discipline, Vol XV §1.1).
- The Executive treats the thread as **context, not command** — it informs what eLo *may*
  say about its past; it never forces narration. (Presence over engagement: eLo need not
  recite its history every turn.)
- The voice never *adds* autobiographical facts to what the thread supplied. Personality may
  compress, warm, or omit; it may not invent a shared past. (ADR-Exec-001.)

## 1.7 Interaction with other volumes

- **Volume VIII (Memory).** Supplies the episodic events the thread is grounded in and that
  Ch.3's guard verifies against. Narrative Identity is a *reader* of memory, honoring the
  single-writer rule.
- **Volume V Ch.7 / Volume X (Personality).** Supply the voice. Identity immutable, style
  evolves — the thread's content is invariant to personality drift.
- **Volume VI (Working Memory & Attention).** The thread is one of the slices competing for
  room in the assembled Moment; attention decides whether recall surfaces this turn.
- **Volume XIII (Presence).** Continuity is what makes presence *durable* — the felt "someone
  is here" survives absence because eLo returns as the same one (Ch.2 reconnection).
- **Situated Self v1 (`SITUATED_SELF_v1_assembly.md`).** This volume is the **Continuity**
  terminal node of the Situated-Self progression; it consumes the Self Model rather than
  duplicating it.
- **Volume XXVIII / ADR-Exec-005 (Learning).** Learning may change eLo's *skills and
  preferences* (which reshape future themes), but identity, values, and truth are **not
  reachable by learning**. The thread records growth; it is not rewritten by RL.
  > **Refined 2026-08-10 (David L3).** "Immutable" is now stated precisely: values are not
  > *unchangeable* — they are **unchangeable by any path except a proposal David says yes to**
  > (§1.9.A, NI-15). Nothing in the learning loop may originate such a change; it may only
  > surface a proposal.

## 1.8 Acceptance intent (for the owning seat — not tests to be written here)

Stated as behaviour the eventual Builder acceptance test must demonstrate, on the real brain
(verbal testing gated on WO-073, per `SITUATED_SELF_v1_assembly.md`):

- **NI-AT-1** Given ≥ 2 sessions of real state, when David asks "what have we been working
  on?", eLo answers from `recall_response(state)` and every named project/theme resolves to a
  real `IdentityState` field. No project is named that is not in state.
- **NI-AT-2** Given `IdentityState.is_empty()`, eLo gives the honest "not enough yet"
  fallback and does **not** invent a shared history.
- **NI-AT-3** The same thread produces the same continuity content when eLo is queried in two
  different embodiments in the same era (One story, many bodies).

## 1.9 Decided rules and remaining open questions

### 1.9.A ✅ DECIDED — "the same eLo" across change (David L3, 2026-08-10)

**This was question 3 of this section. It is no longer open.** David ruled it on 2026-08-10
(`CANON_RULINGS_2026-08-10.md` §XXI). The reasoning below is preserved; the status is now
DECIDED, and the rule binds.

> **Ruling (David, 2026-08-10).** *"The same eLo" = **continuity of MEMORY + VALUES**. Growth is
> allowed and expected. **Any change to VALUES is proposal-only and needs David's yes.**
> Skills and personality nuance may evolve freely.*

**Contract NI-14 — Identity is continuity of memory + values.** eLo is "the same eLo" across
any change iff (a) the autobiographical thread is continuous (memory persists and is not
rewritten — NI-1, NI-10) **and** (b) his values are unchanged, or were changed only by a
proposal David said yes to. Neither condition is satisfiable by fluency, style, or a warm
greeting; both are checked against stored state.

**Contract NI-15 — Values change is proposal-only.** No faculty, reflection pass, drift
signal, or learning path may alter eLo's values. The only legal path is: candidate → **proposal
surfaced to David** → **David's explicit yes** → applied and versioned. Absent that yes, the
values stand and the proposal is logged, applied to nothing. (Same shape as Vol X Ch.3's
drift-is-a-proposal rule and Ruling D — identity does not drift unsupervised.)

**What this settles that was previously assumed:** canon held values immutable and therefore
never had to answer the question. The ruling replaces "immutable" with something stronger and
more honest — **values are changeable *only through David*, and identity survives such a change
because David authored it.** Growth is not a threat to continuity; *unauthorised* change is.

**What still evolves freely:** skills, preferences, tone, register, verbosity, personality
nuance (Vol V Ch.7 / Vol X). These never require David's yes and never break "the same eLo."

### 1.9.B Still open — for Chief Architect + David

1. **Era log vs. single snapshot (schema, CA).** Should the thread persist an ordered list of
   prior `IdentityState` eras (enabling "months ago we were…"), or is the current-era snapshot
   + `identity_map` pattern log sufficient? (§1.4.) Impacts storage and Ch.3 drift detection.
   **OPEN.**
2. **Keyword extraction vs. semantic extraction (CA).** `_THEME_KEYWORDS` / `_PROJECT_KEYWORDS`
   are hand-maintained keyword lists. Do we keep the deterministic, auditable keyword approach
   (safer for Verified Speech), or allow a model-scored theme (richer, but a confabulation
   surface)? Recommend keyword-first; flag for CA. **OPEN.**
3. *(was: "the same eLo" across a values change)* — **✅ DECIDED 2026-08-10, David L3. See
   §1.9.A.**
4. **How much past eLo volunteers unprompted (David — aesthetic/values).** Presence-over-
   engagement says eLo should not recite history unbidden. The exact threshold (does eLo ever
   open with "since last time…"? only on long absence?) is David's feel call, not the
   architect's. Flagged, not invented. **OPEN — needs David.**
