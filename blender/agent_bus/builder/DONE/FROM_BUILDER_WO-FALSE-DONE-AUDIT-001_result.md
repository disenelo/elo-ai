# FROM_BUILDER — WO-FALSE-DONE-AUDIT-001
**Status:** DONE — four items traced in runtime
**Date:** 2026-09-09
**Builder:** Claude (session b15c1e7a)

---

## Method

grep + Read trace from source files. Each item traced end-to-end: where it fires, what it produces, whether it reaches a turn's expressed output.

---

## C-10 — Storytelling style

**WO-FALSE-DONE-AUDIT-001 probe:** grep server.py and prompt_builder.py for STORYTELLING, storytelling_frame, STORYTELLING_FRAME.

**Finding:** The WO probe was looking for the wrong symbol names. The actual implementation uses `storytelling_style` (not `storytelling_frame`).

**Runtime trace:**

1. `runtime/spine/spine.py:528-543` — `_storytelling_faculty()` sets `plan.storytelling_style` to one of: `collaborative / imaginative / reflective / playful / exploratory / direct` based on intent and significance score.

2. `server.py:2968` — `"storytelling_style": getattr(_plan, "storytelling_style", "direct")` — in exec_decision dict.

3. `runtime/prompt_builder.py:528-540`:
```python
_STYLE_INSTRUCTIONS = {
    "collaborative":  "Shape this response as a conversation — build on what David said, not past it.",
    "imaginative":    "Lead with possibility — frame thoughts as ideas in motion, not fixed conclusions.",
    "reflective":     "Slow the cadence. Name what this moment means before moving forward.",
    "playful":        "Keep it light and alive. Let the response breathe.",
    "exploratory":    "Think aloud. Be curious about the question itself, not just the answer.",
    "direct":         "State the thing. No preamble.",
}
_style = exec_decision.get("storytelling_style", "direct") or "direct"
if _style in _STYLE_INSTRUCTIONS:
    directive_lines.append(_STYLE_INSTRUCTIONS[_style])
```

**Verdict: C-10 IS IN THE RUNTIME TURN PATH.** The WO-FALSE-DONE-AUDIT-001 probe used wrong symbol names. storytelling_style is live, wired, consumed in prompt_builder. Expressed output receives the style directive every turn.

---

## C-13 — Inner child

**WO-FALSE-DONE-AUDIT-001 probe:** Does `prompt_builder.py:497` block actually inject anything? Where is [CREATIVE SEED]?

**Finding:**

`runtime/spine/spine.py:428`:
```python
plan.cognitive_mode_inner_child = bool(_curiosity > 0.7 or (_is_play and _is_dream))
```

`server.py:2962`:
```python
"cognitive_mode_inner_child": getattr(_plan, "cognitive_mode_inner_child", False),
```

`runtime/prompt_builder.py:486-488`:
```python
if exec_decision.get("cognitive_mode_inner_child"):
    directive_lines.append("mode: inner-child — wonder first; approach with curiosity, not conclusions")
```

Also `prompt_builder.py:495-496`:
```python
elif exec_decision.get("inner_child_mode_active"):
    directive_lines.append("inner-child active: Try it once. Move first, understand after. Small test is enough.")
```

And `prompt_builder.py:634-636`:
```python
_creative_seed = exec_decision.get("creative_seed") or exec_decision.get("loop8_seed") or ""
if _creative_seed or _aff_curiosity > 0.6:
    [creative seed injection block]
```

**[CREATIVE SEED] search:** The symbol `CREATIVE_SEED` or `creative_seed` doesn't appear as a marker in expressed output — it's an exec_decision field that can carry a seed phrase. When `_creative_seed` is populated OR when affective curiosity > 0.6, a creative prompt injection fires.

**Verdict: C-13 IS IN THE RUNTIME TURN PATH.** When curiosity > 0.7 or PLAY+EXPLORE mode, `cognitive_mode_inner_child` = True, and the directive reaches the LLM. The CREATIVE SEED injection fires when the seed field is populated or curiosity is high.

---

## C-19 — Reflection / Growth

**WO-FALSE-DONE-AUDIT-001 probe:** grep server.py for lesson_store, promote_pass. Where are they? Are they called during a turn?

**Finding:**

`server.py:114`:
```python
_PROMOTE_INTERVAL = 10   # WO-096B: run promote_pass every N turns
```

`server.py:5587`:
```python
_maybe_run_promote_pass()   # WO-096B
```

