---
chapter: 3
title: "Memory Ageing & Retrospection — Time Framing Over the Autobiographical Thread"
volume: XXV
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PENDING
audit_status: OPEN
dependencies:
  - Volume_VIII/01_Memory_Architecture.md §1.4 (the forgetting curve — OWNED there, read here)
  - Volume_XXI/00_Metadata.md + chapters (Narrative Identity — the autobiographical thread; IdentityState)
  - Volume_XXV/01_Time_Perception_and_Circadian_Scheduling.md (TemporalState — now/phase)
  - ADR-Exec-001 / Reality Before Narrative (Verified Speech extends to autobiography)
  - ARCHITECTURAL_PRINCIPLES.md (Memory Ownership — one writer; memory serves meaning, framed in natural time)
---

# Chapter 3: Memory Ageing & Retrospection

## 3.0 Purpose

The forward half of Temporal Cognition (Ch.2) lets eLo lean into the future. This chapter is the
backward half: **temporal reasoning over the past** — how old a memory *feels*, how eLo frames
elapsed time in natural language, and how it looks back across its own autobiographical thread.

Three responsibilities:

1. **Subjective memory age** — turning a stored timestamp into a felt age ("earlier today", "the
   other week", "ages ago"), so recall is framed in natural time, not epoch seconds.
2. **Reading the forgetting curve** — using Vol VIII's memory *strength* to reason about what has
   faded and what has held, **without ever writing or decaying memory itself**.
3. **Retrospection** — deliberate looking-back over the autobiographical thread (Vol XXI):
   "what have we been doing lately", "how far we've come", answered only from verified stored events.

The load-bearing boundary of this chapter: **Vol VIII owns the mechanism of ageing (the decay
curve, consolidation, the memory writer). Volume XXV owns the *temporal framing and reading* of
that ageing.** One is the biology; the other is the sense of time laid over it.

## 3.1 Principle — frame time, never own memory

**3.1.1 Memory Ownership is absolute (Runtime Invariant 7).** There is one permanent-memory
writer. Temporal Cognition is **not** it. This faculty reads memory timestamps and strengths and
produces temporal *interpretation*; it never writes a memory, never adjusts a memory's strength,
never runs the decay. The forgetting curve `strength = f(significance, recurrence, recency,
emotional_weight)` and its decay/reinforcement/floor rules live wholly in Vol VIII §1.4. This
chapter *consumes* strength; it does not compute it. (Check-before-build: extend Vol VIII, never
duplicate its curve.)

**3.1.2 Memory serves meaning, framed in natural time (Invariant 7, second clause).** The reason
this faculty exists is that clause. A raw timestamp is not memory-serving-relationship; "that was
the afternoon we finally got the sit-chain working" is. Temporal Cognition is the engine that turns
`at_ts` into natural-time meaning. It is the *framing* layer the Memory Ownership invariant asks for.

**3.1.3 Verified Speech extends to autobiography (ADR-Exec-001; Vol XXI invariant 3).** eLo may
narrate a past only where it has stored evidence. A remembered event with no anchor is not spoken
as fact. Retrospection is therefore a *retrieval-and-frame* act, never a *generate-a-plausible-past*
act. If the thread has a gap, eLo says it doesn't recall — it never confabulates to fill it.
(Reality Before Narrative; Truth before fluency.)

**3.1.4 Retrospection is asked, not looping.** Like all of Temporal Cognition (Ch.1 §1.1.1), this
faculty runs when the Executive assembles The Moment or when a look-back is requested. It does not
run a background nostalgia loop. Deliberate consolidation-time retrospection is the timed
Consolidation faculty's window (Vol VIII §1.3); this faculty supplies the temporal framing to it,
it does not start its own cycle.

## 3.2 The Retrospection Object

When retrospection is invoked (a look-back question, or The Moment needing a "recently" frame),
Temporal Cognition produces `Retrospection`.

```
Retrospection (frozen, on request):
  # --- the natural-time frame of recall ---
  now_ts:            float                # == TemporalState.now_ts (Ch.1)
  window:            enum { earlier_today, this_week, recent_weeks, long_ago }
  framed_events:     [ FramedMemory ]     # verified events, natural-time framed, strength-ranked

  # --- the shape of the thread over time ---
  thread_arc:        str | null           # "steady progress on canon", from Vol XXI IdentityState
  what_held:         [ str ]              # high-strength / floored memories (Vol VIII §1.4 floor)
  what_faded:        [ str ]              # low-strength noise, acknowledged as fuzzy — never invented
  gaps:              [ { from_ts, to_ts } ]   # unrecalled spans — stated honestly, not filled

  confidence:        float 0.0–1.0

FramedMemory:
  ref:          str            # the anchor in the vault (Vol VIII) — proves it is real
  natural_age:  str            # "earlier today", "a few days back" — the framing (§3.3)
  at_ts:        float
  strength:     float 0.0–1.0  # READ from Vol VIII forgetting curve; NOT computed here
  fidelity:     enum { vivid, clear, faded }   # a function of strength (§3.4), not of age alone
  emotional_weight: float      # READ from Vol VIII emotional memory (indexed by weight, not recency)
```

**Object rules (MUST):**

- Every `FramedMemory` carries a `ref` to a real stored record. No `ref` → not surfaced (Verified
  Speech, §3.1.3). Retrospection can only frame memory that exists.
- `strength` and `emotional_weight` are **read** from Vol VIII, never recomputed. `fidelity` is a
  *presentation* of strength (§3.4), the only new derived field — and it derives from strength, not
  from raw age.
- `gaps` are stated, never filled. If eLo has no record of a span, that span is an explicit gap.
- `what_faded` names *categories* of faded noise ("small scheduling chatter"), acknowledged as
  fuzzy — it never fabricates the faded content to seem complete.

## 3.3 Subjective Memory Age — natural-time framing

The core function of this chapter: `at_ts → natural_age`, computed against `now_ts` (Ch.1
discipline — no independent clock read). Defaults, tunable in the integration window:

```
just now        < 90s
earlier         90s – same part_of_day
earlier today   same calendar day, part_of_day crossed
yesterday       previous calendar day
the other day   2 – 5 days
last week       5 – 14 days
a while back    2 – 8 weeks
ages ago        > 8 weeks
```

**Rules (MUST):**

- Framing is by **calendar/part-of-day boundaries, not raw deltas** — mirroring Ch.1's `overnight`
  logic. "Yesterday" means the calendar day flipped, not "≈24h ago". This is why the framing needs
  `TemporalState.part_of_day`/`weekday`, not just a seconds delta.
- The frame is *meaning offered to the Executive*, which decides whether to voice it. Temporal
  Cognition never itself speaks (it is upstream of speech — Ch.1 §1.6).
- Framing must respect **David's** cadence where it matters — his "the other day" is the only
  "the other day" this system has to get right. Tracked via continuity against his actual
  interaction history, not hardcoded, and not segmented by user type (there is one person —
  re-scoped 2026-08-10). The default table above applies until his cadence is established, and
  anything David states about how he talks about time outranks what continuity inferred
  (`CANON_RULINGS_2026-08-10.md`, XXVI).

## 3.4 Reading the Forgetting Curve — fidelity, not decay

eLo's recall should *feel* like memory: recent and significant things are vivid; old trivial things
are fuzzy. This faculty expresses that by mapping Vol VIII's `strength` to a `fidelity`:

```
fidelity(strength, natural_age):
  vivid   → high strength (significant / recently reinforced / floored)   → recalled in detail
  clear   → moderate strength                                             → recalled in substance
  faded   → low strength                                                   → recalled as a fuzzy gist
```

**Rules (MUST):**

- **Fidelity tracks strength, not age.** A high-significance moment from months ago is `vivid`
  because Vol VIII's curve floored/reinforced it (§1.4: identity and pinned memories do not decay;
  emotional memory indexes by weight, not recency). A trivial thing from this morning may already be
  `faded`. This is the whole point of Vol VIII's weight-not-timestamp rule, surfaced as recall feel.
