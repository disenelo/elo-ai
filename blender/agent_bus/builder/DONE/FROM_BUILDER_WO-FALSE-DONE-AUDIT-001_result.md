# FROM BUILDER — WO-FALSE-DONE-AUDIT-001 RESULT

**Status:** DONE — 2026-09-08  
**Audit type:** Diagnostic — no code changes

---

## C-10 — Storytelling Style: CONFIRMED DONE

**Where it runs:**
- `server.py:3790-3800`: `_plan.storytelling_style` checked + `[STORYTELLING FRAME — this turn only]` injected into system prompt
- `runtime/prompt_builder.py:503-512`: `storytelling_style` key consumed from exec_decision; style-specific directive injected

**Evidence:** `server.py:3800` — `system = system + f"\n\n[STORYTELLING FRAME — this turn only]\n{_ss_hint}"`. Fired on every turn where plan.storytelling_style is non-empty.  
**Was the board right?** Yes — WO-SC-NEW-001 done. The gap the BOARD_DIRECTIVE saw predated WO-EXEC-DECISION-FIELDS-001 (commit `2a23484`) which wired `storytelling_style` into exec_decision.

---

## C-13 — Inner Child: CONFIRMED DONE

**Where it runs:**
- `runtime/spine/spine.py:421-424`: `cognitive_mode_inner_child = bool(curiosity > 0.7 or (is_play and is_dream))`
- `server.py:3807`: `[CREATIVE SEED — imagined, not asserted]` injected from `_plan.creative_candidates`
- `runtime/prompt_builder.py:482-483`: Inner-child directive `"mode: inner-child — wonder first"` appended when flag is True

**Evidence:** `spine.py:424` sets flag from curiosity_score. `server.py:3807` injects [CREATIVE SEED]. Verified by `tests/test_wo_inner001_creative_seed_injection.py`.  
**Was the board right?** Yes — WO-INNER-001 done. The BOARD_DIRECTIVE gap predated WO-EXEC-DECISION-FIELDS-001.

---

## C-19 — Reflection / Growth: CONFIRMED DONE (architecture correct; data sparse by design)

**Where it runs:**
- **Read path (per turn):** `runtime/spine/spine.py:251` — `lesson_store.recall()` called; `runtime/the_moment.py:188` — `lesson_store.recall()` also called; lessons flow into `high_priority_memories` / `medium_priority_memories` on CognitiveState
- **Write path (event-driven):** `server.py:3310-3323` — `record_outcome()` on body ACK for sit; `server.py:3349-3357` — `record_outcome()` on body ACK timeout; `server.py:5478` — `_maybe_run_promote_pass()` every 10 turns
- `server.py:114`: `_PROMOTE_INTERVAL = 10`

**Why data is sparse:** Only body-ACK events trigger write. No body-ACK events = no write-side data. Architecture is correct; data will accumulate as system runs live with real interactions.  
**Was the board right?** Not fully. lesson_store WAS imported and called in server.py; the BOARD's grep for bare `lesson_store` missed the `from self.lesson_store import` pattern.

---

## C-20 — Personality Evolution: CONFIRMED DONE

**Where it runs:**
- `runtime/spine/spine.py:937-952`: `personality_evolution_faculty.load_personality()` + `get_trait_values()` + `get_affect_baseline()` called per turn
- `server.py:2912`: `"personality_traits": getattr(_plan, "personality_traits", {})` in exec_decision
- `runtime/prompt_builder.py:516-522`: Top 2 traits injected when significance ≥ 0.3: `"Expressed traits this turn: wonder, empathy"`

**Live state:** 8 traits loaded: `{'curiosity': 0.62, 'patience': 0.65, 'confidence': 0.60, 'empathy': 0.72, 'discipline': 0.58, 'wonder': 0.80, 'playfulness': 0.68, 'directness': 0.72}`. State file: `self/personality_state.json`.  
**Persistence between sessions:** YES — `load_personality()` reads from `self/personality_state.json` on each boot.  
**Was the board right?** The gap predated WO-EXEC-DECISION-FIELDS-001. personality_evolution IS in the turn path via spine.py.

---

## Summary

All four items are DONE. The BOARD_DIRECTIVE audit was filed 2026-09-08 before WO-EXEC-DECISION-FIELDS-001 (commit `2a23484`) was executed. That single WO wired all expression fields (storytelling_style, personality_traits, ccm_context, significance_score, relationship_mode, turn_mode) into exec_decision and prompt_builder. The audit's gap was real at time of filing; it is resolved.

**No code changes required. No false completions remain in these four items.**

*Builder · 2026-09-08 · Diagnostic only*
