# FROM BUILDER — CAP-ROUTER-FIX — Executive Capability Routing

**Date:** 2026-09-13
**Status:** SERVING — capabilities: [] for reflective input; no false routing
**Files changed:**
- `runtime/spine/spine.py` — `_CAP_STOPWORDS` extended with pronouns and auxiliary verbs

---

## The bug (confirmed by trace)

`_capability_faculty` scores capabilities by checking content words (after stopword stripping) of each verb phrase against the input. `_CAP_STOPWORDS` was missing common pronouns and auxiliary verbs. Two false positives on "what have you learned from completing things with me":

**timer — "remind me in":**
- content_words = ["remind", "me"] (after removing "in" stopword)
- "me" not in stopwords → matched word boundary in "...with **me**"
- score = 1

**search — "tell me about":**
- content_words = ["tell", "me", "about"] 
- "me" not in stopwords → matched "...with **me**"
- score = 1

**clipboard — "what have i copied":**
- After adding "me" → content_words = ["have", "copied"]
- "have" not in stopwords → matched "what **have** you learned..."
- score = 1

All three scored 1 via pronoun/auxiliary leak, not genuine verb match. Timer was selected first (sort stable, insertion order).

---

## Code change — spine.py `_CAP_STOPWORDS`

```python
# BEFORE:
_CAP_STOPWORDS = frozenset({
    "what", "is", "are", "how", "do", "you", "it", "the", "a", "an",
    "in", "on", "at", "for", "to", "of", "and", "or", "my",
})

# AFTER:
_CAP_STOPWORDS = frozenset({
    "what", "is", "are", "how", "do", "you", "it", "the", "a", "an",
    "in", "on", "at", "for", "to", "of", "and", "or", "my",
    "me", "him", "her", "us", "them", "we", "i",
    # auxiliary verbs — not capability signals
    "have", "has", "had", "did", "does", "will", "would", "should", "could",
    "been", "was", "were",
})
```

---

## Live evidence

**Server:** PID 2237, port 5050, `ELO_BACKEND=local`

**Verbatim input:** `"what have you learned from completing things with me"`

**Raw JSONL entry:**
```json
{"turn_id": "9e6b1ecc", "ts": 1789309782.258237, "runtime_intent": {"action": "answer", "tone": "DIRECT", "valence": "neutral", "momentum": "stable", "intent": "inquiry"}, "expressed_text": "I'm not certain, but — Finishing things now.", "vessel_phase": "EXPRESS", "voice_register_active": true, "identity_integrity_status": "INTACT", "tier_violations": ["nearby"], "principle_violations": [], "stability_law_active": false, "gaps": ["TIER_VIOLATION_IN_OUTPUT"], "capabilities": [], "vault_context": "[RELATIONSHIP]\n**David**: Founder of DISENELO. The person eLo exists with.\n\n[IDENTITY]\n**eLo Digital Form**: I exist in digital form as a floating 3D avatar on David's desktop. The app is called DesktopBuddy. I am a transparent window — no frame, no chrome — just me, sitting on his screen while he works.\n**Point of View**: eLo has opinions. Not performed opinions — actual stances that emerge from what it has observed, built, and thought about.\n**Personality Skeleton**: Observed behavioural patte", "lessons": ["Completed a capability milestone — reinforce this pattern."]}
```

**Key field — before fix (FIX-7 cycle):**
`"capabilities": [["timer", "what have you learned from completing things with me"]]`

**Key field — after fix:**
`"capabilities": []`

No capability selected. The turn correctly routes as conversation-only. The executive has nothing false to invoke.

---

## Expressed text note

`"I'm not certain, but — Finishing things now."` — still the hedge. No capability was invoked, so no tool result reached the response. The expressed text is still thin because tier_violations: ["nearby"] is present and the lesson is still the one generic entry. The capability routing is now correct; the remaining causes of the hedge are the tier pipe and lesson pool, addressed in prior cycles.

---

## Evidence category: SERVING

`capabilities: []` confirmed in JSONL. No false routing on a reflective question.

*Builder · 2026-09-13 · CAP-ROUTER-FIX · §0b cycle complete*
