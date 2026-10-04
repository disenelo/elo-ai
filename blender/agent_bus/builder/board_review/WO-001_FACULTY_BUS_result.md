# WO-001 Faculty Bus — Result Card

**Builder:** Builder 1
**Date:** 2026-10-04
**Status:** COMPLETE — 5/5 ATs pass; already implemented in prior session

---

## What was verified

`core/faculty_bus.py`:
- `Envelope` dataclass: id, sender, receiver, priority, context, payload, confidence, expires, trace
- `publish(envelope)` routes to subscribers by receiver or broadcast (`"*"`)
- Boundary validation: rejects envelopes missing required fields
- `trace` appended on every hop; expired envelopes dropped with trace note
- `confidence` invariant: lowering allowed, raising rejected in transit
- `get_bus()` returns module singleton

## ATs

- FT-1 ✅ publish routes envelope to subscriber
- FT-2 ✅ confidence invariant — lower allowed, raising rejected
- FT-3 ✅ expired envelope dropped; trace note in dropped_log
- ST-1 ✅ get_messages pull-and-clear — second pull returns empty
- ST-2 ✅ get_bus() module singleton — same instance across calls

**Run:** `python3 tests/test_wo001_faculty_bus.py` → **5/5 passed**

## Files

- `core/faculty_bus.py` — Envelope, publish, subscribe, get_bus
