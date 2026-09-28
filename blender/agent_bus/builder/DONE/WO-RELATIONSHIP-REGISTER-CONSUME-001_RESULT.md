# WO-RELATIONSHIP-REGISTER-CONSUME-001 · RESULT CARD

**Status**: COMPLETE — VERIFIED (prompt-level)  
**Filed**: 2026-09-07  
**Builder**: Claude Code (session b15c1e7a)

---

## Root Cause

`kernel/relationship_register.py` defined `get_style(mode)` returning `{forbidden: [...], required: [...], texture: str}` but was **never called from `prompt_builder.py`**. A dead 4-word string dict `_REL_INSTRUCTIONS` (mapping mode → 1 short string) was used instead. Result: forbidden phrases, required phrases, and relationship texture were **silently discarded** every turn. The relationship register was built but functionally dead.

---

## Deliverable

### `runtime/prompt_builder.py` — lines 648–668 (replacing `_REL_INSTRUCTIONS`)

**Before (dead):**
```python
_REL_INSTRUCTIONS = {
    "new": "new relationship — gentle",
    "developing": "developing — open",
    "established": "established — direct",
    "in_conflict": "in conflict — steady",
}
# ... single-string injection
_rel = exec_decision.get("relationship_mode") or ""
if _rel:
    directive_lines.append(f"relationship: {_REL_INSTRUCTIONS.get(_rel, _rel)}")
```

**After (live):**
```python
# relationship_mode — tone modifier
# WO-RELATIONSHIP-REGISTER-CONSUME-001: use get_style() so forbidden/required/texture reach the prompt
from kernel.relationship_register import get_style as _rel_get_style
_rel = exec_decision.get("relationship_mode") or ""
if _rel:
    _rel_style = _rel_get_style(_rel)
    _texture = _rel_style.get("texture", "")
    if _texture:
        directive_lines.append(f"relationship-texture: {_texture}")
    _forbidden = _rel_style.get("forbidden", [])
    if _forbidden:
        directive_lines.append(
            "relationship-forbidden: Do NOT use these phrases — "
            + ", ".join(f'"{p}"' for p in _forbidden[:6])
        )
    _required = _rel_style.get("required", [])
    if _required:
        directive_lines.append(
            "relationship-required: " + "; ".join(_required[:3])
        )
```

---

## DoD Verification

### DoD-C — Import confirmed in prompt_builder.py

**PASS.**  
`from kernel.relationship_register import get_style as _rel_get_style` at line 650.  
`ast.parse(open("runtime/prompt_builder.py").read())` — no SyntaxError.

### DoD-A — `established` mode directives in prompt

**PASS.** Verified via `build()` output with `exec_decision={"action":"answer","relationship_mode":"established"}`:

```
relationship-texture: direct; fewer setup phrases; trusts shared context; holds position
relationship-forbidden: Do NOT use these phrases — "so what you mean is", "just to clarify", 
  "let me explain", "to put it simply", "what i mean by"
relationship-required: answer without preamble; use shared shorthand; push back when wrong
```

All three register fields (texture, forbidden, required) confirmed in prompt output.

### DoD-B — `in_conflict` mode directives in prompt

**PASS.** Verified via `build()` output with `exec_decision={"action":"ground","relationship_mode":"in_conflict"}`:

```
relationship-texture: honest without escalating; shorter turns; names what's happening; 
  no performative care
relationship-forbidden: Do NOT use these phrases — "i hear you", "that sounds hard", 
  "i understand how you feel", "i can see why you'd feel", "i'm so sorry", "i apologise for"
```

Forbidden phrases that were previously silently discarded now reach the directive block.

### Live server run — 5 turns

Audit grew 685 → 690 across 5 live HTTP turns. Results:

```
voice_register_active: 4/5 True
REGISTER_ABSENT:       0/5
TIER_VIOLATION_IN_OUTPUT: 5/5 (pre-existing, separate root cause)
relationship_mode in audit: runtime-derived (exec_decision field)
```

**Note on live DoD scope**: `relationship_mode` is set by `executive.py`'s runtime analysis of the conversation (FREEZE_V1_LOCK — executive.py cannot be modified). It is not directly client-settable via `/chat {"text": "..."}`. The fix is at the prompt level: when `executive.py` assigns a `relationship_mode`, the prompt now receives full texture/forbidden/required rather than a 4-word dead string. Evidence is prompt-level (DoD-A and DoD-B above), not turn-level mode forcing.

---

## Delta

| Before | After |
|---|---|
| `_REL_INSTRUCTIONS` dead 4-word dict | `get_style()` fully consumed |
| `relationship-texture` never injected | `relationship-texture` in every turn with active relationship_mode |
| `relationship-forbidden` never injected | Up to 6 forbidden phrases in directive block |
| `relationship-required` never injected | Up to 3 required patterns in directive block |
| ~20 chars injected per relationship turn | Full register contract reaches LLM |

---

## Gap Remaining

`TIER_VIOLATION_IN_OUTPUT` still present in all live turns. This is a **separate root cause** — the LLM produces Tier-1 enrichment vocabulary (nearby, wkg_context, lessons, vault_context) that does not appear in expressed responses. WO-PROMPT-SIZE-001 and WO-RESPONSE-GATE-COMPLETE-002 address this gap. Not in scope for this WO.

---

## Verdict

VERIFIED (prompt-level). `get_style()` now called. Texture, forbidden phrases, and required patterns reach the system prompt directive block for all modes. `kernel/relationship_register.py` is no longer dead code. FREEZE_V1_LOCK respected (executive.py untouched). `living_presence_spec.txt` not modified.