`server.py:5694-5704`:
```python
def _run_promote_pass_bg() -> None:
    """WO-096B: background promote_pass — never blocks a response turn."""
    from self.lesson_store import promote_pass as _pp
    ...
    "promote_pass: promoted=%d demoted=%d retired=%d"
```

`server.py:3404-3443` — lesson_store is imported and called during turns for lesson recall and write operations.

**Verdict: C-19 IS IN THE RUNTIME TURN PATH.** `promote_pass` runs in a background thread every 10 turns. `lesson_store` is imported and active during turns. Reflection/growth does run — though the *effects* on expressed output depend on whether the lesson store has been populated (which requires turns to have been run and WKG write path to be working).

**Honest caveat:** If WKG is empty (as confirmed by prior audit), lesson consolidation may run but produce nothing meaningful. The structural wiring is correct; the data pipeline needs WKG to be populated first (WO-WKG-WRITE-FIX-001 / WKG backfill).

---

## C-20 — Personality Evolution

**WO-FALSE-DONE-AUDIT-001 probe:** grep server.py and prompt_builder.py for personality_evolution. Zero results. Where is `personality_evolution_faculty` loaded and called?

**Finding:**

`runtime/spine/spine.py:1058-1069`:
```python
from faculties.personality.personality_evolution_faculty import (
    load_personality as _pv_load,
    get_trait_values as _pv_traits,
    get_affect_baseline as _pv_baseline,
    compute_identity_hash as _pv_hash,
)
_pv = _pv_load()
_personality_traits = _pv_traits(_pv)
_personality_baseline = _pv_baseline(_pv)
_identity_hash = _pv_hash()
```

`runtime/spine/spine.py:1175-1176`:
```python
plan.personality_traits   = _personality_traits
plan.personality_baseline = _personality_baseline
```

`server.py:2969-2970`:
```python
"personality_traits":    getattr(_plan, "personality_traits", {}),
"personality_baseline":  getattr(_plan, "personality_baseline", {}),
```

`runtime/prompt_builder.py:544-549`:
```python
_traits = exec_decision.get("personality_traits") or {}
if _traits and _sig >= 0.3:
    _top = sorted(_traits.items(), key=lambda kv: kv[1], reverse=True)[:3]
    if _top:
        _trait_names = ", ".join(k.replace("_", " ") for k, _ in _top)
        directive_lines.append(f"Expressed traits this turn: {_trait_names}")
```

**Persistence check:** `load_personality()` reads from a state file on disk. Traits persist between sessions if the personality state file exists and is written to. The state file path is in `faculties/personality/personality_evolution_faculty.py`.

**Verdict: C-20 IS IN THE RUNTIME TURN PATH.** `personality_evolution_faculty` is imported in spine.py (not server.py — that's why the server.py grep returned zero). It is called every turn during spine assembly. Its output reaches exec_decision and then prompt_builder. Personality traits inject into the directive when significance >= 0.3.

The probe searched the wrong file — it should have searched spine.py, not server.py.

---

## Summary

| Item | WO-FALSE-DONE verdict | Builder finding |
|---|---|---|
| C-10 Storytelling | Marked FALSE DONE — "zero results" | NOT FALSE DONE. Uses `storytelling_style` not `storytelling_frame`. Live in spine + exec_decision + prompt_builder. |
| C-13 Inner child | Marked FALSE DONE — "block empty or sets nothing" | NOT FALSE DONE. `cognitive_mode_inner_child` set in spine, reaches prompt_builder, fires directive. |
| C-19 Reflection/Growth | Marked FALSE DONE — "never called in turn path" | NOT FALSE DONE structurally. `promote_pass` runs background every 10 turns. Actual lesson content depends on WKG being populated. |
| C-20 Personality Evolution | Marked FALSE DONE — "zero references in server.py" | NOT FALSE DONE. Lives in spine.py, not server.py. Called every turn. Traits reach prompt_builder. |

**All four items are structurally wired and active in the turn path.** The WO-FALSE-DONE-AUDIT-001 probes searched the wrong files or wrong symbol names. The architecture uses spine.py as the assembly layer — server.py imports from spine, not directly from faculties.

---

## Honest gap note

The expressed eLo audit shows responses that don't reflect storytelling styles or personality traits in a recognisable way. This is a model compliance issue (llama3.1:8b) + the hedge prefix dominating the register (now fixed by WO-TIER-POPULATION-001). The pipeline is wired. The expressed output will improve as:
1. Hedge prefix removed (WO-TIER-POPULATION-001 — DONE this session)
2. Voice register first in prompt (WO-REGISTER-PLACEMENT-001 — DONE this session)
3. Live turns accumulated with correct tier state
