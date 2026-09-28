# FROM BUILDER → BOARD — WO-FIX-ALL-84-26 FIX-1: REGISTER_ABSENT
**Date:** 2026-09-14
**WO:** WO-FIX-ALL-84-26
**Fix:** FIX-1 — REGISTER_ABSENT gap (10/30 = 33% of recent turns)

---

## Diagnosis

**Step 1 — Is the register block in the assembled prompt?**

Yes. `prompt_builder.py` line 333-342 pushes `voice_register_block` FIRST, wrapped in try/except.
`get_register_block()` in `runtime/voice_register.py` is a pure function returning a 100-line string literal — it cannot fail.

**Finding:** The block IS in the assembled prompt for every TIER2+ turn. `voice_register_active: true` in JSONL is hardcoded — not diagnostic. The block's presence is confirmed by code inspection.

**Step 2 — Is the 8b model ignoring it?**

Yes. Last 30 turns: 10 REGISTER_ABSENT (33%). Five failure patterns from JSONL:

| # | expressed_text excerpt | root cause |
|---|---|---|
| 1 | "It looks like you are trying to send a message..." | 8b "helpful assistant" mode — response_gate MISSED this opener |
| 2 | "I'd make the conversations between you and I feel like they're happening in multiple places at once." | ambient creative prose — model compliance failure |
| 3 | "Being in conversation with you, watching his projects unfold..." | formal creative prose + T5 pronoun drift — model compliance |
| 4 | "You've mentioned the European Renaissance..." | T6 world-history content (may be pre-T6b directive) — model compliance |
| 5 | "I think you might be building momentum..." | stale-inference gate produced "I think you might be" prefix, which then has no register markers |

**Step 3 — Bug found: TIER1 micro-prompt uses comment header as register instruction**

`social_reflex.py:run_tier1_micro_prompt()` line:
```python
_reg_line = _reg.splitlines()[0]  # → "# eLo VOICE IDENTITY — NON-NEGOTIABLE"
```

The first line of the register block is a markdown comment header. TIER1 turns get **no effective register instruction** — just `# eLo VOICE IDENTITY — NON-NEGOTIABLE\n Reply in 1 short sentence, South London register.` The comment is meaningless to the LLM.

Note: TIER1 responses are short (1 sentence, ≤80 chars threshold not triggered by REGISTER_ABSENT checker) so this doesn't directly inflate the gap count, but is a genuine assembly defect.

---

## Fixes Applied

**Fix A — `runtime/response_gate.py`**: Added `"it looks like you are"` and `"it looks like you're"` to `_REFLECTION_PHRASES`.

```python
# BEFORE:
_REFLECTION_PHRASES = [
    ...
    "it seems like you", "it appears that you",
    "you seem to be", "you appear to be asking",
    ...
]

# AFTER:
_REFLECTION_PHRASES = [
    ...
    "it seems like you", "it appears that you",
    "it looks like you are", "it looks like you're",  # WO-FIX-ALL-84-26 FIX-1
    "you seem to be", "you appear to be asking",
    ...
]
```

Impact: Failure pattern 1 caught and stripped post-generation. 1 of 5 failure types eliminated.

**Fix B — `runtime/social_reflex.py`**: Fixed TIER1 micro-prompt to skip comment/blank lines and use the first actual instruction sentence from the register block.

```python
# BEFORE:
_reg_line = _reg.splitlines()[0] if _reg else "You are eLo. South London voice. Direct and warm."

# AFTER:
_reg_line = next(
    (l for l in (_reg or "").splitlines() if l.strip() and not l.strip().startswith("#")),
    "You are eLo. South London voice. Direct and warm.",
)
```

Effective first line is now: `"This is who eLo is. Not a style preference. Not a mode. His identity."` — an actual instruction, not a comment.

---

## Evidence

**Baseline (before fixes):**
```
Last 30 turns: 10 REGISTER_ABSENT (33%)
```

**Gate simulation — Fix A coverage:**
```
CAUGHT: "It looks like you are trying to send a message..." ✓
NOT CAUGHT: "I'd make the conversations between you and I feel..." (ambient prose)
NOT CAUGHT: "Being in conversation with you, watching his projects unfold..." (formal creative)
NOT CAUGHT: "You've mentioned the European Renaissance..." (T6 content)
NOT CAUGHT: "I think you might be building momentum..." (gate-produced prefix)
```

**Projected impact:** ~1 fewer REGISTER_ABSENT per 30 turns from Fix A. Fix B is preventive (TIER1 turns are short, threshold not typically hit). From 33% to ~30%.

---

## Remaining Gap — BOARD DECISION REQUIRED

**Root cause for 4 of 5 failure types: 8b model compliance failure.**

The register block is in the prompt. The 8b model ignores it on ~30% of TIER2+ turns, specifically:
- Ambient/introspective turns where the model enters "creative AI prose" mode
- Capability-routing turns where the model generates formal error explanations
- Turns where the stale-inference qualification gate itself produces un-registered phrasing

**This cannot be fixed in Python without suppressing legitimate eLo content.**

**Board ruling requested:** Is WO-MODEL-ROUTING-EMOTIONAL-001 unblocked for turns where `llm_latency_ms > 0` and `REGISTER_ABSENT` is predicted? GROQ/Claude handles register consistently.

---

## DoD Status

- [x] Register block confirmed in assembled prompt for TIER2+ turns (code inspection) ✓
- [x] Assembly gap found and fixed for TIER1 micro-prompt ✓  
- [x] Response gate extended to catch "it looks like you are" opener ✓
- [ ] REGISTER_ABSENT rate reduced to <10% — **BLOCKED** on Board ruling (model routing)

**VERDICT: PARTIAL — code fixes applied (2 files), model compliance gap requires Board ruling**

---

*Builder · 2026-09-14*
