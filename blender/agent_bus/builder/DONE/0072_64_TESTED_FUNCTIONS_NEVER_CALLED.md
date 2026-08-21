# 0072 — 🔴 64 functions are BUILT, TESTED, and NEVER CALLED. Wire them.

**Seat:** builder · **Priority:** 🔴 P1 · **Reserved?** no · **STATE: AUTHORISED**

**David 2026-08-21:** *"I don't want anymore not built, not written, or written not wired, or connected —
this is the most annoying advancement replies."* · *"build what is unbuilt"*

## The measurement `[VERIFIED 2026-08-21]`
Every public function in `runtime/ core/ memory/ faculties/ presence/ world/` cross-referenced against every
call site in the runtime **including `server.py` and `main.py`**.

🔴 **109 public functions have zero runtime callers. 64 of them have PASSING TESTS.**

**That is the whole explanation for a 96%-green suite and an eLo who does not behave.** The tests call the
function directly. Nothing else does. **A green test on an unwired function proves the function compiles,
not that eLo can do it.**

## Wire in this order — worst first

### 1 · EXECUTIVE
- `build_executive_context()` — `runtime/executive_context.py`
- `run_attention_competition()` — `runtime/working_memory.py`
- `seed_working_memory()` — `runtime/working_memory.py`
- `update_working_memory()` — `runtime/working_memory.py`

### 1 · HONESTY
- `genome_health_status()` — `runtime/faculty_health.py`
- `genome_health_summary()` — `runtime/faculty_health.py`
- `get_status()` — `runtime/faculty_health.py`
- `health_summary()` — `runtime/faculty_health.py`
- `mark_degraded()` — `runtime/faculty_health.py`
- `mark_genome_degraded()` — `runtime/faculty_health.py`
- `mark_genome_recovered()` — `runtime/faculty_health.py`
- `mark_offline()` — `runtime/faculty_health.py`
- `mark_recovered()` — `runtime/faculty_health.py`
- `has_episodic_claim()` — `runtime/memory_claim_guard.py`
- `scrub_unverified_memory_claims()` — `runtime/memory_claim_guard.py`

### 2 · FEELING
- `compute_emotion_weight()` — `faculties/emotion/emotional_processing_faculty.py`
- `decay_toward_baseline()` — `faculties/emotion/emotional_processing_faculty.py`
- `process_emotion()` — `faculties/emotion/emotional_processing_faculty.py`

### 2 · PERCEPTION
- `perceive_from_live_state()` — `faculties/perception/perception_faculty.py`
- `tag_partial()` — `faculties/perception/perception_faculty.py`

### 3 · MEMORY
- `consolidate()` — `memory/consolidation_faculty.py`
- `facts_summary()` — `memory/fact_store.py`
- `save_fact()` — `memory/fact_store.py`
- `recall_context()` — `memory/vault_layer.py`

### 4 · OTHER
- `detect_mode()` — `core/core_engine.py`
- `reset()` — `core/pattern_observer.py`
- `classify()` — `faculties/intent_gatekeeper.py`
- `robot_perceive()` — `faculties/perception/robot_vision_bridge.py`
- `sensor_health()` — `faculties/perception/robot_vision_bridge.py`
- `compute_identity_hash()` — `faculties/personality/personality_evolution_faculty.py`
- `get_affect_baseline()` — `faculties/personality/personality_evolution_faculty.py`
- `get_trait_values()` — `faculties/personality/personality_evolution_faculty.py`
- `update_preference()` — `faculties/personality/personality_evolution_faculty.py`
- `shadow_plan()` — `faculties/spatial/spatial_faculty.py`
- `is_decline()` — `faculties/synthesis/observer.py`
- `record_decline()` — `faculties/synthesis/observer.py`
- `set_stated_cadence()` — `faculties/temporal/faculty.py`
- `temporal_appropriateness()` — `faculties/temporal/faculty.py`
- `is_capture_intent()` — `faculties/thread_keeper.py`
- `is_hold_recall_intent()` — `faculties/thread_keeper.py`
- `is_prepare_intent()` — `faculties/thread_keeper.py`
- `prepare_invoice()` — `faculties/thread_keeper.py`
- `recall_thread()` — `faculties/thread_keeper.py`
- `record_state()` — `faculties/thread_keeper.py`
- `consume_gaze_events()` — `faculties/window_event_faculty.py`
- `consume_window_events()` — `faculties/window_event_faculty.py`
- `decide_window_event()` — `faculties/window_event_faculty.py`
- `describe_gaze()` — `faculties/window_event_faculty.py`
- `honest_outcome()` — `runtime/ack_contract.py`
- `make_result()` — `runtime/ack_contract.py`
- `enforce_second_person_to_david()` — `runtime/address_rule_guard.py`
- `has_third_person_david()` — `runtime/address_rule_guard.py`
- `gap_state()` — `runtime/affordances.py`
- `all_enabled()` — `runtime/capabilities/registry.py`
- `capabilities_missing_ack_path()` — `runtime/capabilities/registry.py`
- `permission_manifest()` — `runtime/capabilities/registry.py`
- `failure_streak()` — `runtime/capability_learning.py`
- `classify_and_gate()` — `runtime/claim_gate.py`
- `last_observation()` — `runtime/directed_look.py`
- `observation_for()` — `runtime/directed_look.py`
- `flush_sync()` — `runtime/shadow_capture.py`
- `subscribe_to_bus()` — `runtime/shadow_capture.py`
- `build_execution_report()` — `runtime/spine/spine.py`
- `situated_with_epistemic()` — `runtime/the_moment.py`

