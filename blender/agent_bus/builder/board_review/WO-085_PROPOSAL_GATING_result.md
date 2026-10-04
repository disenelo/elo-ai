# WO-085 Proposal Gating — Result Card

**Builder:** Builder 1
**Date:** 2026-10-04
**Status:** COMPLETE — 8/8 ATs pass; already implemented in prior session

---

## What was verified

`faculties/synthesis/observer.py` + `server.py`:
- At most 1 proposal fires per batch of observed items (rate/relevance gate)
- After decline, same topic suppressed for cooldown period
- Relaxation signal → zero proposals (respects state)
- No user-facing output contains "vault" in proposal phrasing
- No fabricated "it's touching X tracker" link claims in offers
- `record_decline()` sets global cooldown → `observe()` returns None
- Offer uses natural phrasing variants (not a fixed mechanical string)

## ATs

- AT-1 ✅ 6 observed items → at most 1 proposal fires
- AT-2 ✅ after decline, same topic suppressed for cooldown
- AT-3 ✅ relaxation signal → zero proposals
- AT-4 ✅ no user-facing output contains "vault" in proposal phrasing
- AT-5 ✅ no "it's touching X tracker" fabricated link claim in offer
- AT-6 ✅ record_decline() sets global cooldown → observe() returns None
- AT-7 ✅ offer uses natural phrasing variants (not a fixed string)
- AT-8 ✅ py_compile clean on observer.py and server.py

**Run:** `python3 tests/test_wo085_proposal_gating.py` → **8/8 passed**