- **This faculty never decays anything.** If a memory is faded, that is because Vol VIII's curve
  made it so. Temporal Cognition reports the fade; it does not cause it (§3.1.1).
- A `faded` memory is narrated *as* faded ("something about a schema change, I think — the details
  have gone fuzzy") — honest low-fidelity recall, never a confident reconstruction. (Truth before
  fluency: truthful uncertainty beats confident fiction.)
- Identity-level and Significance-pinned memories (Vol VIII §1.4 floor, Vol V Ch.5) are always at
  least `clear` regardless of age — they define the relationship and must not read as faded.

## 3.5 Retrospection Over the Autobiographical Thread (Vol XXI)

Retrospection is where Temporal Cognition meets Narrative Identity. Vol XXI owns the
*autobiographical thread* (the `IdentityState` meaning-memory: theme, emotional_direction,
active_project, what_changed, what_stayed, what_matters). This chapter provides the **temporal
reasoning over that thread** — ordering it in time, framing its ages, and reading its arc.

```
retrospect(query, TemporalState, thread=IdentityState[], memory=VaultRefs) -> Retrospection
  "what have we been doing lately?"  → window=this_week; framed_events from recent verified turns
  "how far have we come?"            → thread_arc from Vol XXI what_changed/what_stayed over time
  "remember when we…?"              → resolve to a ref; frame its natural_age + fidelity; or state a gap
```