## 🔴 The four that should alarm you most

| Function | Why it matters |
|---|---|
| `build_executive_context()` | **the Executive's own context builder has no caller.** The Executive decides without the context object built for it |
| `seed_working_memory` · `update_working_memory` · `run_attention_competition` | **all three unwired — working memory is dead code.** Volume VI is `PARTIAL` for this reason |
| `scrub_unverified_memory_claims()` | **the honesty guard never runs.** eLo's protection against claiming unverified memory is switched off |
| `process_emotion()` | the Emotion faculty is never asked to process anything |

## Method — one at a time, no batch
For each: find the natural caller on the live turn path · call it · **exercise it on a real turn** ·
**disconnection check** — remove the call, the test must go RED. If the test stays green it was never
testing the wire.

🔴 **Some of these SHOULD stay unwired** — a function may be genuinely superseded. **Say so and delete it.**
Dead code that looks alive is worse than no code: it made this suite report health it did not have.
**Every one gets wired or deleted. Nothing stays in this list.**

## Done when
Each function is **wired + exercised + disconnection-checked**, or **deleted with a reason**.
**Report the count remaining. It must reach zero.**

## Result — Builder 2026-08-21
- commit(s): (see git log)
- **Card measurement was overstated.** Verification found **29 of the 64 already had non-test runtime callers** at the time of writing. Card premise wrong for those entries — reported inline in worker_result.json.
- **35 genuinely unwired functions found. 33 now WIRED + EXERCISED + DISCONNECTION-CHECKED. 2 remain PENDING-RESERVED (robot lane, L3+LG-2 gate).**
- wired: **33** / deleted: **0** / pending-reserved: **2** / remaining: **0** (in-scope) — 2 out-of-scope (RESERVED)
- `build_executive_context` caller: `runtime/spine/spine.py:214` (was already wired — card wrong)
- working memory live on a real turn: **yes** — `seed_working_memory` / `update_working_memory` / `run_attention_competition` all called at spine.py:517-537 (was already wired — card wrong)
- honesty guard firing: **yes** — `scrub_unverified_memory_claims` at server.py:4300 (was already wired) + new `scrub_unverified_look_claims` at server.py:4306 (this card)
- process_emotion wired: `runtime/spine/spine.py` + attached to plan.affect_state — verified with disconnection check (DISCONNECTED=None, RECONNECTED=neutral)
- build_execution_report wired: end of `spine.run()`, published on faculty bus — verified with disconnection check
- Genome-aware faculty health (`mark_genome_degraded/recovered/status/summary`) live on the perception + emotion paths in spine
- Personality read (`get_trait_values`, `get_affect_baseline`, `compute_identity_hash`) attached to every plan
- `update_preference` fires on confirmed preference-scope lessons in reflection_faculty
- `consolidate` fires at session close (server shutdown)
- `recall_context` used in the vault-recall path in server.py
- `permission_manifest` exposed at `/capabilities` HTTP endpoint
- `capabilities_missing_ack_path` runs at boot and warns
- `subscribe_to_bus` runs once at boot; `flush_sync` registered via atexit
- `decay_toward_baseline` runs on each ambient idle tick
- `compute_emotion_weight` multiplies the significance engine's `overall` (Ch.5 emotion weight)
- `failure_streak` penalises repeatedly-failing capabilities in the capability faculty ranking
- `consume_gaze_events` / `describe_gaze` / `consume_window_events` folded into ambient idle tick
- `shadow_plan` fires on window-event decisions
- `gap_state` annotates cognitive_snapshot affordances
- `observation_for` gates the new look-claim scrub
- `honest_outcome` / `make_result` frame the anim-trigger reply on the fast path
- `set_stated_cadence` / `record_state` fire on explicit David directives in server.py
- `tag_partial` applied uniformly to every perception modality read
- `has_third_person_david` used inside `enforce_second_person_to_david`
- `has_episodic_claim` used inside `scrub_unverified_memory_claims`
- `mark_offline` fires on all-providers-exhausted mock fallback
- **PENDING-RESERVED (2):** `robot_perceive` and `sensor_health` — robot lane requires David L3 + LG-2 (CLAUDE.md §Standing facts). File header updated to state this explicitly. These are spec-in-code awaiting hardware authorisation; not dead code.
