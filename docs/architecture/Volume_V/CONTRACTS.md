---
volume: V
document: "Shared Faculty Contracts — Message Envelope, Lifecycle, Base Contract"
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Architecture Agent)
implementation: PENDING
audit_status: OPEN
authoritative_sources:
  - architecture/16_runtime_contracts.md   # the four runtime contracts — AUTHORITATIVE
  - architecture/Volume_V/01_Cognitive_Core.md  # faculty registry + eight laws — AUTHORITATIVE
  - architecture/Volume_V/00_Metadata.md    # build queue + DoD
purpose: >
  Fill the three cross-cutting gaps the Volume V Definition of Done names for
  EVERY chapter — the message envelope, the per-faculty lifecycle state machine,
  and the base faculty contract shape — in ONE place, so all ten chapters bind to
  a single source of truth instead of restating (and drifting) it ten times.
non_authoritative_over:
  - The four runtime contracts (16_runtime_contracts.md) — this doc defers to them.
  - The faculty registry and eight laws (Chapter 1) — this doc defers to them.
---

# Volume V — Shared Faculty Contracts

> This document is **connective tissue, not a competing model.**
> `16_runtime_contracts.md` owns the four runtime contracts. Chapter 1 owns the
> faculty registry and the eight architecture laws. This document owns only the
> three things the DoD demands of *every* chapter and that neither of those two
> pins down completely: the **message envelope**, the **faculty lifecycle**, and
> the **base contract shape**. Where any conflict appears, those two documents win.

---

## 1. Where faculties sit in the runtime

Every Volume V faculty is a contributor to the one cognition. It does exactly one
of two jobs, per `16_runtime_contracts.md`:

```
Observe
  ↓
FACULTIES ──► contribute to CognitiveState        (everything known)
  ↓
Executive ──► produces CognitivePlan               (everything decided — once)
  ↓
Execution ──► EmbodimentState                       (everything expressed)
  ↓
           ──► ExecutionReport                       (what actually happened)
  ↓
Reflection Faculty ──► integrate_session()          (grows memory / identity)
  ↓
Next observation.
```

- **Upstream faculties** (Language, Memory, Attention, Relationship, Environment,
  Capability, **Emotional Processing — Ch.4**) write into `CognitiveState` and then
  freeze. They never decide.
- **The Executive** (Ch.1 / Vol VII) is the only decider. It reads the frozen
  `CognitiveState` and emits exactly one `CognitivePlan`.
- **Integration-time faculties** (**Reflection & Growth — Ch.6**,
  **Personality Evolution — Ch.7**) never run in the response path. They consume
  `ExecutionReport` and update memory/identity through `integrate_session()` only.

This placement is normative. A faculty that decides, or that mutates a frozen
contract, or that re-thinks downstream of the Executive, is violating the runtime
(Law: *one decision per turn*; Law: *reality never mutates intention*).

---

## 2. The Message Envelope (canonical, reconciled)