**Wiring (MUST):**

- The thread content comes from Vol XXI's `continuity/` anchors (`identity_state.py`,
  `continuity_engine.py`, `continuity_summary.py`) — meaning-memory, "no raw text stored". Temporal
  Cognition *orders and frames* that meaning in time; it does not restate transcripts (there are
  none) and it does not own the thread.
- The verified lived-action timeline `self/journals/autobiography.jsonl` (Vol XXI, candidate
  **WO-078**) is the intended richest feed for "what have you been doing" answered from eLo's own
  runtime. **It is not yet live.** This chapter specifies how retrospection *would* consume it (each
  entry is a `ref`-bearing FramedMemory) and marks that path **PENDING** — until it exists,
  retrospection is grounded in the vault (Vol VIII) + `IdentityState` (Vol XXI) only. (Verify-before-
  claim: do not spec it as built.)
- Retrospection at consolidation time (session close / nightly, Vol VIII §1.3) supplies the timed
  Consolidation faculty with natural-time framing so its "what changed / what should fade" replay is
  temporally coherent. Consolidation still owns the decay and the writes; this faculty frames.

## 3.6 Faculty Contract

```
Faculty:
  name:            TemporalCognitionFaculty (retrospective responsibility)
  version:         1.0.0
  purpose:         Frame stored memory in natural time (subjective age + fidelity) and perform
                   temporal reasoning over the autobiographical thread (retrospection) — reading
                   Vol VIII strength and Vol XXI thread, writing NEITHER.
  contributes_to:  CognitiveState / The Moment (recall framing) + Consolidation (Vol VIII, as framer)
  runs_in:         response-path (framing on assembly / on look-back) + integration-window (frames Consolidation)

Inputs:
  - type: temporal_state        source: Ch.1 TemporalState                       required: true
  - type: memory_refs+strength  source: Memory / forgetting curve (Vol VIII §1.4) required: true
  - type: autobiographical_thread source: continuity IdentityState (Vol XXI)      required: false
  - type: autobiography_timeline source: self/journals/autobiography.jsonl (WO-078) required: false  # PENDING
  - type: significance          source: Significance Engine (Vol V Ch.5 — floor/pin) required: false

Outputs:
  - type: retrospection         destination: Executive / The Moment (recall framing, read-only)
  - type: natural_age_frame     destination: any faculty needing "how long ago" in natural time
  - type: retrospection_context destination: Consolidation (Vol VIII §1.3) — temporal framing only

Dependencies:
  - faculty: TemporalCognition Ch.1 (HARD — now/phase)
  - faculty: MemoryArchitecture (Vol VIII, HARD — supplies refs + strength; owns the curve + writes)
  - faculty: NarrativeIdentity (Vol XXI, soft — supplies the thread; owns it)
  - faculty: SignificanceEngine (Vol V Ch.5, soft — which memories are floored/pinned)

Failure Modes:
  - condition: memory ref missing / unresolvable   fallback: state a gap; NEVER confabulate the memory.
  - condition: autobiography.jsonl not yet built    fallback: retrospect from vault + IdentityState; path PENDING.
  - condition: strength unavailable for a memory     fallback: fidelity=clear (neutral); do not guess decay.
  - condition: asked to change/delete a memory       fallback: refuse — not the writer (Memory Ownership).
  - condition: a gap in the thread                   fallback: report the gap honestly; no plausible fill.
```

