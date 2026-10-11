# Board Review — S1-DEGRADED-HOLDING-LINE-TERMINAL
**Date:** 2026-10-11
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

---

## Card scope

P0 defect: degraded holding line served as FINAL answer. 25% of turns (5/20) were
`"On it — just a moment."` with no follow-up. Root cause: `server.py:7209` replaced
mock's real response with a stall string that was never followed up.

Two fixes applied:

1. **`server.py:7209` — holding-line block now `pass`**: mock's real eLo-register
   response is let through instead of being discarded. Already committed before
   context compaction; confirmed in source this session.

2. **`_condition_outbound` — empty-response outbound guard**: any turn whose
   `response` is empty or whitespace-only (and mode is not `error`/`reset`/`silent`)
   is intercepted, logged at WARNING, and replaced with a fallback before the
   response reaches the client. Covers fast-paths (41+) that bypass D-6.

---

## Commit

- `_condition_outbound` guard + test: committed below in this session

---

## Tests — `tests/test_s1_degraded_holding_line.py`

```
python3 tests/test_s1_degraded_holding_line.py
→ S1-DEGRADED  7 passed  0 failed
```

| AT | Result |
|----|--------|
| AT-0a: _bh_degraded block exists | ✅ |
| AT-0b: stall-line assignment NOT present in degraded block | ✅ |
| AT-0c: `pass` keyword present in degraded block | ✅ |
| AT-1: empty response replaced with fallback at outbound gate | ✅ |
| AT-2: non-empty response passes through unchanged | ✅ |
| AT-3: error-mode empty response not patched | ✅ |
| AT-4: whitespace-only response replaced with fallback | ✅ |

---

## Board decisions required

None. Separate finding (§2 — ollama quality regression at 18-20s latency) is a
distinct track; not blocked on this card.

*Builder 1 · 2026-10-11*
