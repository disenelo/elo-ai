# BUILDER 1 → BOARD: WO-INNER-THOUGHT-ORDERING — Built
**Date:** 2026-10-11  
**From:** Builder 1  
**To:** Board  
**Commit:** dd3aecf

---

## What was built

`server.py` — inner thought now fires BEFORE the main response (David's 3-beat spec).

**Beat 1:** ACK now fires on complex turns via `pre_thought["complex"]`, not just tool turns.  
**Beat 2:** `collect(_it_early_flight, timeout_s=0.8)` called before LLM. If thought formed, spoken via TTS immediately — user hears it before the main response.  
**Beat 3:** Actual thought text injected into system prompt, superseding the pre_thought skeleton. Executive sees the real thought.

**collect() idempotent:** post-response background thread calls collect() again → returns "" → no double-speak. No flag needed.

---

## Previous behaviour

Inner thought generated POST-response in background thread, spoken as a closing reflection. Users heard: response → (15s later) inner thought. Inverse of David's spec.

## New behaviour

ACK (if complex) → inner thought spoken → LLM fires with thought in context → main response.

---

## Tests

3875 passing. Pre-existing 24 failures and collection errors unaffected by this change (confirmed by running full suite before and after).

---

## Note on timeout

Builder 1 used 0.8s timeout (Board had not yet confirmed). The early_runner starts at turn entry (line 2643) and has 2–5s of system-assembly time before collect() fires. Most thoughts should be ready. If timeout is too short or long, Board can adjust the constant.

*Builder 1 · 2026-10-11*
