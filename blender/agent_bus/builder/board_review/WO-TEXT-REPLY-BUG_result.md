# TEXT-REPLY-BUG — RESULT: Root cause 1 FIXED; Root causes 2-3 OPEN (Board decision)
**Status:** Partial — silence gate race fixed (86b46e0); latency is voice_rewrite (Board option needed)
**Evidence:** `engineering/evidence/TEXT_REPLY/text_reply_bug_analysis.md`

---

# DISPATCH — Live Bug: Text Reply Missing / Latency in DISENELO Presence
**From:** Board / Lead Architect
**To:** Builder 1
**Date:** 2026-10-03
**Priority:** P1 — live, David-reported

## Symptom (David verbatim)
"why is there latency in DISENELO presence text reply, sometimes he replies to me but not in text"

eLo speaks (TTS fires) but text does not appear — or appears with significant delay — in DISENELO Presence UI. Intermittent. Not fixed despite Builder 2 reporting "Bug 2 closed."

**PARTIAL = BROKEN. Bug 2 is not closed.**

## What to diagnose

The HTTP API text reply path in server.py:
1. Where does `response` field get written to the HTTP response / socket?
2. Is `response` always populated before the reply is sent, or can it be empty/None?
3. Is there a race condition between TTS (`inner_thought`) firing and the text (`response`) being pushed to the UI?
4. Does voice_rewrite affect the text path? The recent fix (content-preservation guard) targets `elo_final` collapse — does the text UI read `elo_raw_gen` or `elo_final`?
5. Is there a separate code path for voice vs text in server.py that could diverge?

## What to check
- `runtime/server.py` — the HTTP response construction. Find where text is sent to DISENELO Presence.
- `runtime/voice_rewrite.py` — does it block or delay the text response?
- Any async/threading issue where TTS fires before the text socket write completes?
- Check whether the `response` field is ever None, empty string, or skipped when `inner_thought` takes priority.

## Acceptance
David sends a message → text reply appears in DISENELO Presence within expected latency, every time. No missing text responses. TTS and text are independent — voice speaking does not prevent text from appearing.

## Also — server restart correction
Builder 1 does NOT need to wait for a separate server restart to run RR22. Designer rebuilds restart the server every time. Run RR22 immediately after next Designer build or current restart. Do not hold COG-004/008/010/012/017 retests for a dedicated restart.
