# WO-B1-0111 — Unlearn Mechanism
**Seat:** Builder 1  
**Priority:** P1 — demo milestone end of October  
**Source:** `docs/architecture/_intake/SOURCE_DEMO-MILESTONE_2026-10-10.md` [DAVID 2026-10-10]  
**Date:** 2026-10-10

---

## What

eLo can unlearn — David can correct a wrong WKG node and eLo stops using it. Or eLo recognises a node is stale/incorrect and marks it for review.

Two paths:
1. **David-initiated:** "That's not right" / "Forget that" / "I told you wrong" → eLo marks the relevant WKG node as `status: deprecated` or updates it with the correction
2. **Self-initiated (stretch):** eLo notices a node contradicts a newer retrieval and flags it for reconciliation

---

## How

- Add intent pattern to `intent_engine.py` or capability dispatcher: detect correction/forget intent
- Map to WKG node update: find the node most recently used or most relevant to the correction, set `status: deprecated` or overwrite `value` with the correction
- Confirmation: eLo acknowledges the correction in character ("Got it, I had that wrong")
- Log the unlearn event to `decision_trace.jsonl` — provenance matters

Scope: David-initiated path only for demo. Self-initiated is post-demo.

---

## Done when

Live turn: David corrects a fact eLo has used before. eLo updates the WKG node. Next time the topic comes up, eLo uses the corrected version. Board verifies: (1) node updated, (2) old value deprecated, (3) new retrieval uses corrected value.

File to Board for sign-off.
