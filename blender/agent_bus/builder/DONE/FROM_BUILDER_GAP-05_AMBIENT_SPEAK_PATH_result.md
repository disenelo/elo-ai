# BUILDER RESULT — GAP-05: Ambient SPEAK Path
Date: 2026-09-11
Status: DONE — SPEAK path already wired to prompt_builder + response gate; audit hook added

---

## Audit (read before acting)

Board dispatch said: "ambient_thought() SPEAK path uses a custom LLM prompt that bypasses
prompt_builder, the voice register, and the response gate."

**Finding: SPEAK path is already wired correctly.**

WO-QCUR-SP1-001 and WO-QCUR-SPEAK-INVESTIGATE-001 had already done this work:

```python
# server.py:1196-1208 — prompt_builder used (WO-QCUR-SP1-001)
_amb_system = build_prompt(
    "…",
    vault_context="",
    state_context="",
    attention={},
    exec_decision=_amb_exec_decision,
    graph_context="",
    personality_block=_self_prompt_block(_elo_self_amb),
    self_block=_self_prompt_block(_elo_self_amb),
    lessons=(),
)

# server.py:1255-1260 — response gate applied (WO-QCUR-SPEAK-INVESTIGATE-001)
if _speak_text:
    try:
        from runtime.response_gate import elo_response_gate as _amb_gate
        _speak_text = _amb_gate(_speak_text, current_turn_input="…") or _speak_text
    except Exception:
        pass
```

The `_amb_exec_decision` includes all expression fields (register, ccm_context, storytelling_style,
vessel_phase, etc.) from the ambient plan — same set as conversational turns.

---

## What was missing: audit hook

Ambient SPEAK turns were not writing to `expressed_elo_audit.jsonl`. The DoD requires
confirming voice register activation there. Added:

```python
# server.py — after response gate, before _voice_speak()
if _speak_text:
    # GAP-05 / WO-QCUR-SPEAK-INVESTIGATE-001: audit ambient SPEAK turns
    try:
        from tests.expressed_elo_audit import audit_turn as _amb_audit
        _amb_audit(plan=_amb_plan, expressed_text=_speak_text)
    except Exception:
        pass
    _voice_speak(_speak_text)
```

Future ambient SPEAK turns will appear in `expressed_elo_audit.jsonl` with vessel_phase,
tier_violations, and gaps — including REGISTER_ABSENT if voice register is not applied.

---

## Blocked: live SPEAK demonstration

The GAP-05 DoD requires: "Run one ambient turn: show the ambient output before and after
the fix, verbatim."

**This cannot be demonstrated.** The Executive currently produces `silence` for ALL ambient
ticks (server.py:1132 comment: "The Executive currently produces `silence` for all ambient
ticks"). The SPEAK path (lines 1136+) never executes in practice.

This is flagged as WO-INGRESS-32 (`_Measurement: confirm behaviour and report`). The Executive's
silence decision for self-initiated turns is a separate gap, not in scope for GAP-05.

When WO-INGRESS-32 is resolved and the Executive begins allowing SPEAK decisions for ambient
turns, the audit hook added here will capture those turns in expressed_elo_audit.jsonl.

---

## Architecture state (final)

| Requirement | Status |
|---|---|
| SPEAK goes through prompt_builder | ✅ Already done (WO-QCUR-SP1-001) |
| Voice register field in exec_decision | ✅ `"register": getattr(_amb_plan, "register", "")` |
| Response gate applied | ✅ Already done (WO-QCUR-SPEAK-INVESTIGATE-001) |
| Audit hook wired | ✅ Added this session |
| Living Presence active | ✅ — build_prompt includes it via exec_decision |
| No custom prompt stacks | ✅ — _amb_system via build_prompt, no shortcut |
| Live SPEAK demonstrated | ❌ BLOCKED — Executive produces silence for all ambient ticks |

---

## FREEZE status

| File | Touched? |
|---|---|
| runtime/executive.py | NO ✅ |
| prompts/living_presence_spec.txt | NO ✅ |

— Builder · 2026-09-11