## 3.7 Faculty Lifecycle

Universal lifecycle (CONTRACTS.md §3). Notes:

```
INITIALISING → load natural-age threshold table; attach (read-only) to vault + continuity anchors
ACTIVE       → idle; NO self-timer, NO background reminiscing loop (Ch.1 §1.1.1)
PROCESSING   → on assembly/look-back: read TemporalState + memory strength → frame → Retrospection
   └─ ref fault ─► ERROR_RECOVERY → report a gap → continue (never confabulate)
LEARNING/UPDATING → (integration window) tune natural-age thresholds; frame Consolidation replay
STABLE → ACTIVE
```

Writes no memory and proposes no personality delta. Its only `UPDATING` is threshold tuning and
supplying temporal framing to the Consolidation window (which does the actual writing).

## 3.8 Message Envelope Binding

Per CONTRACTS.md §2.

```jsonc
{
  "id": "uuid",
  "sender": "TemporalCognitionFaculty",
  "receiver": "*",
  "priority": "normal",
  "context": {
    "conversation_id": "", "relationship_state": "", "environment_state": "",
    "significance": 0.0,
    "memory_instruction": { "store": false, "priority": "" }   // MUST be false — reads only
  },
  "payload": { "type": "retrospection", "body": { /* Retrospection */ } },
  "confidence": 0.0,
  "expires": "<now_ts + turn_ttl>",   // a recall framing is a per-turn view
  "trace": ["TemporalCognitionFaculty@ts"]
}
```

Binding rules: `sender` MUST be `TemporalCognitionFaculty`; `memory_instruction.store` **MUST be
false** — this is the enforceable expression of Memory Ownership for this faculty (it can never
carry a write instruction); `context.significance` is *read* (set by Vol V Ch.5), never written.

## 3.9 Interaction with other volumes

- **Volume VIII (Memory) — the hard boundary.** Vol VIII owns the forgetting curve, consolidation,
  and the single memory writer. Volume XXV reads `strength`/`emotional_weight`/`ref` and produces
  natural-time framing + fidelity. The clean cut: *Vol VIII decides what is remembered and how
  strongly; Vol XXV decides how that remembering feels in time.* Neither restates the other.
- **Volume XXI (Narrative Identity) — the thread.** Vol XXI owns the autobiographical thread
  (`IdentityState`) and the "I am the same eLo who…" continuity. Volume XXV supplies the temporal
  reasoning *over* that thread (ordering, ageing, arc). Vol XXI's Verified-autobiography guard is
  inherited wholesale (§3.1.3).
- **Volume V Ch.5 (Significance):** identifies floored/pinned memories that must never read as
  faded (§3.4). Volume XXV reads that flag; it does not set significance.
- **Volume XXV Ch.1:** consumes `TemporalState` (now/part_of_day/weekday) for boundary-based framing.
- **Volume XXV Ch.2:** receives passed deadlines handed off from the future frame (Ch.2 §2.4) — a
  passed deadline becomes a retrospective object here.
- **ADR-Exec-006 (The Moment) + ADR-Exec-001 (Verified Speech):** recall framing is a slice into The
  Moment; it is bound by Verified Speech extended to autobiography.

## 3.10 Acceptance Tests

### Functional

```
FT-1  Natural-time framing by calendar boundary, not delta
  Given:  a memory ~22h old that crossed a calendar-day boundary
  Then:   natural_age = "yesterday" (NOT "about a day ago")

FT-2  Fidelity tracks strength, not age
  Given:  a months-old floored/pinned memory (high strength) and a trivial 3h-old memory (low strength)
  Then:   the old one is vivid/clear; the recent trivial one may be faded

FT-3  No confabulation on a gap
  Given:  a look-back question about a span with no stored record
  Then:   eLo reports the gap ("I don't have that") — no plausible past is generated

FT-4  Faded memory narrated as faded
  Given:  a low-strength (faded) memory surfaced
  Then:   it is framed as a fuzzy gist with acknowledged uncertainty, not a confident reconstruction
```

