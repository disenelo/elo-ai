# Board Review — WO-094: Window Events — eLo Notices and Chooses
**Date:** 2026-10-11
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

---

## Card scope

Builder §B — brain consumes window events and decides:
- `consume_window_events()` reads from `unity_events.json`; absent/non-window/eLo-surface all handled
- `decide_window_event()` returns real decision (can legitimately decide to ignore)
- `user_active` → peripheral (does not interrupt David working)
- Route memory: ACK-gated writes, append-only, recall prefers success, confidence tracks experience
- §D learning: outcomes written ONLY on verified body ACK; route recall beats re-solve for known targets
- Nothing in the learning path touches identity/values/personality (ADR-Exec-005)

Designer §A (emit events UP) and §C (free-form routing via existing planner) are Unity agent handover.

---

## Commit

- `38676e8` — WO-094: window events — brain notices and chooses

---

## Tests — `tests/test_wo094_window_events.py`

```
python3 tests/test_wo094_window_events.py
→ WO-094 window events  5 passed  0 failed
```

| AT | Result |
|----|--------|
| AT-0: consume_window_events: absent/non-window/window handled | ✅ |
| AT-1: decide_window_event returns None for empty state / eLo surface / unknown type | ✅ |
| AT-2: user_active → peripheral; idle+curiosity → observe/glance | ✅ |
| AT-3: route_memory: ACK gate, append-only, recall prefers success | ✅ |
| AT-4: ambient_engine.py wires WO-094; all three files compile clean | ✅ |

---

## Board decisions required

None. Designer half (emit UP) still needs Unity agent handover.

*Builder 1 · 2026-10-11*
