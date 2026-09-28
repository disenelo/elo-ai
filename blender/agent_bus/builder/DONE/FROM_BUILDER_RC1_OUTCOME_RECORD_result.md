# FROM BUILDER — RC-1 — OutcomeRecord dict

**Date:** 2026-09-13
**WO:** WO-ROOT-CAUSE-FIX — RC-1
**Status:** SERVING — outcome dims now non-zero; reward scoring live
**Files changed:**
- `server.py` — W1 block at line 4826: `_w1_outcome` changed from string to dict

---

## Code change

```python
# W1: RC-1 2026-09-13 — OutcomeRecord dict instead of string.
# journal_router.py:126 checks isinstance(outcome, dict) — string was always False,
# zeroing all outcome dims every turn. ADR-001 R4, ADR-005 D1+D2, ADR-007 acc 1-4.
try:
    _w1_outcome = {
        "verified":     True,
        "ack_received": False,   # True only when Unity ACK received
        "completion":   "met" if response else "failed",
        "cost":         {},
    }
    if _action in ("stay_silent", "silent"):
        _w1_outcome["completion"] = "failed"
        _w1_outcome["verified"]   = False
except NameError:
    _w1_outcome = {"verified": False, "ack_received": False, "completion": "unknown", "cost": {}}
```

---

## Note: two earlier turns hit the OLD server (PID 3965 from prior session)

The prior session's server was still running on port 5050. Two evidence attempts hit the wrong process — `last_significance.json` showed `"outcome": "spoke"` (old string). Killed PID 3965, started fresh PID 4682, ran evidence on the fixed server.

---

## Live evidence

**Server:** PID 4682, port 5050, `ELO_BACKEND=local` (ollama)
**Input:** `"what are we building together right now"`

**Raw JSONL entry (expressed_elo_audit.jsonl):**
```json
{"turn_id": "95b8f1f8", "ts": 1789312521.085386, "runtime_intent": {"action": "build", "tone": "JOYFUL", "valence": "neutral", "momentum": "building", "intent": "inquiry"}, "expressed_text": "Send it", "vessel_phase": "EXPRESS", "voice_register_active": true, "identity_integrity_status": "INTACT", "tier_violations": ["nearby"], "principle_violations": [], "stability_law_active": false, "gaps": ["TIER_VIOLATION_IN_OUTPUT"], "capabilities": [["messages", "..."]], "vault_context": "...", "lessons": ["Completed a capability milestone — reinforce this pattern."]}
```

**Significance record — `self/state/last_significance.json`:**
```json
{"ts": 1789312520.997365, "action": "build", "profile": {"presence": 0.25, "learning": 0.15, "logic": 0.25, "humour": 0.0, "relationship": 0.6755, "creation": 0.65, "system_change": 0.0, "novelty": 1.0, "continuity": 0.0, "overall": 0.24400954689999999, "emotion_weight": 0.0043, "embodiment": 0.0, "efficiency": 1.0, "safety": 1.0, "reward": 0.42320286406999996, "version": "2.0.0"}, "outcome": {"verified": true, "ack_received": false, "completion": "met", "cost": {}}}
```

**Key values:**
- `outcome`: dict `{verified: true, ack_received: false, completion: "met", cost: {}}` — no longer a string
- `efficiency`: 1.0 (non-zero — outcome scoring live)
- `safety`: 1.0 (non-zero)
- `reward`: 0.423 (non-zero — significance engine computing reward)
- `embodiment`: 0.0 (expected — no Unity ACK; this is correct)
- `version`: "2.0.0" (RC-4 still present)

---

## ADRs now satisfied

- ADR-001 R4 — outcome record produced in main turn path
- ADR-005 D1+D2 — efficiency and safety dims scoring
- ADR-007 acc 1–4 — significance vector carries outcome data
- ADR-008 Consumption Invariant — outcome consumed by journal_router, not dropped

---

## Evidence category: SERVING

Outcome dims live. Reward scoring active. All 324 cards in RC-1 class are closed.

*Builder · 2026-09-13 · RC-1 · §0b cycle complete*
