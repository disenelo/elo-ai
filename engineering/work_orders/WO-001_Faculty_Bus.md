---
id: WO-001
title: "Faculty Bus + canonical message envelope"
status: READY            # D-A ratified 2026-07-27 — unblocked
target_agent: Builder
priority: P0
owner: ""
depends_on: [decision D-A]
blocks: [WO-006, WO-002-observability]
spec_refs:
  - docs/architecture/Volume_V/CONTRACTS.md
  - docs/architecture/ARCHITECTURE_AUDIT.md
audit_gap: "Critical Gap #1 (HIGHEST)"
created: 2026-07-27
---

# WO-001 — Faculty Bus + canonical message envelope

## 1. Objective
Build `core/faculty_bus.py`: a typed message envelope and routing layer that every
faculty passes through, so inter-faculty traffic is observable and traceable.

## 2. Why now
Architecture Audit **gap #1 (highest)**. Today faculties communicate via direct Python
imports and free-form dicts — no trace, no way to know which faculty produced which part
of a response. As faculties grow, debugging becomes impossible. The bus is the
observability spine every later WO relies on.

## 3. Spec references (read first)
- `Volume_V/CONTRACTS.md §2` — the canonical nine-field envelope (this is what to build).
- `Volume_V/CONTRACTS.md §1` — where faculties sit relative to the four runtime contracts.
- `ARCHITECTURE_AUDIT.md` — gap #1 statement.

## 4. Deliverable
- `core/faculty_bus.py` exposing:
  - `Envelope` dataclass: `{id, sender, receiver, priority, context, payload, confidence, expires, trace}`.
  - `publish(envelope)` / `subscribe(faculty, filter)` — routing + broadcast (`receiver="*"`).
  - Boundary validation: reject envelopes missing `id/sender/receiver/priority/payload.type`.
  - `trace` append on every hop; drop envelopes past `expires`.
  - `confidence` may only be lowered downstream (assert in transit).

## 5. Files to TOUCH
- `core/faculty_bus.py` — new.
- Wire ONE producer/consumer pair first (e.g. Attention → Executive) as proof; do not
  migrate all faculties at once.

## 6. Files/things you MUST NOT touch
- `runtime/executive.py`, `prompts/` (FREEZE_V1_LOCK).
- Do not change faculty *decisions* — this is transport only.
- Do not raw-write `blender/blender_state.json`.

## 7. Acceptance tests (Definition of Done)
- [ ] An envelope missing a required field is rejected at the boundary (not processed).
- [ ] `trace` shows every hop `Faculty@ts` for a round-trip.
- [ ] An expired envelope (past `expires`) is dropped with a trace note.
- [ ] `confidence` cannot be raised in transit (attempt → rejected/clamped).
- [ ] The proof producer/consumer pair exchanges a real turn's data with identical
      behaviour to the pre-bus path (parity).
- [ ] Regression: full conversation batch unchanged in output.

## 8. Risks / footguns
- The whole turn holds one lock (`server._process_turn`) — the bus must be synchronous
  and non-blocking within the turn; no cross-thread stalls.
- `contracts.py` is target-state; the bus transports envelopes, it does not require the
  four contracts to be fully wired yet.

## 9. Handback
Diff + test output + a short note updating `ARCHITECTURE_AUDIT.md` gap #1 row to reflect
the bus landing. Architecture verifies against §7 before `DONE`.

> D-A ratified 2026-07-27 by David. Status: READY. Routed to Builder.
