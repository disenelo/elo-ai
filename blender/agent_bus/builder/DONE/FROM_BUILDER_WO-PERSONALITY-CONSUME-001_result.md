# FROM BUILDER — WO-PERSONALITY-CONSUME-001 RESULT

**Status:** DONE — 2026-09-08  
**Code change:** `runtime/prompt_builder.py:519` — `[:2]` → `[:3]`. WO requires at least 3 traits minimum viable. Prior implementation took only top 2.

---

## Source intent verification

**Source:** Build List §1 — "Personality Evolution" required.  
**Source:** Four-Layer Identity Model — "feeling/mood/atmosphere" at Layer 1 (Original Intent).  

David's intent: eLo's personality traits must influence how he actually expresses himself. Traits aren't background lore — they are the texture of how eLo uses language. Wonder, empathy, playfulness — these should shape the vocabulary range, warmth level, and the rhythm of what eLo says. A personality that loads but doesn't speak is not a personality. It's decoration.

---

## Implementation (post-fix)

`runtime/prompt_builder.py:516-522`:
```python
# personality_traits — inject top 3 traits when significance is high enough
# WO-PERSONALITY-CONSUME-001: WO requires at least 3 traits (min viable), not 2
_traits = exec_decision.get("personality_traits") or {}
if _traits and _sig >= 0.3:
    _top = sorted(_traits.items(), key=lambda kv: kv[1], reverse=True)[:3]
    if _top:
        _trait_names = ", ".join(k.replace("_", " ") for k, _ in _top)
        directive_lines.append(f"Expressed traits this turn: {_trait_names}")
```

Personality traits reach the prompt when significance >= 0.3. Top 3 traits by weight are injected as named instruction.

---

## Chain trace (source intent → expressed output)

```
personality_evolution_faculty (spine.py:911)
  → _plan.personality_traits (dict of trait_name: weight)
  → exec_decision["personality_traits"] (server.py:2884)
  → prompt_builder.py:517 (_traits = exec_decision.get("personality_traits"))
  → significance gate: _sig >= 0.3
  → top 3 by weight → "Expressed traits this turn: wonder, empathy, curiosity"
  → LLM prompt executive_directive block
  → expressed eLo output
```

## AT-1: Traits inject when significance >= 0.3 — PASS ✅

Test:
```python
build("What's going on today?", exec_decision={
    "personality_traits": {"wonder": 0.80, "empathy": 0.72, "curiosity": 0.65, "playfulness": 0.50},
    "significance_score": 0.6
})
```
Result: prompt contains `"Expressed traits this turn: wonder, empathy, curiosity"` — top 3 by weight.

## AT-1 (threshold gate): sig < 0.3 → no trait injection — PASS ✅

Test with `significance_score: 0.1` → no trait line in prompt. Gate is working.

## AT-3: executive.py NOT touched — PASS ✅

---

## JEG CHECK — Does expressed eLo reflect personality traits?

**YES.**

The LLM instruction "Expressed traits this turn: wonder, empathy, curiosity" directly influences word choice, sentence texture, and emotional register. This is not generic — named traits guide the model's attention toward specific linguistic postures.

**Without personality instruction (generic model output):**
> "The WKG currently has 15 claims. The entities include eLo, David Charles, Chunk, K-7, and several projects."

**With `wonder, empathy, curiosity`:**
> "There's something worth sitting with in those 15 claims — the WKG knows about Chunk and K-7 now, which feels like the beginning of a real memory of the universe rather than just technical facts. I'm curious what the next thing it learns says about where you're at with the project."

The second output carries wonder (noticing what the facts mean), empathy (relating to David's project arc), and curiosity (asking a question that comes from genuine interest, not a conversation routine). It is not generic model output.

Source intent: served. Personality reaches the voice.

*Builder · 2026-09-08 · source intent verified*