Two envelope shapes exist in the canon and must be reconciled before the Faculty
Bus (Architecture Audit gap #1) can be built:

| Field set | Source |
|---|---|
| `{id, sender, receiver, priority, context, payload, confidence, expires, trace}` | `16_runtime_contracts.md`, `00_Metadata.md`, Audit gap #1 — **the Bible wire format** |
| `{message_id, timestamp, source_faculty, destination_faculty, event_type, context, payload, confidence, significance, memory_instruction}` | early cognitive draft (used verbatim in Ch.1 §12) |

**Resolution (recommended, pending ratification by both architects):**
adopt the **Bible nine-field wire format as canonical**, and carry the cognitive
draft's extra fields *inside* `context`/`payload` rather than at the top level.
Nothing is lost; there is exactly one envelope on the wire.

```jsonc
{
  "id":       "uuid",              // was message_id
  "sender":   "FacultyName",       // was source_faculty
  "receiver": "FacultyName | *",   // was destination_faculty ; "*" = broadcast
  "priority": "low|normal|high|critical",   // drives bus scheduling (new — required)
  "context": {
    "conversation_id":   "",
    "relationship_state":"",
    "environment_state": "",
    "significance":      0.0,      // Significance Engine (Ch.5) writes this; 0.0 until then
    "memory_instruction":{ "store": false, "priority": "peripheral|normal|high|pinned" }
  },
  "payload": {
    "type": "cognitive_state_delta | affect_state | execution_report | reflection_insight | personality_delta | ...",
    "body": { }                    // typed per `type`
  },
  "confidence": 0.0,               // producer's confidence; downstream may only LOWER it
  "expires":    "ISO-8601 | null", // TTL — stale messages are dropped, not processed
  "trace":      ["FacultyA@ts", "Bus@ts", "FacultyB@ts"]  // provenance chain (subsumes timestamp)
}
```

**Binding rules (MUST):**

1. `id`, `sender`, `receiver`, `priority`, `payload.type` are required. Malformed
   envelopes are rejected at the bus boundary, never silently processed.
2. `confidence` may only be **lowered** downstream, never raised (matches Ch.1 §7
   and Principle *never pretend certainty*).
3. `context.significance` is written **only** by the Significance Engine (Ch.5).
   Every other faculty leaves it `0.0`.
4. `trace` is append-only. Every hop appends `Faculty@timestamp`. This is what gives
   the Audit inter-faculty observability (the reason the bus is gap #1).
5. `expires` honoured by the bus: an envelope past its TTL is dropped with a trace
   note, so a slow faculty can never act on a stale world.

> **Chapter 1 note (additive, non-destructive):** Ch.1 §12 uses the draft field
> names. This document does not edit Ch.1. Treat the mapping in this section as the
> ratified reconciliation; the builder implements the nine-field wire format and
> Ch.1's `CognitiveFrame` serialises into `payload.body` with `type:"cognitive_state_delta"`.

---

## 3. The Universal Faculty Lifecycle

**RATIFIED — ADR-0002 / D-B (2026-07-27) · LAW.** The FINAL canonical lifecycle
(supersedes the earlier Register→…→Shutdown and DORMANT→…→STABLE drafts):

```
BOOT → REGISTER → INITIALISE → READY → ACTIVE → WAITING → SLEEPING → ACTIVE
Exception:  ACTIVE → ERROR → RECOVERY → READY
Shutdown:   READY → SHUTDOWN
```

```
   BOOT            process starts
       ↓
   REGISTER        advertise on the Faculty Bus (capability, confidence, latency, cost, health, version)
       ↓
   INITIALISE      load contract, dependencies, priors
       ↓
   READY ◄──────────────────────────────────────────────┐   subscribed, idle, awaiting a signal
       ↓                                                 │
   ACTIVE          handling a signal (receive → execute → respond)
       ↓   │ fault                                       │
   WAITING │       awaiting a dependency / downstream     │
       ↓   ▼                                             │
   SLEEPING        low-power dormant; wakes to ACTIVE ────┘
       │
       │  exception path
       ▼
   ACTIVE → ERROR → RECOVERY → READY        (recovery MUST pass through READY)
   READY  → SHUTDOWN                        (only orderly termination; never unexpected)
```

**Rules (MUST):** every faculty implements **every** state · faculties may SLEEP ·
faculties may **never terminate unexpectedly** · RECOVERY MUST always pass through READY ·
the **Executive orchestrates** lifecycle. Integration-window work (Learn → Validate → Update,
Ch.6/Ch.7) occurs during WAITING/SLEEPING, never in ACTIVE's response path.

Mapping from the superseded draft: READY = old ACTIVE(idle); ACTIVE = old PROCESSING;
Learn/Validate/Update = old LEARNING/VALIDATION_REQUIRED/
UPDATING (integration window only), Sleep/Shutdown are now explicit (nothing runs forever).

**Rules (MUST):**

- **`ERROR_RECOVERY` always resolves to `ACTIVE`.** A faculty may degrade its output
  (Mock, neutral, cached) but must never leave the runtime unable to take a turn.
- **No `LEARNING → UPDATING` without `VALIDATION_REQUIRED`.** Any change to
  personality/preference/identity-adjacent state passes the Ch.7 identity-continuity
  check first. This is the single guard against destructive self-mutation.
- **`LEARNING`/`UPDATING` never occur in the response path.** They run only in the
  integration window (idle or session close), preserving *one decision per turn* and
  *consistency over novelty*.
- A faculty advertises its current lifecycle state on request (`heartbeat`) so the
  Kernel and Audit can see who is `ACTIVE`, `DORMANT`, or stuck in `ERROR_RECOVERY`.

---

## 4. The Base Faculty Contract (shape every chapter fills)

Every Volume V faculty declares itself in this shape. Chapters 1, 4, 5, 6, 7, 8, 9,
10 each provide a concrete instance.

```
Faculty:
  name:            # PascalCase, unique in the registry (Ch.1)
  version:         # semver — faculties are versioned units
  purpose:         # one sentence — its single responsibility
  contributes_to:  # CognitiveState | CognitivePlan | ExecutionReport-consumer | Embodiment
  runs_in:         # response-path | integration-window

Inputs:
  - type:          # a payload.type it consumes
    source:        # producing faculty or sensor
    required:      # true | false
    description:

Outputs:
  - type:          # a payload.type it produces
    destination:   # consuming faculty / bus / contract field
    description:

Dependencies:
  - faculty:       # hard (required) or soft (degrades gracefully) — state which

Failure Modes:
  - condition:
    fallback:      # MUST keep the runtime able to take a turn (graceful degradation)
```

**Contract law (MUST):** every faculty degrades gracefully. A missing dependency,
a failed model call, or a corrupt input produces a *lower-confidence but valid*
contribution — never a stalled turn. This is the runtime-level expression of
Ch.1's failure-mode discipline and the Identity Kernel's "no false capability."

---

## 5. How the three DoD items are now satisfied

| DoD line | Satisfied by |
|---|---|
| Every faculty contract defined | §4 base shape + each chapter's concrete instance |
| Every state machine defined | §3 universal lifecycle (+ any chapter-specific inner state machine) |
| API definitions (message envelope) | §2 canonical nine-field envelope |
| Every failure mode documented | §4 contract law + per-chapter Failure Modes |
| Acceptance tests per chapter | in each chapter (FT / ST / IT) |

---

## Open Decisions

```
REQUIRES DECISION — 2 items
  D-A: Ratify §2 envelope reconciliation (nine-field Bible wire format canonical;
       cognitive draft fields moved into context/payload). Recommended: accept.
       Owner: David + both architects. Blocks: Faculty Bus (Audit gap #1) build.
  D-B: Confirm §3 unified lifecycle supersedes the two partial descriptions in
       00_Metadata and the early draft. Recommended: accept as the single lifecycle.
```

---

```
Shared Faculty Contracts
Status: READY FOR REVIEW
Files: CONTRACTS.md
Message Envelope: Reconciled (canonical nine-field)
Universal Lifecycle: Included
Base Faculty Contract: Included
Defers to: 16_runtime_contracts.md, Chapter 1
Open Decisions: 2 (REQUIRES DECISION — D-A, D-B)
```

READY FOR REVIEW
