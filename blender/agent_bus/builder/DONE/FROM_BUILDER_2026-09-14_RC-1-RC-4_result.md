# FROM BUILDER → BOARD — WO-ROOT-CAUSE-FIX: RC-1 + RC-4 Live Evidence
**Date:** 2026-09-14
**WO:** FROM_ARCHITECT_2026-09-13_WO-ROOT-CAUSE-FIX.md
**Authority:** David L3 — 2026-09-13

---

## Live server turn

**Input:** "what if we built the vinyl art piece before the Kickstarter so we have something physical to photograph for the campaign?"
**turn_id:** 1dec57c6
**ts:** 1789406027.840578
**backend:** ollama(stream)
**mode:** answer
**expressed response:** "Jumping ahead, yeah."

---

## RC-4 evidence — version field in significance vector

Verbatim from `self/state/last_significance.json` after turn `1dec57c6`:

```json
{
  "ts": 1789406027.764826,
  "action": "answer",
  "profile": {
    "presence": 0.25,
    "learning": 0.4,
    "logic": 0.37,
    "humour": 0.0,
    "relationship": 0.6755,
    "creation": 0.1,
    "system_change": 0.0,
    "novelty": 0.7,
    "continuity": 0.0,
    "overall": 0.1953207529,
    "emotion_weight": 0.0043,
    "embodiment": 0.0,
    "efficiency": 1.0,
    "safety": 1.0,
    "reward": 0.40859622587,
    "version": "2.0.0"
  },
  "outcome": {
    "verified": true,
    "ack_received": false,
    "completion": "met",
    "cost": {}
  }
}
```

`"version": "2.0.0"` present in profile dict. ADR-007 §3 satisfied. ✓

---

## RC-1 evidence — OutcomeRecord dict (not string)

Same record shows `"outcome": {"verified": true, "ack_received": false, "completion": "met", "cost": {}}`.

This is a proper dict, not a string. `journal_router.py:126`: `isinstance(outcome, dict) == True`.
All significance dimensions receive the outcome for scoring. `efficiency: 1.0` and `safety: 1.0` confirm non-zero downstream scoring. ✓

Code location: `server.py:4919` — "W1: RC-1 2026-09-13 — OutcomeRecord dict instead of string."

---

## Audit JSONL entry — turn 1dec57c6

```
turn_id: 1dec57c6
ts: 1789406027.840578
runtime_intent: {'action': 'answer', 'tone': 'DIRECT', 'valence': 'neutral', 'momentum': 'stable'}
tier_violations: []
voice_register_active: True
vault_context_len: 1500
vault_context[:100]: '[RELATIONSHIP]\n**David**: Founder of DISENELO. The person eLo exists with.\n\n[IDENTITY]\n**eLo Digital'
```

`vault_context_len: 1500` — full identity block visible. vault_context cap 500→1500 confirmed active. ✓

---

## RC-2 status (code applied, evidence pending)

`runtime/cognitive_snapshot.py:132-145`: RC-2 comment + `UnifiedCognitiveState = CognitiveSnapshot` alias. The Executive receives one object. Live turn confirming the Executive received one unified state (not two separate objects) would require server instrumentation beyond what's in the audit log. Code-level evidence: `assemble_cognitive_state()` is not called in the fast path when `CognitiveSnapshot` is used.

---

## RC-3 status (code applied, evidence pending)

`runtime/executive.py:432`: `_adv = attention_model.get("learning_advice") or {}`. Consuming lesson advice and applying it to action selection. Live evidence of a lesson influencing expressed output requires a turn where a prior lesson is relevant and changes the response — non-deterministic on cold turns.

---

## RC-5 status (non-deterministic)

Ambient SPEAK through spine requires ambient engine to fire SPEAK decision — non-deterministic. Evidence will appear naturally when ambient engine fires with SPEAK allowed.

---

*Builder · 2026-09-14*
