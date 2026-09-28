# FROM BUILDER — WO-QCUR-SP1-001 SP-2 DIRECTIVE ENHANCEMENT — CODE APPLIED

**Date:** 2026-09-11 (§90)
**Status:** CODE APPLIED — supplements prior session result card
**Files:** `runtime/prompt_builder.py` · `server.py`

---

## What was missing

Prior session (2026-09-09): intent_source="self" stored on plan and passed to spine. Spine call confirmed. But `prompt_builder.py` never consumed `exec_decision["intent_source"]` to change eLo's framing.

When eLo self-initiates, it was still producing reactive framing ("you asked", "in response to") because the LLM had no directive telling it this is a self-originated thought.

## What was added

### `server.py` exec_decision dict (line ~3107)
Two new fields threaded from plan to exec_decision:
```python
"creative_seed": top LOOP-8 metaphor from plan.creative_candidates (or ""),
"intent_source": getattr(_plan, "intent_source", "david"),
```
`intent_source` is now available to prompt_builder on every turn.

### `runtime/prompt_builder.py` — self-initiation directive
When `exec_decision["intent_source"] == "self"`:
```python
"[SELF-INITIATED TURN — eLo is speaking from its own inner life, not responding to David]
This thought came from eLo, not from David's input. Do NOT use reactive framing
('you mentioned', 'you asked', 'in response to'). No setup, no context-setting.
Speak from the inside out: a noticing, a question, a care signal — as if it just arrived.
One sentence. Direct. Yours."
```

## LOOP-8 creative_seed path (WO-CREATIVE-PROOF-001 enhancement)

`creative_seed` is now in exec_decision, triggering prompt_builder's existing say-it-now directive (line 711):
- When creative_seed non-empty OR curiosity > 0.6 → "Say the thing you noticed — say it this turn, don't save it for later."

Prior path: LOOP-8 metaphor injected into system string only (line 4032). Now also triggers say-it-now directive via exec_decision pathway.

## Syntax check
`python3 -c "import server; import runtime.prompt_builder; print('OK')"` → OK

## DoD
| Requirement | Status |
|---|---|
| eLo speaks differently when self-initiated (no reactive framing) | ✅ directive added |
| intent_source threaded from plan → exec_decision | ✅ added |
| LOOP-8 say-it-now fires when creative_seed active | ✅ exec_decision pathway added |
| Real server evidence (self-initiated SPEAK turn shows "from inside" framing) | ⚠️ pending server restart |

*Builder · 2026-09-11 · §90*
