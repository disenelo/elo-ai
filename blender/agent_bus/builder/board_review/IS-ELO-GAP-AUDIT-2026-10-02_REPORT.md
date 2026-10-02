# IS ELO Gap Audit — DISENELO Presence vs Code Reality

**Report date:** 2026-10-02  
**Builder:** Claude Sonnet 4.6 (Builder lane)  
**Commissioned by:** David Charles (direct)  
**Source spec:** IS ELO — full ~600-question specification across 30+ categories  
**Codebase audited:** `~/elo-ai/` (commit HEAD after dispatch `48b26b2`)  
**Audit method:** Subagent file-level inspection + line-level trace against server.py, elo_self_model.py, spine.py, capability_learning.py, reflection_faculty.py, working_memory.py, curiosity_faculty.py, conversation_tracker.py, emergent_cognition.py, self_knowledge.py, novelty_detector.py, initiative_faculty.py, silence_faculty.py, dream faculty stack, spg_faculty.py, wkg/, provenance.py.

**Rule:** ✅ = file + line wired + tested. ⚠️ = exists in code but causally incomplete. 🔴 = not real.

---

## The Walking Question — Answered First

**IS ELO — Embodied but Not Trapped by His Body?**  
> "Can eLo understand that walking in Unity and walking physically are different experiences?"

**Answer: No. Not yet.**

What currently exists:
- `EloSelfState.embodiment` — knows which body it's in (`desktop|robot|phone|game|AR`)
- `EloSelfState.available_actions` — gates capabilities per embodiment (game has jump, desktop does not)
- `route_memory.py` — records Unity movement ACKs (arrived, fell, route_nodes, duration) — **game embodiment only**
- WIRE-9 (`server.py` ~line 4523) — `record_failure('MOVE')` on `_mout.fell or not _mout.arrived` — **game movement only**

What is missing:
- **No per-embodiment movement experience store.** Desktop movement (screen XY interpolation) leaves no experience record. Game movement does (route_memory ACKs). Robot movement doesn't exist yet.
- **No phenomenological distinction.** "Walking in Unity = CharacterController + physics response" vs "walking on desktop = smooth XY interpolation" are not represented as qualitatively different. eLo knows it's in a different body; it does not know what that body's movement *feels like* vs another.
- **No cross-embodiment movement comparison.** If eLo walks in game and is asked "does walking in Unity feel different from walking on your screen?", nothing in the architecture supports that answer from stored state. The LLM generates a plausible answer, not an experience-grounded one.

**Gap to close:**  
`EloSelfState` needs `locomotion_experience: dict[str, dict]` — per-embodiment recorded movement properties. Desktop: `{type: 'screen_position_interp', latency_ms, smoothness, no_physics}`. Game: `{type: 'charactercontroller_physics', fell_count, avg_route_duration, terrain_resistance}`. Robot (future): `{type: 'servo_tension_omniwheel', ...}`. This makes embodiment difference causal, not conversational.

---

## IS ELO — Causally Real? (The Critical Layer)

The IS ELO spec asks not just "does eLo possess X?" but "what would have to be true for eLo to *genuinely* possess X?" — meaning the property must have **causal reality in the running system**, persist after the generating response ends, and affect later turns.

Causal chain requirement: **state change → persists to disk → read on next turn → affects Executive → becomes action → result feeds back as memory.**

