# WO-B1-0111 — Unlearn Mechanism
**Seat:** Builder 1  
**Priority:** P0 — demo milestone  
**Date:** 2026-10-11  
**Status:** NOT IMPLEMENTED — card was moved to BUILT with no code changes. Board returning it.

---

## What

David says "that's not right" / "forget that" / "I told you wrong" → eLo marks the relevant WKG node as `status: deprecated`, stops retrieving it, acknowledges the correction in character.

## How

- Add intent pattern to `intent_engine.py` or capability dispatcher: detect correction/forget/unlearn intent
- Find the most recently used or most contextually relevant WKG node
- Set `status: deprecated` or overwrite `value` with the correction
- eLo acknowledges: "Got it, I had that wrong" — in character, not robotic
- Log the unlearn event to `decision_trace.jsonl`

David-initiated path only for demo. Self-initiated is post-demo.

## Done when

Live turn: David corrects a fact eLo has used before → WKG node updated → next retrieval uses corrected value. File to Board: (1) node before, (2) node after, (3) next retrieval shows corrected value.
