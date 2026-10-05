# WO-KNOWLEDGE-PSYCHOLOGY-001 — Result Card
**Builder:** Builder 1  
**Date:** 2026-10-05  
**Commit:** e3deadc  
**Status:** COMPLETE — 62/62 tests pass (shared test file with WO-SOCIAL-DYNAMICS-001)

---

## Gap closed

eLo had no psychology domain knowledge. Without it: David says "I can't focus today" — eLo had no model of attention, habit disruption, or stress response. Could only process surface words, not understand the human experience behind them.

---

## What was built

### WKG data — `relationships/world_graph.json`

New source: `wkg:source:psychology_consensus` (reliability note: models describe tendencies, not individual diagnoses).

**17 new WKG claims** covering all 16 domains from David's spec + 1 epistemic boundary claim:
- `emotion_is_multidimensional` — valence, arousal, behavioural components; multiple models, none complete
- `motivation_intrinsic_extrinsic` — SDT, Maslow's hierarchy (not empirically sequential)
- `habit_is_cue_routine_reward_loop` — basal ganglia loops; disruption ≠ failure
- `attention_is_finite_selective` — flow states, attentional fatigue, eLo can support or compete
- `perception_is_constructive` — active construction, expectation effects, same input → different read
- `learning_has_multiple_modes` — classical/operant/observational/insight; learning styles not supported
- `human_memory_is_reconstructive` — VERIFIED; reconstructive not archival; never correct David on his own experience
- `social_behaviour_is_context_dependent` — same person, different setting; don't treat observed as stable trait
- `communication_is_more_than_words` — subtext, pragmatics, what's left unsaid
- `attachment_shapes_relationships` — Bowlby/Ainsworth; styles are tendencies not fixed states
- `groups_shape_individual_behaviour` — groupthink, in-group/out-group, leadership
- `cognitive_biases_are_systematic_errors` — confirmation bias, availability heuristic, sunk cost, anchoring; eLo's own reasoning can be biased
- `decision_making_is_dual_process` — System 1 (fast/intuitive) vs System 2 (slow/deliberate); stress → System 1 dominates
- `creativity_follows_incubation_pattern` — preparation→incubation→illumination→verification; flow; creative blocks = evaluative pressure
- `stress_activates_threat_response` — VERIFIED; fight/flight/freeze; cortisol impairs cognition; eLo reduces friction, doesn't add load
- `behavioural_patterns_are_stable_tendencies` — tendencies not rules; learn David's patterns without labelling uninvited
- `psychology_models_are_not_individual_diagnoses` — **epistemic boundary claim** — models describe populations, not individuals; hard lane enforcement in the data layer

All psychology claims carry `hard_lane: general_knowledge_not_diagnosis` (or `model_vs_diagnosis_gate`) in notes.

### Faculty — `faculties/knowledge/psychology_faculty.py`

- `is_domain_trigger(text)` — keyword set covering all 16 domains
- `query(text, max_results)` — loads psychology claims, token-scores against interpretation + notes, min token length 5 (no stop-word false matches), returns ranked list with `_score`
- `context_block(text, max_results)` — query wrapper that prepends `HARD_LANE_NOTE` to injection string; empty string for unrelated text

**HARD_LANE_NOTE (verbatim):** `[PSYCHOLOGY KNOWLEDGE — hard lane: general knowledge only. Do NOT diagnose, label, or interpret David's behaviour back at him. Use this understanding to be a more attuned presence, not an analyst.]`

---

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| AC-1 | eLo can discuss psychological concepts with domain competence | ✅ — 17 claims cover all 16 domains |
| AC-2 | eLo understands model ≠ individual diagnosis | ✅ — epistemic boundary claim + hard lane in data + faculty |
| AC-3 | Feeds CCM without causing over-interpretation | ✅ — hard lane note in every context injection |
| AC-4 | Does not pathologise — observes patterns, not disorders | ✅ — hard lane enforced at data and faculty layer |

---

## Tests
`tests/test_wo_knowledge_psychology_social.py` — 62/62 (shared with WO-SOCIAL-DYNAMICS-001)
- TestPsychologyWKGData (20): source present, 16+ claims, all 16 domains covered, hard_lane tag on all claims
- TestPsychologyFaculty (10): importable, hard lane prohibits diagnosis/labelling, trigger detection, query relevance, max_results, empty for unrelated
