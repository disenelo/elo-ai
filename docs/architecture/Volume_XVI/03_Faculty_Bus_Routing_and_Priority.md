---
chapter: 3
title: "The Faculty Bus — Envelope Routing, Priority & Traceability"
volume: XVI
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PARTIAL (bus + envelope live; priority scheduling + full routing PENDING)
audit_status: OPEN
dependencies:
  - Volume_XVI/01_Coordination_Under_One_Executive.md ("all traffic goes through the bus")
  - Volume_XVI/02_Executive_Assembly_One_Plan.md (contributions arrive via the bus)
  - Volume_V/CONTRACTS.md §2 (canonical nine-field envelope — AUTHORITATIVE)
  - core/faculty_bus.py (Envelope + FacultyBus — live, WO-001)
  - ARCHITECTURE_AUDIT.md gap #1 (Faculty Bus — HIGHEST)
---

# Chapter 3: The Faculty Bus — Envelope Routing, Priority & Traceability

## 3.0 Purpose

One Brain forbids faculties from calling each other directly (Ch.1, Invariant #6). Every
inter-faculty message must cross **one** channel — the **Faculty Bus** — so that traffic is
**typed, routed, prioritised, and traceable**. Without a single channel, faculties drift
into private back-channels and the Executive can no longer see or govern the traffic; the
Architecture Audit names this gap #1 (HIGHEST).

This chapter defines *how* the bus moves envelopes: routing (who receives), priority (what
the Executive's scheduling means), and trace (how every hop stays observable). It is the
transport layer beneath Ch.2's Assembly (contributions ride the bus) and Ch.4's conflict
resolution (competing contributions are surfaced to the Executive via the bus).

## 3.1 Principle — One Channel, Typed and Traceable

**3.1.1 No direct calls.** A faculty never invokes another faculty. It publishes an
envelope; the bus routes it. A direct call bypasses the Executive's visibility and is a
One-Brain violation (Ch.1 prohibition: *bypass the Executive*).

**3.1.2 One canonical envelope.** All traffic uses the nine-field wire format ratified in
`Volume_V/CONTRACTS.md §2` (ADR-0001 / D-A · LAW). Malformed envelopes are rejected at the
boundary — never silently processed.

**3.1.3 Provenance is mandatory.** Every hop appends to `trace`. This is what gives the
Audit inter-faculty observability — the reason the bus is gap #1. Confidence may only be
**lowered** downstream, never raised (a faculty cannot inflate another's certainty).

## 3.2 The Envelope (canonical, live)

The bus carries the canonical nine-field envelope. This is **already implemented** in
`core/faculty_bus.py` as the `Envelope` dataclass:

```
Envelope (core/faculty_bus.py — LIVE):
  id          uuid                                   REQUIRED
  sender      PascalCase faculty name                REQUIRED
  receiver    PascalCase name | "*" (broadcast)      REQUIRED
  priority    low | normal | high | critical          REQUIRED  (drives scheduling — §3.4)
  context     { conversation_id, relationship_state, significance, memory_instruction }
  payload     { "type": str, "body": dict }           payload.type REQUIRED
  confidence  0.0–1.0                                  (only LOWERED downstream)
  expires     ISO-8601 | None                          (past-TTL envelopes dropped)
  trace       ["Faculty@ts", "Bus@ts", …]             (append-only per hop)
```

**Binding rules (MUST) — enforced in `Envelope.is_valid()` / `FacultyBus.publish()`:**

- `id`, `sender`, `receiver`, `priority`, `payload.type` required → else `REJECTED` to the
  `_dropped` audit log, never processed.
- `priority ∈ {low, normal, high, critical}` → else rejected.
- `0.0 ≤ confidence ≤ 1.0`; `lower_confidence()` raises if you attempt to *raise* it.
- `expires` past → `DROPPED: past expires` with a trace note; a slow faculty can never act
  on a stale world.
- `trace` is append-only (`_append_trace` adds `Bus@<ts>` on every publish).

## 3.3 Routing

`FacultyBus` (live) is a **synchronous, non-blocking** router — it holds no cross-thread
lock and must never stall the turn.

```
Routing model (core/faculty_bus.py — LIVE):
  subscribe(faculty, filter_fn=None)   register a receiver; optional predicate filter
  publish(envelope) -> bool            validate → trace → deliver to matching subscribers
  get_messages(faculty) -> [Envelope]  pull-and-clear the faculty's queue
  _addresses(env, faculty)             receiver == "*" (broadcast) OR receiver == faculty
```

**Routing rules (MUST):**

- Delivery is by `receiver`: exact match or `*` broadcast. A subscriber's optional
  `filter_fn` further narrows what it queues (e.g. the live proof pair: the Executive
  subscribes to `Attention` signals only when `priority ∈ {high, critical}`).
- Consumption is **pull-and-clear**: `get_messages` drains the queue. A faculty reads its
  inbox once per turn; nothing lingers to be re-processed next turn.
- The bus **never decides**. It moves envelopes; it does not resolve conflicts (that is the
  Executive's, Ch.4). It does not fabricate or reorder content.

**Live scope (grounded):** today the bus wires exactly one proof pair —
**Attention → Executive** (`_wire_proof_pair`, WO-001 acceptance criterion). Full faculty
subscription (Memory, Relationship, Capability, World, etc. onto the bus) is **PENDING** —
those faculties currently exchange state via the spine's in-process call order
(`runtime/spine/spine.py`), not yet via published envelopes. Migrating each faculty onto the
bus is the remaining work of Audit gap #1.

## 3.4 Priority — the Executive's Scheduling Dial

`priority` is the field through which the **Executive** expresses urgency across faculty
traffic (Ch.1: the Executive alone "assigns priorities"). It is a coordination signal, not a
faculty's self-granted importance.

```
Priority semantics (INTENDED):
  critical  safety / interrupt-now (e.g. distress, stop) — pre-empts the queue
  high      time-sensitive coordination the Executive wants first
  normal    default faculty traffic
  low       background / peripheral contributions
```

> **Invention flagged — not yet implemented.** The `priority` field is carried and
> validated in `core/faculty_bus.py`, and the live proof-pair filter reads it
> (`priority in ("high","critical")`). BUT the bus currently delivers in **arrival order**
> (`self._queues[faculty].append(...)` — FIFO); it does **not** yet order delivery by
> priority. Priority-ordered scheduling (critical pre-empts) is a **PENDING** enhancement
> and the semantics table above is a proposed target, not shipped behaviour. Mark PENDING;
> do not claim the bus prioritises today.

**Priority rules (MUST, on implementation):**

- Only the **Executive** sets `critical`/`high` for coordination; a faculty may not
  self-escalate to jump the queue (One Brain — no faculty out-ranks the Executive).
- `critical` is reserved for safety/interrupt paths and is a RESERVED-adjacent concern —
  changes to what counts as `critical` route through David L3 where safety is implicated.

## 3.5 Observability

The bus is the Audit's window into inter-faculty traffic. Live surfaces
(`core/faculty_bus.py`):

- `dropped_log()` — audit trail of every `REJECTED` (malformed) / `DROPPED` (expired)
  envelope, with reason and timestamp.
- `heartbeat()` — subscribers, per-faculty queue depths, total dropped. Consumed by the
  Debug Agent to see who is subscribed, who is backed up, and what is being discarded.
- `trace` on every envelope — the append-only provenance chain (`sender@ts → Bus@ts →
  receiver@ts`).

**Observability rule (MUST):** nothing crosses faculties invisibly. A message with no
trace, or a delivery the heartbeat cannot see, is a defect — the bus exists precisely to
make coordination auditable.

## 3.6 Faculty Contract (the Bus as infrastructure)

> The bus is **infrastructure**, not a cognitive faculty — it neither contributes to
> `CognitiveState` nor decides. Its contract is a transport contract.

```
Component:
  name:            FacultyBus
  version:         1.0.0 (core/faculty_bus.py — WO-001)
  purpose:         Route typed envelopes between faculties — validated, prioritised,
                   traceable — so all inter-faculty traffic is observable and governed.
  contributes_to:  (none — transport; carries others' contributions)
  runs_in:         response-path (synchronous, non-blocking)

Inputs:
  - type: envelope (any payload.type)  source: any faculty  required: true
Outputs:
  - type: envelope (routed)            destination: subscribed receiver(s)
  - type: dropped_log / heartbeat      destination: Debug Agent / Audit

Failure Modes:
  - condition: malformed envelope        fallback: REJECTED at boundary → _dropped; never processed.
  - condition: expired envelope          fallback: DROPPED with trace note; not delivered.
  - condition: no subscriber matches      fallback: publish() returns False; sender sees non-delivery.
  - condition: a faculty attempts a direct call (bypass)  fallback: architecturally disallowed;
               only bus traffic is honoured (Ch.1 prohibition).
```

## 3.7 Lifecycle & Envelope Binding

The bus is not a faculty and does not run the faculty lifecycle; it is a singleton
(`get_bus()`) available across the runtime. Faculties that ride it follow the ratified
lifecycle (`CONTRACTS.md §3`): they `REGISTER` (advertise + subscribe) before they publish,
and they consume their queue only while `ACTIVE`. Envelope shape is `CONTRACTS.md §2`
verbatim (§3.2 above) — this chapter adds no fields.

## 3.8 Acceptance Tests

### Functional
```
FT-1  Malformed rejected     Given an envelope missing payload.type, When published,
                             Then publish()=False and _dropped records REJECTED; no delivery.
FT-2  Broadcast + address     Given receiver="*", Then all subscribers receive; given a named
                             receiver, Then only that faculty's queue gets it.
FT-3  Filtered subscription   Given the Executive subscribes to Attention high/critical only,
                             When a normal Attention signal publishes, Then it is not queued.
FT-4  Trace appended          Given any successful publish, Then trace gains a Bus@<ts> hop.
```

### Stability
```
ST-1  Confidence never raised   Given lower_confidence(higher_value), Then it raises ValueError.
ST-2  Expired dropped           Given expires in the past, Then DROPPED (not delivered), logged.
ST-3  Pull-and-clear            Given get_messages() called twice, Then the second call is empty.
ST-4  Non-blocking              Given a slow subscriber, Then publish() does not stall the turn lock.
```

### Integration
```
IT-1  Proof pair (LIVE)   Attention.publish_attention_signal(high) → bus → Executive queue
                          receives it; a normal-priority signal does not. (WO-001 criterion.)
IT-2  Bus feeds Assembly  Faculty contributions published as cognitive_state_delta envelopes
                          are the inputs ExecutiveAssembly (Ch.2) composes. Assert no faculty
                          contributes to the assembled state except via the bus. [PENDING wiring]
```

## 3.9 Claude Implementation Notes

- The envelope and router are **live** (`core/faculty_bus.py`); do NOT rebuild them.
  Remaining work is (a) subscribing the real faculties (not just the proof pair) and
  (b) implementing priority-ordered delivery (§3.4) — currently FIFO.
- Keep the bus **synchronous and non-blocking** — it must never hold a cross-thread lock or
  stall the turn (existing constraint in the module docstring).
- When migrating a faculty onto the bus, preserve behaviour parity: route its existing
  in-process contribution through a published envelope, assert identical downstream output
  (the same discipline used for the World State migration in `Volume_XV`).

## 3.10 References
- `Volume_V/CONTRACTS.md §2` — canonical nine-field envelope (AUTHORITATIVE), lifecycle §3.
- `Volume_XVI/01…` — "all traffic goes through the Faculty Bus" (Ch.1 §1.1).
- `Volume_XVI/02…` — Assembly consumes bus-delivered contributions.
- `ARCHITECTURE_AUDIT.md` — gap #1 (Faculty Bus, HIGHEST).
- Code: `core/faculty_bus.py` (`Envelope`, `FacultyBus`, `make_envelope`, `get_bus`,
  `_wire_proof_pair`, `publish_attention_signal`).

---
```
Chapter 3 — The Faculty Bus — Envelope Routing, Priority & Traceability
Status: READY FOR REVIEW
Live code cited: core/faculty_bus.py (Envelope + FacultyBus + proof pair — LIVE)
Grounded: envelope validation, routing, trace, dropped log, heartbeat, Attention→Executive pair
Flagged PENDING: priority-ordered scheduling (FIFO today) · full faculty subscription (proof pair only)
Faculty/Transport Contract: Included · Acceptance Tests: FT×4 ST×4 IT×2
Implementation: PARTIAL (bus live; priority + full routing PENDING)
```

READY FOR REVIEW
