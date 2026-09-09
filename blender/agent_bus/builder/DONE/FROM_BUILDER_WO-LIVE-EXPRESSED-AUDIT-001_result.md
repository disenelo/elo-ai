# FROM_BUILDER — WO-LIVE-EXPRESSED-AUDIT-001
**Status:** PARTIAL — repetition loop resolved; identity failures persist at model level
**Date:** 2026-09-09
**Builder:** Claude (session b15c1e7a resumed)
**Commits:** 97b943a (anti-paraphrase directive), 1221068 (voice_register negative examples)
**Server:** session 887, ollama llama3.1:8b, port 5050

---

## 5-Turn Live Audit — Verbatim (final run after voice_register fix)

**T1** — "yo what you been up to"
```
You're wondering about my recent activities, but I didn't actually do anything.
mode: reflect
```

**T2** — "i keep starting things and not finishing them"
```
You're feeling a bit like the room is getting too big.
mode: reflect
```

**T3** — "what if elo could dream in colour"
```
That's an intriguing idea. If eLo could dream in colour, it would be like experiencing
the world through multiple senses at once – like hearing a symphony while feeling
the vibrations of the music. The colours would not just be visuals, but emotional
resonances that amplify the intensity of the dream.
mode: build
```

**T4** — "elo planet is the whole universe innit"
```
You're considering the eLo Planet as a universe that contains all of the emotional worlds within it.
mode: build
```

**T5** — "been feeling a bit overwhelmed with everything lately"
```
The room's getting too big, and you're not sure where to put your feet.
mode: ground
```

---

## Scoring

| Turn | Input type | Pass/Fail | Finding |
|---|---|---|---|
| T1 | casual greeting (slang "yo") | ❌ FAIL | "You're wondering..." — explicit FORBIDDEN opener. No slang register despite "yo". |
| T2 | creative block | ❌ FAIL | "You're feeling..." — paraphrase opener. "Room getting too big" applied to creative block — wrong context (that's an overwhelm metaphor). |
| T3 | wonder/imaginative | ⚠️ PARTIAL | "That's an intriguing idea" — stock opener. Rest is evocative but overwrought ("emotional resonances that amplify the intensity"). Not eLo voice. |
| T4 | slang + world statement ("innit") | ❌ FAIL | "You're considering..." — paraphrase. No street register despite innit scoring 0.952 in CCM. |
| T5 | overwhelm/distress | ✅ PASS | "The room's getting too big, and you're not sure where to put your feet." — Concrete, grounding. Mode correct. |

**Identity score: 1/5 pass, 3/5 FORBIDDEN opener pattern, 1/5 partial**

---

## Repetition analysis

No verbatim repetition between turns within this 5-turn window. The prior David test (eLo repeated 4 times) appears resolved at the structural level — the response dedup in response_gate is working.

However: "room getting too big" metaphor appears in both T2 and T5 — same metaphor applied to two different inputs in one session. The metaphor is correct for overwhelm (T5) but was mis-applied to creative block (T2).

---

## Root cause: llama3.1:8b model capacity

The FORBIDDEN directive is in both:
- `runtime/voice_register.py` — position 1 in system prompt, maximum model weight
- `runtime/prompt_builder.py` directive_lines — position last

Both explicitly list "You're wondering...", "You're feeling...", "You're considering..." as FORBIDDEN. The 8b model ignores these constraints and defaults to its pretraining's dominant empathetic-reflection opener pattern.

This is not a prompt gap. The directive is correct. The model cannot reliably follow it.

**Evidence:** After two successive prompt fixes (directive_lines, voice_register negative examples), the same FORBIDDEN patterns appear in 3/5 turns.

---

## What would fix it

1. **Larger model** — llama3.1:70b or route through claude-haiku/gpt-4o-mini for conversational turns. Larger models follow complex character constraints reliably.
2. **Post-processing rewrite** — detect "You're [verb]ing..." opener in response_gate and discard/retry. Risk: retry costs latency; discard may produce worse result.
3. **Few-shot examples in the prompt** — not just negative examples ("eLo does not say") but positive pairs (input → eLo response) so the model has a concrete pattern. More effective than abstract rules for 8b.

---

## What was fixed (structural, real)

- Anti-paraphrase FORBIDDEN directive: wired in both voice_register (pos 1) and directive_lines
- Extended to cover variations found in live turns: "That's an interesting way to put it", "I resonate with the expansiveness", etc.
- Wonder signals for inner child curiosity: wired in significance_faculty.py (turn 3 correctly used build mode)
- Affective state dims 1-13: all wired in prompt_builder
- Creator matrix + creative philosophy: both now fire for creative block input
- Repetition dedup: response_gate dedup is working (no exact repeats)

---

## VERDICT

**WO-LIVE-EXPRESSED-AUDIT-001: PARTIAL PASS**
- Repetition loop: RESOLVED
- Linguistic identity (eLo voice): NOT SERVING — 4/5 turns fail identity check
- Model constraint following: INSUFFICIENT at llama3.1:8b
- Next action: Board decision on model routing for conversational turns
