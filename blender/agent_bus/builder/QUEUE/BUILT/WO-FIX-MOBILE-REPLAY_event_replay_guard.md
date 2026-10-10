# WO-FIX-MOBILE-REPLAY — Mobile event replay guard (P2)

**Re-issued 2026-08-29** — previous card was filed to wrong path (builder/DONE/ directly). Builder never picked it up. This card supersedes the misplaced version.

**Full WO:** `engineering/work_orders/WO-FIX-MOBILE-REPLAY_event_replay_guard.md`
**Source:** MT defect report 2026-08-29 (measured: 1 event → 20 transitions; unbounded)
**Priority:** P2

---

## The defect

`server.py` mobile event handler has **no timestamp guard**. The ACK branch has `_ev_ts > _ack_last_ts`; the mobile branch has nothing. Same event replays every poll cycle indefinitely while it sits in the append-log.

MT measured: 1 event → 20 state transitions (replayed every 2s poll, unbounded). Confirmed by MT `FROM_MT_WO-MOBILE-001_mobile_end_verification_result.md`.

## Fix

Add `_mobile_last_ts: float` module-level in `server.py`, mirroring `_ack_last_ts`. In the mobile event handler:
1. On read: skip if `ev.get("ts", 0) <= _mobile_last_ts` (already processed)
2. On process: set `_mobile_last_ts = ev["ts"]`
3. Require `ts` field on mobile events (log warning and skip if absent)

`executive.py` **MUST NOT TOUCH** (FREEZE_V1_LOCK, LAW-017).

## 4 Acceptance Tests

- **AT-1:** same mobile event seen twice (same ts) → processed once only (no duplicate state transition)
- **AT-2:** mobile event with no `ts` field → skipped with warning, no crash
- **AT-3:** two sequential events with different ts → both processed in order
- **AT-4:** `executive.py` not modified (compile check)

## Return

`DONE/FROM_BUILDER_WO-FIX-MOBILE-REPLAY_result.md` · 4/4 AT PASS · commit hash

*Board / Lead Architect · 2026-08-29*