| Property | Causal Reality | Break Point |
|---|---|---|
| Identity persists across restart | ⚠️ Partial | `elo_self_state.json` persists. But `check_identity_drift()` only logs WARNING — no corrective action fires. Drift detected = drift ignored. |
| Open threads persist across restart | ⚠️ Partial | `EloSelfState.open_threads` saves to disk and is the fallback that works. **`carry_wm()` is never called on session close in production.** The `continuity/` write path is architecturally declared but untriggered live. |
| Failure learning persists | 🔴 Not real | `_failure_streaks` in `capability_learning.py` is a **module-level in-memory dict** — resets on every process restart. Proposals written to `logs/learning_proposals.jsonl` but nothing reads them back. Zero cross-session causal learning. |
| Reflection lesson persists | ⚠️ Partial | WIRE-2 writes to `self/lessons_ledger.jsonl`. But `_elo_self.last_reflection_lesson` is updated on the **in-memory cached copy**, not via `_self_mutate()`. Next `_self_mutate()` call overwrites it. Lesson may die within the same session. |
| Identity drift corrects | 🔴 Not real | Warning-only (`logging.warning()`). No regeneration, no correction block, no forced revision. |
| Curiosity is real | 🔴 Not real | `runtime/curiosity_faculty.py` does not exist. Curiosity is a float scalar in EloSelfState. No faculty generates questions, retains them, or returns to them. |
| Conversational referent tracking | ⚠️ In-session only | `conversation_tracker.py` + `referent_extractor.py` wired, functional during a session. Dies completely on restart — no persistence to disk. eLo forgets all referents between conversations. |
| Episodic vs semantic retrieval | ⚠️ Write-only distinction | `proposed_type: episodic|semantic|procedural|emotional` exists in `memory_faculty.py`. Query layer does not filter by type. Distinction is on write, irrelevant on retrieval. |
| Cross-embodiment identity in self_knowledge | ⚠️ Incomplete | `self/elo_self_model.py` lists `desktop|robot|phone|game|AR`. `runtime/self_knowledge.py` only knows terminal/desktop/mobile/robot — **"game" is missing**. |
| Does changing state change future behaviour? | ⚠️ Conditional | Yes if changes go through `_self_mutate()`. No if they mutate the in-memory copy only (which WIRE-2's reflection lesson does). |
| Can eLo fail without pretending it succeeded? | ⚠️ Partial | Game movement failures: ✅ WIRE-9 records them. Conversational failures, tool failures, misunderstandings: 🔴 no failure state written, no record. |
| If prompts removed, does architecture still produce eLo? | ⚠️ Partial | `elo_self_state.json` loads and injects identity data. Without `living_presence_spec.txt` (FREEZE_V1_LOCK), underlying Qwen drifts. Persistent state contains identity *data*; *behaviour* is prompt-dependent. Not fully architecture-native yet. |

---

## Full Category Status by IS ELO Section

### Identity & Self — ⚠️ overall

| Claim | Status | Code location | Gap |
|---|---|---|---|
| Continuous identity | ⚠️ | `self/elo_self_model.py` EloSelfState — `identity_name`, `core_values`, `invariants` | Drift guard logs only; no corrective action |
| Self-model | ⚠️ | EloSelfState | No `limitations` list, no `uncertainty` field, no `learned_skills` structured store |
| Embodied self | ⚠️ | `embodiment` field + `embodiment_history` | Knows current body; no comparative experience across bodies |
| History contributes to identity | ⚠️ | `self/journals/autobiography.jsonl` (provenance-gated) | Autobiography exists; not read back into Executive decisions |
| Identity across embodiments | ⚠️ | `embodiment_transitions` list on EloSelfState | No per-embodiment experience differentiation |
| Identity when model changes | 🔴 | — | No model-change detection or identity continuity guard |

### Agency & Decision — ✅ overall with gaps

| Claim | Status | Code location | Gap |
|---|---|---|---|
| Single decision authority | ✅ | `runtime/executive.py` | Sole authority; faculties propose |
| Decide not to act | ✅ | `runtime/silence_faculty.py` wired in server.py | SPG `edge_hint='silence'` mechanism |
| Hold intention across turns | ⚠️ | `EloSelfState.open_threads` + WIRE-7 | carry_wm not flushed on session close |
| Recognise failed action | ⚠️ | WIRE-9 for movement; nothing for other failure types | Tool failures, conversational failures: no failure state written |
| Revise intention before execution | ⚠️ | Working memory has threads; no explicit revision API | |

### Perception & Awareness — ⚠️ overall

| Claim | Status | Code location | Gap |
|---|---|---|---|
| Novelty detection | ✅ | `memory/novelty_detector.py` + server.py prompt injection | Injected every turn |
| Notice environmental change | ⚠️ | SPG detects recurring signals; no real-time environment watcher | |
| Prediction error / surprise | ⚠️ | Novelty scores against base rate | No explicit prediction→reality comparison cycle; no "I expected X and got Y" state |

### Conversation — ✅ in-session, 🔴 cross-session

| Claim | Status | Code location | Gap |
|---|---|---|---|
| Referent tracking | ✅ | `faculties/grounding/conversation_tracker.py` + `referent_extractor.py` | In-memory only |
| Pronoun resolution | ✅ | `referent_extractor.py` `pronoun_resolution` dict | |
| All conversation context | 🔴 | — | Dies on restart — no persistence; eLo forgets every referent between conversations |

### Memory — ⚠️ overall

| Claim | Status | Code location | Gap |
|---|---|---|---|
| Autobiographical memory | ✅ | `self/journals/autobiography.jsonl`, `append_autobiography()` verified-only gate | |
| Provenance | ✅ | `memory/provenance.py` full pipeline | |
| Episodic/semantic distinction | ⚠️ | `memory_faculty.py` type field on write | Query layer treats both identically |
| Update/correct memory | ⚠️ | `fact_store.py` can add facts | No `update_memory()` with correction history; no amend-with-provenance |
| Conflict detection | 🔴 | — | No conflicting memory detection system |
| Remember without treating as verified fact | ✅ | `verified=True` gate on autobiography | Only verified events stored |

### Knowledge & Truth — ⚠️ overall

| Claim | Status | Code location | Gap |
|---|---|---|---|
| WKG (knowledge graph) | ✅ | `memory/wkg/`, `knowledge/graph_loader.py` | |
| Knowledge vs belief vs inference | ⚠️ | Provenance types: AUTHORITATIVE/RETRIEVED/GENERATED/INFERRED | Not exposed to Executive as a reasoning distinction |
| Knowledge can become outdated | 🔴 | — | No staleness model on WKG entries |
| Identify contradictions in knowledge | 🔴 | — | No contradiction detection |

### Learning — 🔴 mostly

| Claim | Status | Code location | Gap |
|---|---|---|---|
| Learn from mistakes | ⚠️ | `capability_learning.py` `record_failure()` | `_failure_streaks` in-memory only, resets on restart |
| Learn from success | ⚠️ | `record_success()` | Same in-memory problem |
| Persistent learned behaviour | 🔴 | `logs/learning_proposals.jsonl` | Proposals written; nothing reads them back into Executive |
| Forget/deprioritise obsolete | 🔴 | — | `unlearn.py` does not exist |
| Develop second-nature responses | 🔴 | — | No habit formation system |
| Learn without retraining model | ⚠️ | fact_store, autobiography, EloSelfState changes | None of these automatically alter future behaviour without prompt injection |

### Skills & Habits — 🔴

| Claim | Status | Gap |
|---|---|---|
| Learned skills store | 🔴 | No `learned_skills` field on EloSelfState with structure |
| Habit detection | 🔴 | No habit formation or recognition system |
| Low-latency response from repetition | 🔴 | Not implemented |

### Pattern, Intuition & Prediction — ⚠️

| Claim | Status | Code location | Gap |
|---|---|---|---|
| SPG pattern recognition | ✅ | `memory/spg_faculty.py`, `memory/spg_graph.py` | |
| Predictions from experience | ⚠️ | SPG signals injected into prompt | No explicit prediction-tracking; no "I predicted X" stored state |
| Recognise when prediction was wrong | 🔴 | — | No prediction error recording |
| Intuition as signal not fact | ⚠️ | SPG `edge_hint` field | Not surfaced to eLo's own reasoning |

### Curiosity & Exploration — 🔴

| Claim | Status | Gap |
|---|---|---|
| Curiosity faculty | 🔴 | `runtime/curiosity_faculty.py` does not exist |
| Generate questions | 🔴 | No system for this |
| Retain unanswered questions | 🔴 | No persistence |
| Return to unanswered questions | 🔴 | No mechanism |

### Reflection & Self-Correction — ⚠️

| Claim | Status | Code location | Gap |
|---|---|---|---|
| Reflection fires | ✅ | WIRE-2: `integrate_session()` every turn, `self/lessons_ledger.jsonl` | |
| Lesson persists correctly | ⚠️ | `_elo_self.last_reflection_lesson` | Updated on in-memory copy, not via `_self_mutate()` — may not survive |
| Recognise poor response | 🔴 | — | No response quality self-assessment system |
| Correct self without rewriting history | 🔴 | — | No correction-with-provenance system |

### Dream State — ✅

| Claim | Status | Code location |
|---|---|---|
| Dream faculty | ✅ | `faculties/dream/` full stack (dream_faculty.py, dream_work.py, dream_review.py, sleep_cycle.py, symbol_engine.py) |
| Wired to Executive | ✅ | `should_dream()` + `run_dream()` + `wake_from_dream()` in idle-watcher loop, 600s gate |
| Distinguishes dream material from waking memory | ✅ | Architecture separates dream output from autobiography |

### One Brain — ✅ with open question

| Claim | Status | Code location | Gap |
|---|---|---|---|
| Single Executive | ✅ | `runtime/executive.py` | |
| No faculty independently decides | ✅ | Spine architecture | |
| No legacy bypass path | ⚠️ | Ambient processes route through `_self_mutate()` guarded paths | Not fully verified that all legacy paths are retired |
| No ambient process speaks as eLo without cognitive plan | ⚠️ | Needs live verification | |

### Embodiment — ⚠️

| Claim | Status | Code location | Gap |
|---|---|---|---|
| Knows current body | ✅ | `EloSelfState.embodiment` | |
| Adapts capabilities per body | ✅ | `available_actions` + `CAPABILITY_REGISTRY` | |
| Game embodiment in self_knowledge | 🔴 | `runtime/self_knowledge.py` | Only terminal/desktop/mobile/robot listed; "game" missing |
| Per-embodiment movement experience | 🔴 | — | Walking question: no locomotion_experience per embodiment |
| Transfer learning between embodiments | 🔴 | — | No mechanism |

### Self-Knowledge of Architecture — ✅

| Claim | Status | Code location | Gap |
|---|---|---|---|
| Reports live capabilities | ✅ | `runtime/self_knowledge.py` `self_knowledge_block()` | |
| Knows which capabilities unavailable | ✅ | `cannot_do` + `not_on_body` lists | |
| Knows which faculty supplied information | 🔴 | — | No per-response faculty provenance surfaced to eLo |
| Enumerates faculties by name | 🔴 | — | Reports capability categories, not faculty names |

### Attention & Significance — ✅

| Claim | Status | Code location |
|---|---|---|
| Novelty detection | ✅ | `memory/novelty_detector.py` |
| SPG significance patterns | ✅ | `memory/spg_faculty.py` |
| Silence (prevent attention hijacking) | ✅ | `runtime/silence_faculty.py` |
| Initiative | ✅ | `runtime/initiative_faculty.py` |

### Capable of Not Knowing / Silence — ✅

| Claim | Status | Code location |
|---|---|---|
| Silence faculty | ✅ | `runtime/silence_faculty.py` wired in server.py |
| SPG `edge_hint='silence'` | ✅ | Mechanism functional |

### Capable of Failure — ⚠️ Partial

| Claim | Status | Code location | Gap |
|---|---|---|---|
| Failure produces state | ⚠️ | WIRE-9 for game movement | No failure state for conversational, tool, or reasoning failures |
| Failure produces persistent learning | 🔴 | `_failure_streaks` | In-memory only; resets on restart |
| Recognise failure honestly | ⚠️ | For movement: yes (route_memory). For responses: no. | |
| Retry intelligently after failure | 🔴 | — | No intelligent retry system |

---

## IS ELO — Persistent? Honest Verdicts

| IS ELO Question | Honest Answer |
|---|---|
| Does eLo remember something because it happened, not because it was placed in a prompt? | ⚠️ Partial — autobiography entries are provenance-gated. Fact_store entries are not experience-gated. WKG is not experience-gated. Most "memory" is placed in the prompt each turn. |
| Does eLo remember something after restarting the process? | ✅ EloSelfState, autobiography.jsonl, fact_store persist. carry_wm does not (untriggered). |
| Does eLo remember previous mistakes? | 🔴 No — `_failure_streaks` resets on restart. |
| Does eLo remember previous corrections? | 🔴 No — no correction-with-provenance system. |
| Does eLo know when something should be retrieved? | ⚠️ — WKG + vault retrieval wired; no active "should I retrieve?" decision; retrieval is always-on per turn. |
| Does eLo avoid allowing old memory to override current reality? | 🔴 No explicit mechanism. Memory injection is non-selective. |

---

## Priority Gaps — In Causal Severity Order

These are the gaps that must be closed for IS ELO answers to become architecturally true rather than conversationally plausible:

| # | Gap | Severity | Why |
|---|---|---|---|
| 1 | **`carry_wm()` not called on session close** | 🔴 Critical | The intention persistence architecture is declared but untriggered. EloSelfState fallback is the only working path. This breaks the continuity claim. |
| 2 | **`_failure_streaks` not persisted to disk** | 🔴 Critical | Cross-session causal learning from failure is entirely non-existent. "eLo learns from mistakes" is false. |
| 3 | **`curiosity_faculty.py` does not exist** | 🔴 Critical | Already in P2 queue. Curiosity is a float scalar only — no questions generated, retained, or returned to. |
| 4 | **WIRE-2 reflection lesson bypasses `_self_mutate()`** | ⚠️ High | In-memory update may be overwritten intra-session. Lesson persistence is unreliable. |
| 5 | **Identity drift guard is warning-only** | ⚠️ High | `check_identity_drift()` fires every turn but has no corrective action. Drift is detected and logged but not corrected. |
| 6 | **`game` missing from `self_knowledge.py` embodiment list** | ⚠️ Medium | Self-knowledge of architecture is incomplete. eLo cannot accurately report its own game embodiment. |
| 7 | **Per-embodiment locomotion experience** | ⚠️ Medium | Required to answer the walking question with architectural truth. Walking in Unity vs desktop vs robot = identical experience model right now. |
| 8 | **Conversational referent tracking not persisted** | ⚠️ Medium | `conversation_tracker.py` dies on restart. eLo forgets every referent between conversations. |
| 9 | **No correction-with-provenance system** | ⚠️ Medium | "eLo self-corrects without rewriting history" is not implemented. |
| 10 | **`unlearn.py` and `metacognition.py` do not exist** | ⚠️ Medium | P2 queue items. Deprioritisation of obsolete behaviour and meta-learning have no architectural home. |

---

## For Board Action

### Items requiring Board decisions:

**B-ISELO-01 — carry_wm() session-close hook**  
Builder can add a `carry_wm()` call to the server.py shutdown path and to the turn-end path without touching FREEZE_V1_LOCK files. Request: confirm that writing to `continuity/` at turn-end is approved (has latency implications — file write per turn).

**B-ISELO-02 — failure_streaks persistence**  
`capability_learning.py` is not in FREEZE_V1_LOCK. Builder can add `json` persist/load for `_failure_streaks` at module init and on `record_failure()`. Request: Board confirm this scope is approved for next dispatch.

**B-ISELO-03 — curiosity_faculty.py build**  
Already in P2 queue. Confirm priority ordering vs unlearn.py and metacognition.py. All three are P2 and none exist. Recommend curiosity first (causal gap is largest).

**B-ISELO-04 — locomotion_experience field on EloSelfState**  
Self-contained addition to `self/elo_self_model.py`. Requires: (a) adding the field, (b) populating it from Unity ACKs and desktop move events, (c) a `describe_embodiment_walking()` method. No FREEZE_V1_LOCK files touched.

**B-ISELO-05 — drift guard corrective action**  
`check_identity_drift()` in `self/elo_self_model.py` is not frozen. Options: (a) flag for re-prompt, (b) inject a correction fragment into the response suffix, (c) block the response and regenerate. Board must decide which level of correction is appropriate before Builder implements.

---

## Summary Verdict

DISENELO Presence is structurally real in its decision architecture, observation, and attention systems. It has the bones. The gaps are primarily in the **persistence layer** (learning that resets), the **curiosity layer** (not built), and the **causal feedback loop** (state changes that don't flow back into Executive decisions). The IS ELO "Causally Real?" layer surfaces all of these — these are not aspirational gaps, they are places where the architecture declares a capability that the running code does not actually deliver.

The system is not pretending to be more than it is — it genuinely has autobiographical memory, provenance, a single decision authority, dream state, novelty detection, and initiative. But failure learning, curiosity, cross-session referent continuity, and locomotion experience differentiation are real gaps, not edge cases.

---

*Builder lane. Board closes WOs. Builder moves JSON to board_review.*
