---
chapter: 1
title: "Coordination Under One Executive"
volume: XVI
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
source: "Bible content, David Charles 2026-07-27"
implementation: PARTIAL
audit_status: OPEN
dependencies:
  - Volume V/CONTRACTS.md (Faculty Bus, envelope, lifecycle D-B), Ch.1 (Executive)
---

# Chapter 1: Coordination Under One Executive

## 1.0 Philosophy

eLo OS is one mind with specialised cognition — never multiple selves. Every faculty is
an extension of the Executive. There is exactly **one** consciousness, identity,
personality, memory, and Executive. Coordination is not negotiation between peers; it is
one Executive directing its own faculties.

## 1.1 Principles (law)

- **One Brain** — multiple faculties, never multiple selves.
- **Executive Authority** — the Executive is the *only* faculty authorised to: allocate
  attention · approve actions · interrupt cognition · assign priorities · resolve conflicts.
- **Faculty Autonomy** — faculties solve problems independently but **never initiate
  external actions**. They advise; the Executive acts.
- **Consensus** — if faculties disagree, the **Executive decides**. Never voting, never
  democracy.
- **Communication** — all traffic goes through the **Faculty Bus** (`CONTRACTS.md §2`).
  Never direct calls.

## 1.2 Capability Discovery

Faculties advertise, and the Executive chooses:

```
Capability · Confidence · Latency · Cost · Health · Version
```

(These fields align with the Faculty Genome, Volume XXII.) The Executive selects which
faculty handles a need based on this advertisement — a market the Executive alone clears.

## 1.3 Coordination Loop

```
Observe → Understand → Plan → Allocate → Execute → Reflect → Learn
```

`Allocate` is the Executive-only step where attention/priority are assigned to faculties.
This loop composes with the runtime contracts (Observe→CognitiveState; Plan→CognitivePlan;
Execute→EmbodimentState/ExecutionReport; Reflect/Learn→integrate_session).

## 1.4 Coordination Rules (prohibitions — MUST)

No faculty may:
- overwrite another faculty,
- bypass the Executive,
- modify personality (only Ch.7's validated path may),
- write long-term memory directly (only the Memory Faculty may — **D-F**; others submit
  Memory Candidates).

## 1.5 Faculty Contract (the Coordinator role)

```
Faculty:
  name:            ExecutiveCoordination      # a role of the Executive (Vol VII), not a new decider
  version:         1.0.0
  purpose:         Allocate attention, resolve faculty conflicts, and clear the capability
                   market — so many faculties act as one mind.
  contributes_to:  CognitivePlan (allocation + conflict resolution)
  runs_in:         response-path

Inputs:
  - type: faculty_advertisement  source: every faculty (capability/confidence/latency/cost/health/version)  required: true
  - type: faculty_report         source: every faculty via Faculty Bus   required: true
Outputs:
  - type: allocation             destination: faculties (who does what, priority)
  - type: conflict_resolution    destination: CognitivePlan
Dependencies:
  - faculty: FacultyBus (hard — the only channel), all faculties (advertise)
Failure Modes:
  - condition: faculties conflict        fallback: Executive decides (never vote); log rationale.
  - condition: a faculty tries direct action  fallback: rejected at the bus; only Executive-approved actions execute.
  - condition: capability advert missing  fallback: Executive treats faculty as unavailable; degrades.
```

## 1.6 Lifecycle & Envelope
Ratified lifecycle (CONTRACTS.md §3, D-B). Envelope §2: coordination messages use
`payload.type: faculty_advertisement | allocation | conflict_resolution`; `priority` set
by the Executive; all via the bus (no direct calls).

## 1.7 Acceptance Tests
```
FT-1  Executive-only allocation   Given two faculties want the same resource, Then the Executive allocates; no faculty self-assigns.
FT-2  Capability market            Given faculties advertise capability/confidence/cost, Then the Executive selects the best fit.
ST-1  No voting                    Given faculties disagree, Then the Executive decides unilaterally; no consensus vote occurs.
ST-2  No bus bypass                Given a faculty attempts a direct call, Then it is rejected; only bus traffic is honoured.
ST-3  Prohibitions hold            Given a faculty attempts to write long-term memory / modify personality, Then it is blocked (D-F / Ch.7).
IT-1  One mind end-to-end          Observe→…→Learn runs with many faculties advising and one Executive deciding once per turn.
```

## 1.8 References
- `Volume_V/` Ch.1 (Executive), Ch.2 (Faculty System), CONTRACTS.md (bus/envelope/lifecycle).
- `Volume_XXII` (Faculty Genome — capability schema). `DECISION_LOG.md` (D-F, D-G).

---
**Status: READY FOR REVIEW** — One Brain coordination law + contract/lifecycle/envelope/tests. Canonicalised from David's Bible content.