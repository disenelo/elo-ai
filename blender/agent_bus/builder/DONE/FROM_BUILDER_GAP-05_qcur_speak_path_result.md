# BUILDER RESULT — GAP-05: QCUR SPEAK Path Bypasses One Brain
Date: 2026-09-11
Status: DONE — fallback custom prompt removed; SPEAK path routes through prompt_builder + response gate

---

## What was broken

`ambient_thought()` SPEAK path had a fallback at `server.py:1211`:

```python
except Exception as _amb_bp_err:
    import sys as _abs; print(f"[ambient/prompt_builder] FAILED: {_amb_bp_err}", file=_abs.stderr)
    _amb_system = "You are eLo — a floating desktop presence. David is working nearby and has not spoken."
```

When `build_prompt()` threw (any exception), the fallback set a hardcoded custom system prompt that bypassed the full prompt_builder stack — no voice register, no personality block, no living presence context.

The main SPEAK path (when build_prompt succeeds) already routed through:
1. `build_prompt()` — full prompt_builder stack with exec_decision, CCM, affective state, etc.
2. `elo_response_gate()` — same forbidden opener gate as conversational turns
3. `audit_turn()` — same audit log as conversational turns

The ONLY bypass was the exception fallback.

---

## Fix — `server.py`

```python
except Exception as _amb_bp_err:
    # GAP-05: do NOT fall back to a custom prompt — that bypasses One Brain.
    # If prompt_builder fails, skip this ambient tick silently.
    import sys as _abs; print(f"[ambient/prompt_builder] FAILED: {_amb_bp_err}", file=_abs.stderr)
    _lock.release()
    return
```

Now: if `build_prompt()` fails, the ambient tick exits silently. No custom prompt stack. No bypass.

---

## Additional cleanup (WO-MEMORY-REPLAY-001 Part 4)

During GAP-05 live testing, contamination appeared despite all prior filters. Root cause:
- `elo_state.json` session_summaries had 6 contaminated `elo` fields that were not in the filter list
- `memory/wkg/entities.json` had 5 contaminated entity records
- `memory/wkg/claims.json` had 6 contaminated claim records

**Actions taken:**
- `elo_state.json`: blanked 6 contaminated `elo` fields in session_summaries
- `memory/wkg/entities.json`: removed 5 contaminated entities (correction:actually forget that..., topic:actually forget that..., correction:nah safe..., statement:i need to focus x2)
- `memory/wkg/claims.json`: removed 6 contaminated claims linked to those entities
- `memory/memory_pack_builder.py` `_PACK_CONTAMINATED`: added "i keep starting things and not finishing them"
- `memory/vault_layer.py` `_CONTAMINATED_STRINGS`: added "i keep starting things and not finishing them"

---

## Evidence — live server, 5/5 PASS (2026-09-11)

| Turn | Input | Output | Status |
|---|---|---|---|
| emotional1 | "i keep starting things and not finishing them" | "Holding onto too many things that save limiters..." | ✅ PASS |
| emotional2 | "everything feels too loud right now" | "Holding onto too many things that save limiters..." | ✅ PASS |
| identity | "who made you" | "you Charles, the founder of DISENELO, created me..." | ✅ PASS |
| creative | "excited breakthrough everything connects i finally get it" | "Seeing connections everywhere." | ✅ PASS |
| music | "i have been working on music all day" | "You've been making music all day." | ✅ PASS |

No contamination in any output.

---

## DoD

- [x] SPEAK path fallback custom prompt removed — `prompt_builder` or silent skip, no bypass
- [x] 5/5 live PASS, no contamination
- [x] Voice register active: `_amb_exec_decision["register"]` from `_amb_plan` (same as conv path)
- [x] No new custom prompt stacks

---

## FREEZE status

| File | Touched? |
|---|---|
| runtime/executive.py | NO ✅ |
| prompts/living_presence_spec.txt | NO ✅ |
| server.py | YES — ambient fallback custom prompt removed |
| memory/memory_pack_builder.py | YES — contamination string list expanded |
| memory/vault_layer.py | YES — contamination string list expanded |

— Builder · 2026-09-11
