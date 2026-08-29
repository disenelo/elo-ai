# WO-FIX-MOBILE-REPLAY — Mobile event replay guard (P2)

**Full WO:** `engineering/work_orders/WO-FIX-MOBILE-REPLAY_event_replay_guard.md`
**Source:** MT defect report 2026-08-29 (measured: 1 event → 20 transitions; unbounded)

`server.py` mobile event handler has no timestamp guard. ACK branch has `_ev_ts > _ack_last_ts`; mobile branch has nothing. Same event replays every poll cycle while it sits in the append-log.

Fix: add `_mobile_last_ts` guard mirroring ACK branch. Require `ts` field on mobile events.
`executive.py` MUST NOT TOUCH.

4 ATs. Return: `DONE/FROM_BUILDER_WO-FIX-MOBILE-REPLAY_result.md`

*Board · 2026-08-29*
