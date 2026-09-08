# FROM BUILDER — WO-INTENT-ACCURACY-001 RESULT

**Status:** DONE — 2026-09-08

## What was built

**`runtime/router/intent_engine.py`:**

1. **`planning` intent** — 4 new patterns added and block moved BEFORE `lookup` to prevent the generic `what is` lookup pattern catching "what is the plan":
   - `help me plan / figure out / map out / work out / think through`
   - `let's plan / map out / figure out / think through / work out`
   - `plan out / the / this / it`
   - `what should/do we do first/next/now`

2. **`creation` intent** — 2 new pattern groups added:
   - `let's explore / work on / dig into / look at / get into / start on`
   - `I want/need to explore / work on / dig into / start on`

3. **`lookup` intent** — 4 new patterns added:
   - `can you explain / walk me through / break it down / help me understand`
   - `walk me through`
   - `help me understand`
   - `how does X work`
   - `break it/that/this down`

4. **`ground` intent** — new intent added (BEFORE navigation catch-all):
   - `ground myself`
   - `I need to ground/breathe/slow down/calm down/settle`
   - `feeling overwhelmed/scattered/anxious/off/lost/stuck`
   - `help me breathe/ground/settle/calm down/slow down`
   - `take a breath/minute/moment/step back`
   - `I'm overwhelmed/scattered/anxious/spiralling/spinning`
   - Category: **Reflect** / "grounding and steadying"
   - Added to `_CATEGORY_MAP`

## Root cause fixed

`planning` was ordered AFTER `lookup` in `_INTENT_PATTERNS`. The lookup pattern `\bwhat(?:'s|\s+is)\s+(?:a|an|the)?\w` caught "what is the plan" before planning could match. Fixed by moving `planning` before `lookup`.

## Acceptance Tests (17 cases, all PASS)

- "help me plan out the first chapter" → planning ✅
- "what is the plan" → planning ✅ (was: lookup — ordering bug fixed)
- "let us explore the world design" → creation ✅
- "can you explain the architecture" → lookup ✅
- "walk me through how this works" → lookup ✅
- "I need to ground myself" → ground ✅
- "feeling overwhelmed right now" → ground ✅
- "what is a chatbot" → lookup ✅ (generic lookup unchanged)
- "what time is it" → utility_time ✅ (no regression)

## Test Suite

1565 pass. 3 pre-existing failures unchanged.

*Builder · 2026-09-08*
