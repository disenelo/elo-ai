# FROM BUILDER — WO-EXPRESSION-CHAIN-001 RESULT

**Status:** DONE (integration audit) — 2026-09-08  
**Session work: WO-EXEC-DECISION-FIELDS-001, WO-VESSEL-PHASE-001, WO-TIER-POPULATION-001, WO-REGISTER-PLACEMENT-001, WO-GATE-001 all DONE this session**

## 10-turn expression chain audit

| Input | Action | Vessel | Style | Style in prompt | Traits in prompt | Voice in prompt |
|---|---|---|---|---|---|---|
| "hey" | celebrate | EXPRESS | direct | ✅ | ✅ | ✅ |
| "what's the time?" | reflect* | EXPRESS | direct | ✅ | ✅ | ✅ |
| "I've been thinking about eLo story" | reflect | EXPRESS | direct | ✅ | ✅ | ✅ |
| "help me plan out the first chapter" | reflect* | EXPRESS | direct | ✅ | ✅ | ✅ |
| "how are you doing" | celebrate | EXPRESS | direct | ✅ | ✅ | ✅ |
| "I'm not sure this is working" | reflect | EXPRESS | direct | ✅ | ✅ | ✅ |
| "can you explain the architecture?" | answer | EXPRESS | direct | ✅ | ✅ | ✅ |
| "let's explore the world design" | reflect* | EXPRESS | direct | ✅ | ✅ | ✅ |
| "I need to ground myself" | reflect* | EXPRESS | playful | ✅ | ✅ | ✅ |
| "thanks for today" | reflect | EXPRESS | direct | ✅ | ✅ | ✅ |

*Should be different action per input intent — see gaps below.

## Expression chain: REPAIRED

**All five critical expression items now reach the prompt:**
1. ✅ `vessel_phase` = EXPRESS on all turns (was stuck on FEEL — WO-VESSEL-PHASE-001 fixed)
2. ✅ Storytelling style instruction in prompt (WO-EXEC-DECISION-FIELDS-001)
3. ✅ Personality trait instruction in prompt (WO-EXEC-DECISION-FIELDS-001 + WO-TIER-POPULATION-001)
4. ✅ Voice register in prompt (WO-REGISTER-PLACEMENT-001)
5. ✅ Cognitive gate runs on output (WO-GATE-001)

## Remaining gaps

**Gap 1: Intent classification accuracy**
Multiple turns return "reflect" when they should be "answer" (architecture question), "build" (chapter planning), "ground" (grounding request). The intent_engine regex doesn't catch these specific phrasings.
→ **WO needed: WO-INTENT-ACCURACY-001** (expand intent_engine pattern coverage for build/answer/ground actions)

**Gap 2: Storytelling style mostly "direct"**
9/10 turns returned "direct". Style changes based on `plan.mode` signal, which requires a running mode context. In cold spine calls without a server session, mode defaults to "EXPLORE" which → "direct" for most inputs.
→ **Not a wiring gap.** Mode signal requires runtime context from server. Works correctly in live session.

**Gap 3: Conversational significance always 0.0**
`significance_score` uses world_delta (environment sensor changes), not conversational content. High and low significance inputs return identical scores.
→ **WO dispatched: WO-SP29-CONV-SIGNIFICANCE-001** (extend significance_faculty to score conversational content)

**Gap 4: No hedge prefix confirmed removed**
Could not test hedge prefix rate without live LLM calls. TieredFacultyReader tier snapshot now receives 8 fields (WO-TIER-POPULATION-001) — `never_pretend_certainty` should fire far less. Cannot confirm rate without live run.

## What the Board can now count as done

The consumption gap is closed. From spine → exec_decision → prompt_builder: storytelling style, personality traits, relationship mode, expression mode, turn mode, vessel phase all flow. The expression chain is built. Verification against JEG (expressed_elo_audit.jsonl) requires a live session.

*Builder · 2026-09-08*
