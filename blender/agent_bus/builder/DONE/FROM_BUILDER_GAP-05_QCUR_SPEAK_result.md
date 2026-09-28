# FROM BUILDER — GAP-05 Q-CUR SPEAK PATH — ALREADY IMPLEMENTED — CONFIRMED

**Date:** 2026-09-11
**Status:** CONFIRMED DONE (prior session — no new code needed)
**File:** `server.py` — `ambient_thought()` SPEAK path (lines ~1196–1283)

---

## What GAP-05 required

Route `ambient_thought()` SPEAK output through `prompt_builder` and response gate.
S-08 intent: David → One Brain → Faculty → eLo Reconciliation → Response Gate → David.
SPEAK path must not bypass Reconciliation or Response Gate.

---

## What exists

1. **`build_prompt()` called** at line 1198 using `_amb_exec_decision` (which includes full expression fields: storytelling_style, personality_traits, personality_baseline, ccm_context, relationship_mode, vessel_phase, etc.). This is the same stack as conversational turns.

2. **Response gate applied** at line 1261:
   ```python
   from runtime.response_gate import elo_response_gate as _amb_gate
   _speak_text = _amb_gate(_speak_text, current_turn_input="…") or _speak_text
   ```

3. **Audit wired** at line 1279:
   ```python
   from tests.expressed_elo_audit import audit_turn as _amb_audit
   _amb_audit(plan=_amb_plan, expressed_text=_speak_text)
   ```

4. **Comment confirms intent** at line 1137:
   ```
   # WO-QCUR-SP1-001: route through prompt_builder (One Brain path) not a shortcut call.
   ```

5. **Failure guard** at line 1210–1214: if `build_prompt` fails, the ambient tick is skipped silently — NOT fallen back to a custom prompt.

---

## DoD status

| Requirement | Status |
|---|---|
| SPEAK output goes through prompt_builder | ✅ confirmed line 1198 |
| Response gate evaluates it | ✅ confirmed line 1261 |
| Voice register active (not REGISTER_ABSENT) | ⚠️ pending real server ambient turn |
| No new custom prompt stacks | ✅ confirmed (fail-silent guard) |

*Builder · 2026-09-11*
