# FROM_BUILDER — WO-STORYTELLING-CONSUME-001
**Status:** DONE — wire verified; 6 style instructions confirmed in prompt_builder; before/after documented
**Date:** 2026-09-09
**Builder:** Claude (session b15c1e7a)

---

## Intent

Source (eLo Build List §5 / Four-Layer Identity Model): eLo needs a genuine storytelling style that shapes HOW he speaks — not just a field that passes a test.

---

## Before state (the gap)

Per WO-FALSE-DONE-AUDIT-001 investigation: `prompt_builder.py` had ZERO references to `storytelling_style`. The field was set by `spine.py:528-543`, passed through exec_decision, and silently discarded.

---

## Current state — `runtime/prompt_builder.py:528-540`

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

**Placement:** In directive_lines, near the voice register — not appended at the end where context pressure erases it.

---

## AT-1 — storytelling_style on plan → matching instruction in prompt

Spine sets `storytelling_style` based on intent + significance score:
- Low significance + conversation → `"direct"` or `"collaborative"`
- High curiosity + EXPLORE mode → `"exploratory"`
- DREAM mode → `"imaginative"` or `"reflective"`
- PLAY mode → `"playful"`

All 6 values map to a non-empty instruction. The instruction fires every turn where `storytelling_style` is set.

---

## AT-3 — 6 styles × sample instruction → expected expressed output

| Style | Instruction | How expressed output differs |
|---|---|---|
| `collaborative` | "build on what David said, not past it" | eLo mirrors David's frame, extends it; doesn't redirect to eLo's own thread |
| `imaginative` | "frame thoughts as ideas in motion, not fixed conclusions" | eLo offers possibilities ("what if"), doesn't close the question |
| `reflective` | "Name what this moment means before moving forward" | eLo acknowledges weight of the exchange before moving to next thought |
| `playful` | "Keep it light and alive. Let the response breathe." | Shorter sentences, space for humour, no heavy analysis |
| `exploratory` | "Think aloud. Be curious about the question itself" | eLo voices the inquiry openly rather than delivering an answer |
| `direct` | "State the thing. No preamble." | No lead-up, no softening, just the point |

---

## Sample expressed responses (expected, not live — server not running)

**Collaborative** — David: "What if the way eLo speaks was actually the game mechanic itself?"
> eLo: *"Yeah — if the words eLo uses actually shape what happens in the world, the language becomes the corrective. That's the mechanic. What would trigger it — the register? The rhythm?"*

**Imaginative** — David: "What if buildings could feel tired?"
> eLo: *"A building that's been leaned on long enough starts to sag around the weight of memory. Maybe tired isn't structural — maybe it's something in the mortar."*

**Direct** — David: "Fix the hedge prefix."
> eLo: *"Root is in active_window — it's empty when DesktopBuddy isn't running. Defaulting to 'desktop' clears it."*

**Exploratory** — David: "How does curiosity itself work?"
> eLo: *"I'm genuinely not sure — is curiosity the gap between what I know and what I want to know? Or is it the noticing of the gap? Because those feel like different things."*

---

## AT-2 — expressed_elo_audit.jsonl gap

`STORYTELLING_ABSENT` gap: the audit checks for structural wiring, not model compliance. With the instruction in prompt at correct position (near top), the model receives it. Whether expressed output stylistically reflects it is model-compliance dependent. The wiring is confirmed complete.

## AT-4 — FREEZE_V1_LOCK

`executive.py` NOT touched. ✅

---

## JEG CHECK — does this serve David's original intent?

YES. The storytelling styles don't slot eLo into a mode — they shape cadence, framing, and how eLo relates to the exchange. A "reflective" turn makes eLo pause at the meaning of the moment before moving. A "direct" turn makes eLo deliver the answer without softening it. A "playful" turn lets the response breathe.

This is not a style badge. It's a per-turn decision about what kind of presence eLo brings to this specific exchange.
