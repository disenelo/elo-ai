# FROM BUILDER → BOARD — WO-CCM-VENTING-BOUNDARY-001: CCM Venting Boundary Tighten (T2)
**Date:** 2026-09-14
**WO:** FROM_ARCHITECT_2026-09-14_WO-CCM-VENTING-BOUNDARY-001.md
**Authority:** David L3 — 2026-09-14

---

## Diagnosis (required before fix per WO)

**Board hypothesis: "None of the `_VENTING_PATTERNS` are present in the input."**

Builder traced the exact match:

```python
t = "what's the weirdest thing you've thought about today"
"ugh" in t  →  True
```

**Root cause:** `"ugh"` is a substring of `"thought"` — `"tho-ugh-t"`. The substring check `if p in t` for the pattern `"ugh"` fires because `"thought"` contains the character sequence u-g-h. This caused `classify_social_intent()` to return `"venting"` → `classify_tier()` returned `TIER1, intent=venting` → `backend=social_reflex(TIER1)` in the audit.

**Same bug in ccm_enricher.py:** `_detect_emotion()` also used `any(p in tl for p in patterns)` with `"ugh"` in the frustrated signals, producing `emotion="frustrated"` for any input containing "thought" (or "through", "roughly", etc.).

---

## What was built

**Fix 1 — `runtime/social_reflex.py`:**

Added `_VENTING_EXCLUSION` tuple (curiosity/positive/question markers that suppress venting classification):
```python
_VENTING_EXCLUSION = (
    "weirdest", "funniest", "wildest", "craziest", "coolest", "strangest",
    "have you ever", "do you ever", "what do you think", "what's the",
    "tell me what", "i've been thinking", "i was thinking",
    "laughing", "haha", "lmao", "lol", "amazing", "brilliant", "love it", "love this",
    "what would", "what if", "what's your", "how do you", "could you",
)
```

Updated venting match in `classify_social_intent()`:
```python
for p in _VENTING_PATTERNS:
    # SHORT PATTERNS (≤5 chars): require word-boundary match to prevent
    # "ugh" matching inside "thought", "through", "roughly", etc.
    if len(p) <= 5:
        matched = bool(re.search(r"\b" + re.escape(p) + r"\b", t))
    else:
        matched = p in t
    if matched:
        # Exclusion check: suppress if any curiosity/positive/question marker present
        if any(exc in t for exc in _VENTING_EXCLUSION):
            return None
        return "venting"
```

**Fix 2 — `faculties/ccm/ccm_enricher.py`:**

Applied the same word-boundary guard to `_detect_emotion()`:
```python
for p in patterns:
    if len(p) <= 5:
        if re.search(r"\b" + re.escape(p) + r"\b", tl):
            return emotion
    elif p in tl:
        return emotion
```

---

## Evidence

**A. Diagnosis — exact match confirmed:**
```python
"ugh" in "what's the weirdest thing you've thought about today"  →  True
# "tho-ugh-t" — substring match, not a frustration signal
```

**B. T2 input after fix:**
```python
classify_social_intent("what's the weirdest thing you've thought about today")
→ None  (expect: not venting) ✓

classify_tier("what's the weirdest thing you've thought about today")
→ tier='TIER2+', intent=None ✓
```

**C. Venting still works:**
```python
classify_social_intent("ugh this is taking forever")
→ 'venting' ✓  (word-boundary match, no exclusion)
```

**"ugh" alone / start of sentence:**
```python
classify_social_intent("ugh")
→ 'venting' ✓
```

**Thought/memory input — no false positive:**
```python
classify_social_intent("i've thought about this a lot")
→ None ✓
```

**Longer genuine venting:**
```python
classify_social_intent("this is so frustrating i give up")
→ 'venting' ✓
```

**Positive exclusion override:**
```python
classify_social_intent("can't deal with how amazing this is")
→ None ✓  (exclusion: "amazing")
```

**CCM enricher after fix:**
```python
_detect_emotion("what's the weirdest thing you've thought about today")
→ None ✓  (previously: "frustrated" due to "ugh" in "thought")
```

---

## Gap

D. Live JSONL entry with correct intent for curiosity question — pending David L3 live test.

---

## DoD

- [x] Root cause diagnosed: "ugh" substring match in "thought"
- [x] `social_reflex.py`: short patterns (≤5 chars) use word-boundary match
- [x] `social_reflex.py`: `_VENTING_EXCLUSION` added — curiosity/positive/question markers suppress venting
- [x] `ccm_enricher.py`: `_detect_emotion()` — same word-boundary guard applied
- [x] `classify_social_intent()` returns None for T2 input ✓
- [x] Genuine venting (`"ugh this is taking forever"`) still returns `"venting"` ✓
- [x] `"thought"`, `"through"` etc. no longer false-positive on `"ugh"` ✓
- [ ] Live JSONL evidence — David L3 pending

---

*Builder · 2026-09-14*
