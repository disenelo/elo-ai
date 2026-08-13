# WP-X Behaviour Consistency — Current Reality Review

**Status:** REVIEW COMPLETE — 2 high gaps, 2 medium gaps
**Audit date:** 2026-07-12

---

## Consistency audit scope

Behaviour consistency means: eLo's character, rules, and voice are identical regardless of which embodiment or backend is active.

---

## Confirmed consistent across embodiments

| Behaviour | Mechanism | Status |
|---|---|---|
| Core CHARACTER DNA | `prompts/living_presence_spec.txt` — same file, both embodiments | ✓ |
| 5 tones | `runtime/executive.py` — frozen, both paths use it | ✓ |
| 10 CAL actions | Same executive.py | ✓ |
| 14 FORBIDDEN rules | `runtime/prompt_builder.py` — same builder, both paths | ✓ |
| Max sentences enforcement | `runtime/backend_router.py normalise()` | ✓ |
| Register detection (South London) | Same `_detect_register()` | ✓ |
| Memory principle | Same memory pack injection | ✓ |
| Silence rule | Same executive.py | ✓ |
| Eyes animation absent | No eye shapes in prompt or expression dict | ✓ |
| Ambient speech register | Neutral warmth — appropriate by design (fires without user context) | ✓ |

---

## 14 FORBIDDEN rules — confirmed complete

All 14 rules present in `runtime/prompt_builder.py`:

1. Never repeat/echo CONTEXT blocks
2. Never self-reference as "the system"
3. Never use asterisk actions (`*leans in*`, etc.)
4. Never correct user terminology
5. Never blame developers
6. Never offer abstract advice on system issues
7. Never use chatbot openers ("It's interesting that", "That's a great point", etc.)
8. Never narrate system actions
9. Never create bridge constructions ("same thread", "same loop", "links X to Y", etc.)
10. Never analyze fragmented messages
11. Never offer unsolicited psychological interpretation
12. Never narrate observations ("I notice you keep returning")
13. Never extrapolate meaning from light statements
14. Never narrate user's comprehension ("that's what you were looking for")

**Status: COMPLETE ✓**

---

## Violations Found

### V1 — Terminal _av_note missing avatar self-reference prohibition (HIGH)

**server.py _av_note** (DISENELO Presence):
```
"NEVER refer to yourself as 'the system', 'the platform', 'the software', or 'the Avatar'.
You are eLo. The architecture underneath you is irrelevant to David — just be present."
"The app is called DISENELO Presence — not Desktop Buddy."
```

**main.py _av_note** (Terminal):
```
"You have a small visual window in the bottom-right corner of the user's screen.
You move with the conversation — walking, sitting, jumping, looking."
```

Terminal has:
- No "Avatar" self-reference prohibition
- No DISENELO Presence naming
- Weaker identity statement

**Fix:** Unify the avatar note. Add to `main.py`: the self-reference prohibition and the character-over-architecture directive. The DISENELO Presence app name is less relevant for terminal but the prohibition applies universally.

### V2 — VOICE RULE advisory only, not enforced (MEDIUM)

**Architecture spec:** 15–30 words, maximum one breath.

**Current enforcement:**
- Word target: system prompt directive only (advisory)
- Sentence cap: `normalise()` enforces `max_sentences` from Executive
- No word-count validation exists

**Example that passes without issue:**
- "This is a really interesting insight you've shared. The way you're thinking about the project feels alive. I'm curious where you want to take it next." — 3 sentences ✓, ~40 words ✗

**Fix:** Add word-count check to `backend_router.normalise()`. If word count > 45 (allowing margin), truncate to sentence boundary within 30 words.

---

## Gaps Found

### G1 — MULTI-TURN RULE advisory only (MEDIUM)

**Rule:** Ask one missing slot per turn. Confirm previous slot implicitly.

**Current status:** Injected as a directive in system prompt. No post-generation validation. LLM can ask two questions and no enforcement catches it.

**Fix:** Post-generation scan: count `?` characters in sentences. If two questions detected in response, log a behaviour audit event.

### G2 — South London register not tested across embodiments (LOW)

`_detect_register()` exists in both embodiments (via same relationship_faculty.py). But no test confirms that register-mode injection (`[SOUTH LONDON REGISTER]` block) actually changes LLM output in a measurable way across terminal vs server.

---

## Ambient speech register — correct by design

Ambient speech pool uses **neutral warmth** vocabulary (not south London dialect). This is correct: ambient lines fire without user context, so register-matching would be inappropriate. Lines maintain eLo's core presence (calm, observant, grounded) without forcing register on a contextless trigger.

---

## Summary Table

| Expectation | Reality | Match? |
|---|---|---|
| 14 FORBIDDEN rules complete | ✓ All 14 confirmed | ✓ |
| VOICE RULE enforced | ✗ Advisory only; sentence cap enforced, not word count | ⚠️ |
| MULTI-TURN RULE enforced | ✗ Advisory only | ⚠️ |
| Avatar self-reference prohibited in all embodiments | ✗ Terminal _av_note missing prohibition | 🔴 |
| DISENELO Presence named consistently | ✗ Terminal _av_note doesn't name it | ⚠️ |
| Character DNA identical across embodiments | ✓ Same spec file | ✓ |
| Max sentences enforced | ✓ `normalise()` enforces per tone | ✓ |
| Ambient register appropriate | ✓ Neutral warmth, by design | ✓ |
| Eyes absent from expression | ✓ No eye shapes anywhere | ✓ |
