# FROM BUILDER — WO-FACULTY-CHAIN-VERIFY-001 RESULT

**Status:** DONE (diagnostic) — 2026-09-08  
**Test input:** "hey what is up"

## Faculty chain trace — CognitivePlan fields after one live turn

| Faculty | Field | Value |
|---|---|---|
| **Perception** | `raw` | `'hey what is up'` |
| **Attention** | `meaning` | `'what is up'` |
| **Intent** | `intent` | `'conversation'` ← 0.5 (low; falls to conversation default) |
| **Intent** | `capability_hint` | `'lookup'` (intent_engine secondary) |
| **Intent** | `conversation_action` | `'reflect'` |
| **Emotion** | `emotional_vector` | `{state: 'reflection', energy: 0.35, warmth: 0.714, curiosity: 0.55}` |
| **Emotion** | `affect_state` | `AffectState(valence=0.02, arousal=0.43, dominant_emotion='neutral')` |
| **Emotion** | `emotional_tag` | `EmotionalTag(valence=0.02, intensity=0.014, dominant_emotion='neutral')` |
| **Memory** | `lesson_id` | `'99ae9fcf7d4231eb'` (lesson contributed) |
| **Memory** | `cal_reason` | `'lesson: Completed a capability milestone — reinforce this pattern.'` |
| **Reasoning** | `confidence` | `0.5` |
| **Reasoning** | `personality_traits` | `{curiosity:0.62, patience:0.65, confidence:0.6, empathy:0.72, …}` ✅ |
| **Reasoning** | `personality_baseline` | `{mood_baseline:0.728, curiosity_baseline:0.62, empathy_baseline:0.72, …}` ✅ |
| **Reasoning** | `snapshot` | `CognitiveSnapshot(self_mood=0.184, self_curiosity=1.0, …)` |
| **Imagination** | `creative_candidates` | `()` (empty — inner child not active this turn) |
| **Agency** | `capabilities` | `[('search', 'what is up')]` |
| **Expression** | `vessel_phase` | `'EXPRESS'` ✅ (fixed by WO-VESSEL-PHASE-001) |
| **Expression** | `storytelling_style` | `'direct'` (no mode signal for this input) |
| **Expression** | `relationship_mode` | `'developing'` |
| **Expression** | `expression_mode` | `'default'` |
| **Expression** | `speech_licence` | `SpeechLicence(tier_snapshot={pose:observed, mood:inferred, capabilities:inferred, …})` |
| **World** | `world` | `LiveWorldState(desktop=DesktopState(active_app='', platform='mac', available=True))` |
| **Temporal** | `temporal_frame` | `TemporalOutput(now_iso='2026-09-08T16:01:11+00:00', part_of_day='afternoon')` |

## Assessment

**The One Brain assembles a real CognitiveState.** All major faculties contribute. Key findings:

**POPULATED and flowing:** raw, meaning, intent, conversation_action, emotional_vector, affect_state, emotional_tag, personality_traits, personality_baseline, snapshot, capabilities, vessel_phase, storytelling_style, relationship_mode, lesson_id, world, temporal_frame, speech_licence.

**ABSENT / STUB this turn:**
- `creative_candidates` = `()` — imagination faculty ran but produced nothing (curiosity threshold not met)
- `significance_score` — NOT a plan field (checked separately in exec_decision; not on plan itself)
- `ccm_context` — NOT a plan field (set in executive but not surfaced to plan)
- `turn_mode` — NOT a plan field (set in exec_decision from executive output)
- `wkg_context` — lives on cognitive_state object (CognitiveState.wkg_context), not on plan directly

**C-01 verdict:** The One Brain assembly chain IS built and functioning. Faculty chain produces populated CognitivePlan. The "gaps" from prior audit were exec_decision CONSUMPTION gaps (now closed by WO-EXEC-DECISION-FIELDS-001) — not assembly gaps.

*Builder · 2026-09-08 — no code changes, report only*
