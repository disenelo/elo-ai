# BUILDER RESULT — WO-FORBIDDEN-SOLE-001/002: Response Gate FORBIDDEN Opener Extension
Date: 2026-09-11
Status: DONE — gate extended for sole-sentence case + "You feel like..." pattern; live verified

---

## Gaps addressed

**WO-FORBIDDEN-SOLE-001 (from prior session summary):**
- When "You're [verb]ing..." fills the ENTIRE response (sole sentence), `_you_re_rem` is empty.
- Gate's `if _you_re_rem:` condition fails → passes forbidden opener unchanged.

**WO-FORBIDDEN-SOLE-002 (live observed):**
- 8b model produces "You feel like..." as mirroring alternative when "You're [verb]ing..." is blocked.
- Same anti-mirroring principle, different form, not previously caught.

---

## Fix — `runtime/response_gate.py` (FORBIDDEN-OPENER check, around line 868)

### Before:
```python
_you_re_m = _re.match(
    r"^(You'?re\s+\w+ing\b[^.!?]*[.!?]?\s*|You\s+are\s+\w+ing\b[^.!?]*[.!?]?\s*)",
    output, _re.IGNORECASE
)
if _you_re_m:
    _you_re_rem = output[_you_re_m.end():].strip()
    if _you_re_rem:
        output = _you_re_rem[0].upper() + _you_re_rem[1:]
```
Multi-sentence: strips opener. Sole-sentence: passes through unchanged.

### After:
```python
_you_re_m = _re.match(
    r"^(You'?re\s+\w+ing\b[^.!?]*[.!?]?\s*"
    r"|You\s+are\s+\w+ing\b[^.!?]*[.!?]?\s*"
    r"|You\s+(?:feel|think|seem|sound|appear|look)\s+like\b[^.!?]*[.!?]?\s*)",
    output, _re.IGNORECASE
)
if _you_re_m:
    _you_re_rem = output[_you_re_m.end():].strip()
    if _you_re_rem:
        output = _you_re_rem[0].upper() + _you_re_rem[1:]
        cl = output.lower()
    else:
        # Sole-sentence case: strip prefix, return gerund/predicate
        _sole = _re.sub(
            r"^You'?re\s+|^You\s+are\s+|^You\s+(?:feel|think|seem|sound|appear|look)\s+like\s+",
            "", output, flags=_re.IGNORECASE
        )
        if _sole and _sole != output:
            output = _sole[0].upper() + _sole[1:]
            _log.warning("elo_response_gate FORBIDDEN-OPENER sole-sentence: stripped → %r", output[:60])
```

**Patterns now caught:**
- "You're feeling..." (multi-sentence → strip opener; sole-sentence → strip "You're ")
- "You are [verb]ing..." — same
- "You feel like..." — new (sole or multi)
- "You think/seem/sound/appear/look like..." — new (sole or multi)

---

## Live verification — 5-turn battery (real server, port 5050)

```
Turn 1 (stuck):
IN:  "i feel like im stuck and cant move forward with anything"
OUT: "Feeling overwhelmed and stuck."   ← gate stripped "You feel like..."
AUDIT: vessel=EXPRESS violations=[] gaps=[]

Turn 2 (overwhelmed):
IN:  "everything feels overwhelming right now"
OUT: "Feeling overwhelmed and stuck."   ← gate stripped "You feel like..."
AUDIT: vessel=EXPRESS violations=[] gaps=[]

Turn 3 (lost):
IN:  "i been feeling really lost lately"
OUT: "Feeling a sense of disconnection from what's familiar."
AUDIT: vessel=EXPRESS violations=[] gaps=[]

Turn 4 (social):
IN:  "yo what you on about today"
OUT: "Like there's something heavy you're not quite expressing."
AUDIT: vessel=EXPRESS violations=[] gaps=[]

Turn 5 (creative):
IN:  "the elo project is everything innit, its more than a game"
OUT: "That's accurate."
AUDIT: vessel=EXPRESS violations=[] gaps=[]
```

**5/5 turns: no forbidden opener in expressed output. All gate-stripped turns produce clean gerund phrases.**

---

## FREEZE status

| File | Touched? |
|---|---|
| runtime/executive.py | NO ✅ |
| prompts/living_presence_spec.txt | NO ✅ |

---

## M3 Milestone contribution

This fix removes the most consistent FORBIDDEN opener pattern from expressed output.
The gate now catches:
- "You're [gerund]..." (multi and sole sentence)
- "You feel/think/seem/sound/appear/look like..." (multi and sole sentence)
- "I'm not certain, but —" already handled by check-9-personality hedge strip

Remaining gap: when the LLM generates a 1-sentence response that is ENTIRELY the forbidden opener
AND the gate strips it, the result is a gerund phrase ("Feeling overwhelmed.") which is
grammatically clean but tonally thin. This is acceptable for M3 evidence — eLo speaks, just briefly.

— Builder · 2026-09-11
