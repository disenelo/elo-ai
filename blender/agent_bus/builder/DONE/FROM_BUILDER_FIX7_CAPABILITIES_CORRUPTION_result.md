# FROM BUILDER — FIX-7 — Capabilities Input Corruption

**Date:** 2026-09-13
**Status:** SERVING — capability query arrives uncorrupted
**Files changed:**
- `runtime/router/typo_engine.py` — added "have", "had", "having", "right" (and close rhymes) to `_PROTECTED`

---

## The bug (confirmed from prior JSONL)

`typo_engine.repair()` was fuzzy-matching common English words to VOCAB items at edit distance 1:

- **"have"** (4 chars, threshold=1) → edit_distance("have", "save") = 1 → repaired to "save" (confidence 0.875 > 0.80 gate)
- **"right"** (5 chars, threshold=2) → edit_distance("right", "light") = 1 → repaired to "light" (confidence 0.90 > 0.80 gate)

Both "save" and "light" are in `_VOCAB`. Neither "have" nor "right" was in `_PROTECTED`. The spine gate at `repaired["confidence"] >= 0.80` accepted both "repairs" and overwrote `plan.meaning`.

Prior JSONL evidence (TIER_PIPELINE_FIX cycle):
`capabilities: [["dark_mode", "what are you capable of light now"]]` — "right" → "light"

Prior JSONL evidence (LESSONS_FOCAL_THREAD cycle):
`capabilities: [["vault_write", "what save you learned from completing things with me"]]` — "have" → "save"

---

## Code change — typo_engine.py

```python
# Added to _PROTECTED frozenset:
"have", "had", "having",
"right", "might", "light", "sight", "tight", "night",
```

`_PROTECTED` words are never subject to `_fuzzy_match`. The input word is passed through unchanged if it appears in `_PROTECTED`, regardless of edit distance to any VOCAB item.

---

## Live evidence

**Server:** PID 1933, port 5050, `ELO_BACKEND=local`

**Verbatim input:** `"what have you learned from completing things with me"`

**Raw JSONL entry:**
```json
{"turn_id": "166b5188", "ts": 1789309327.887052, "runtime_intent": {"action": "answer", "tone": "DIRECT", "valence": "neutral", "momentum": "stable", "intent": "inquiry"}, "expressed_text": "I'm not certain, but — Finishing things now.", "vessel_phase": "EXPRESS", "voice_register_active": true, "identity_integrity_status": "INTACT", "tier_violations": ["nearby"], "principle_violations": [], "stability_law_active": false, "gaps": ["TIER_VIOLATION_IN_OUTPUT"], "capabilities": [["timer", "what have you learned from completing things with me"]], "vault_context": "[RELATIONSHIP]\n**David**: Founder of DISENELO. The person eLo exists with.\n\n[IDENTITY]\n**eLo Digital Form**: I exist in digital form as a floating 3D avatar on David's desktop. The app is called DesktopBuddy. I am a transparent window — no frame, no chrome — just me, sitting on his screen while he works.\n**Point of View**: eLo has opinions. Not performed opinions — actual stances that emerge from what it has observed, built, and thought about.\n**Personality Skeleton**: Observed behavioural patte", "lessons": ["Completed a capability milestone — reinforce this pattern."]}
```

**Key field — before fix:**
`"capabilities": [["vault_write", "what save you learned from completing things with me"]]`

**Key field — after fix:**
`"capabilities": [["timer", "what have you learned from completing things with me"]]`

"have" is preserved. The query reaching the capability router is now verbatim input.

---

## Secondary observation (not this cycle)

The capability selected is "timer" — not contextually relevant to a reflective question about learning. That's a separate Executive routing issue, not the corruption bug. The query arrives clean; the wrong cap was selected is a different problem.

---

## Evidence category: SERVING

Input arrives uncorrupted at the capability router. "have" preserved. Prior "save" substitution is gone.

*Builder · 2026-09-13 · FIX-7 · §0b cycle complete*