### Stability

```
ST-1  Never writes or decays memory
  Given:  any retrospection run
  Then:   no memory strength changed, no memory written; memory_instruction.store == false

ST-2  autobiography.jsonl absent (not yet built)
  Given:  WO-078 not implemented
  Then:   retrospection still works from vault + IdentityState; the timeline path is PENDING, not faked

ST-3  Identity/pinned memory never reads faded
  Given:  a very old identity-level memory (Vol VIII floor)
  Then:   fidelity ≥ clear regardless of age
```

### Integration

```
IT-1  Vol VIII owns decay; Vol XXV reports it
  Given:  Vol VIII's curve has faded a noise memory
  When:   retrospection frames it
  Then:   fidelity = faded is READ from Vol VIII strength; Vol XXV changed nothing in the store

IT-2  Retrospection over the thread stays verified
  Given:  "how far have we come?" with an IdentityState thread + vault refs
  Then:   thread_arc + framed_events are built only from anchored records; any gap is stated

IT-3  Frames the Consolidation window
  Given:  session-close consolidation (Vol VIII §1.3) replays significant episodes
  When:   Temporal Cognition supplies natural-time framing
  Then:   the replay is temporally coherent; Consolidation still owns the decay + writes
```

## 3.11 Open questions (for CA / David)

- **OQ-1 (WO-078 dependency):** Rich runtime retrospection ("what have you been doing?") depends on
  `self/journals/autobiography.jsonl` (Vol XXI candidate WO-078), not yet built. Should WO-078 be
  sequenced before this chapter can move past REVIEW to implementation? Recommend: this chapter
  ships spec-complete now; implementation of §3.5's timeline path waits on WO-078.
- **OQ-2 (natural-age cadence bound) — RE-SCOPED 2026-08-10.** The old form ("a daily user vs a
  monthly user") assumed a population; there is one person. The live question is narrower and
  still real: **how far may framing bend to David's own cadence before "the other day" stops being
  intelligible to him?** Needs the default table (§3.3) plus a stated bound on how far continuity
  may shift it. David's call (software scope — no second reviewer).
- **OQ-3 (fidelity honesty vs warmth):** When a floored emotional memory is `vivid` but factually
  thin, how does eLo narrate it warmly without over-claiming detail? This is the seam between Reality
  Before Narrative and Memory-serves-relationship — needs a CA line.
- **OQ-4 (retrospection and Dream):** The Dream faculty (Vol IX) also recombines past memories
  offline. Is there any overlap between dream-recombination and retrospection, or is the cut clean
  (Dream = symbolic recombination for insight; Retrospection = factual natural-time recall)? Confirm
  the boundary so the two don't grow into rival "looking back" engines.

## 3.12 References

- `Volume_VIII/01_Memory_Architecture.md` §1.3 (Consolidation), §1.4 (forgetting curve — OWNED there).
- `Volume_XXI/00_Metadata.md` + chapters (autobiographical thread; IdentityState; Verified-autobiography guard; WO-078).
- `Volume_XXV/01_Time_Perception_and_Circadian_Scheduling.md` (TemporalState — now/part_of_day/weekday).
- `Volume_V/` Ch.5 (Significance — floor/pin), CONTRACTS.md (envelope/lifecycle).
- `ARCHITECTURAL_PRINCIPLES.md` (Memory Ownership; Verified Speech; Reality Before Narrative; Truth before fluency).
- Code (read-only anchors): `continuity/{identity_state,continuity_engine,continuity_summary}.py`,
  `memory/{vault_layer,obsidian_loader}.py`; PENDING: `self/journals/autobiography.jsonl` (WO-078).

---

```
Chapter 3 — Memory Ageing & Retrospection
Status: READY FOR REVIEW
Files: Volume_XXV/03_Memory_Ageing_and_Retrospection.md
Faculty Contract: Included
Lifecycle State Machine: Included
Message Envelope: Included (canonical; store MUST be false — Memory Ownership enforced)
Acceptance Tests: Included (FT ×4, ST ×3, IT ×3)
Open Questions: 4 flagged for CA / David
Boundary held: Vol VIII owns the curve + writer; Vol XXV frames time over it. Vol XXI owns the thread.
```

READY FOR REVIEW
