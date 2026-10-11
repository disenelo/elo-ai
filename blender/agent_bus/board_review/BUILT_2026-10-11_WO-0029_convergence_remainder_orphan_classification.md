# Board Review — 0029: Convergence Remainder + Orphan Classification
**Date:** 2026-10-11
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

---

## Section D — Authority Conflicts

### D1 — Two intent authorities: ALREADY RESOLVED

`spine.py:249-253` (D1 ruling from card 0035):
- `plan.intent` = COGNITIVE intent from `core/attention.py` → what the Executive decides
- `plan.capability_hint` = router hint from `intent_engine.py` → which tool to consider

Two questions, two answers, two names. The journal records the cognitive intent. **Verified in code.** No action needed.

### D2 — Two "where am I" authorities: OPEN

- `live_world_state.py:214` hardcodes `surface="mac"` in `_health()` init
- `elo_self_state.surface` reads from Unity `perch_state.json` (updated dynamically via `server.py:3193`)

Only `elo_self_state.surface` reaches speech path. `live_world_state.py`'s surface is never used by the Executive. **Proposed disposition:** accept `elo_self_state.surface` as the single authority; remove the hardcoded `surface="mac"` from LiveWorldState (or deprecate the field). Board decision needed.

### D3 — Three capability-health systems: OPEN (0032 owns the fix)

Three systems:
1. `Capability.health_state` — constant ONLINE, no producer
2. `faculty_health.py` — 4 faculties, CONNECTED/DEGRADED/OFFLINE vocab
3. `capability_learning.py` — failure streaks; imported by spine.py, server.py, unlearn.py — NOT orphaned

Card 0032 owns the join. Builder work pending David L3 on 0032.

### D5 — Self-model load/save race: OPEN

`truth_sync.py:147-149` and `server.py:99` global both load EloSelfState. `server.py` has 7× `_self_save` call sites.
Live evidence: `last_reflection_lesson=""` against 905 growth-journal rows (one save wins, another overwrites).

**Required fix:** one owner (truth_sync), or read-modify-write under a file lock. No fix in this card — board to assign.

### D6 — _SIGNAL_WORDS intercepts perception question as body command: VERIFIED OPEN

`server.py:661`: `"where are you" → "return_elo"` (locomotion command).
`server.py:764` applies `_SIGNAL_WORDS` before any cognition — the phrase is consumed as movement, never reaching the Executive or LLM to answer "I'm at the top-left corner."

A second guard exists at `server.py:6418` that answers "where are you / can you sit / what's your pose" from spatial state — but it fires AFTER `_SIGNAL_WORDS`, so it's never reached for "where are you."

**Fix:** remove "where are you" from `_SIGNAL_WORDS`. Add it to the spatial-state query handler at line 6418 instead. Board decision: is `return_elo` the intended semantics for "where are you"?

### D7 — server.py regex rewrites Executive action post-hoc: VERIFIED OPEN

`server.py:2456-2472` and `:2483-2496` pattern-match the Executive's action after journalling and rewrite it. Honest (journalled as `original_action`) but makes `server.py` a second decider.

**Proposed fix:** move the rule into the Executive prompt/context so the Executive itself applies it, or annotate as "sanctioned post-processing" in the journal. No fix in this card.

### D8 — intent_gatekeeper can veto the Executive's capability decision: VERIFIED OPEN

`server.py:3405-3413` (approx): `intent_gatekeeper` reads the plan and can override capability selection. Demoting to a proposal the Executive confirms is the cleaner architecture, but has latency cost.

**No fix in this card.** Board to decide: veto vs. proposal.

---

## Section A — Gaps

| # | Finding | Status |
|---|---|---|
| A2 | Executive emits no alternatives (129/130 rows `alternatives_rejected: []`) | OPEN — `05b_WO-112` owns the collect; this requires the set to exist at decision time |
| A3 | No Goal anywhere — `working_memory.active_goals` never appended, `elo_self_model.goal` no writer | OPEN — eLo cannot want anything that survives a turn |
| A4 | Governance ladder is docstring-only in `emergent_cognition.py:17-18` — no arbitration function | OPEN — required before agency can be safe |
| A5 | `window_event_faculty.py` has zero non-test callers — significance scores raw strings | OPEN |
| A6 | `identity_meaning.py:164 flag_value_change` — zero callers | OPEN — sanctioned identity-change route is dead code |
| A8 | Where eLo was is never remembered — no `plan.world` → memory path | OPEN |

---

## Section B — Integration Failures

| # | Finding | Status |
|---|---|---|
| B3 | `outcome=` not supplied at `server.py:3539` → embodiment/efficiency/safety/reward never scored | OPEN — one argument at one call site |
| B4 | `stability` + `cognitive_load` dropped between `executive.py:386-388` and `plan.py:34-41` | OPEN — `prompt_builder.py:413` stability directive is unreachable; journal always `""` |
| B5 | `live_world_state.py:350-355` reconstructs `DesktopState` without `available=` → defaults True | OPEN — Executive reads `available`; false available is never propagated |
| B6 | `_IDENTITY_POOL` (7 hardcoded strings, `server.py:1333-1345`) not rendered from `identity_name` — and "what's your name" not in triggers | OPEN — name change in state doesn't change the answer (confirmed C2 fix) |

---

## Section C — Routing

| # | Finding | Status |
|---|---|---|
| C3 | Dead capability choices (`wikipedia`, `camera`, `terminal`, `app_launch`, `volume`) have registry entries, no `_AGENTS` function | OPEN — Executive can select an executor that cannot exist. 0032 startup assertion closes this |
| C4 | "What can you do" never reads the registry — `server.py:1077` → 7-string pool vs real list in Unity panel | OPEN — two answers to one question |
| C5 | `plan.internal_intent` set at `server.py:3055`, after Executive at `:2401` — temporally impossible to consult | OPEN — label as next-turn input, or move before spine |

---

## Section G — lifetime_threads is stopwords

Live contents: `["stand",2] ["didn't",2] ["doing",2] ["should",2]` — untokenised word-frequency counter, max 2 against threshold 3 (`identity_meaning.py:66`). Long-term identity anchor has never fired. **Fix:** tokenise + stopword-filter input, or replace the counter with TF-IDF or entity extraction. OPEN.

---

## E/F — Orphan Classification

Card directive: classify each item as **A** participating · **B** integrated but unverified · **C** implemented but orphaned · **D** canon-only · **E** superseded · **F** dead/deprecated. No deletions. F-labelled items go to board for retirement ruling.

| Orphan | Classification | Reasoning |
|---|---|---|
| `plan.embodiment_state` | **A — participating** | Set at `spine.py:1512` via `build_embodiment_state()`; read at `:1514`. Active every turn. |
| `plan.cognitive_state` | **C — implemented but orphaned** | Not a field on `CognitivePlan` (verified). No setter, no getter. May be a vestigial naming from before `CognitivePlan` was centralised. |
| `plan.internal_intent` | **A — participating** | Used for ambient/self-initiation turns (`server.py:1107`, `spine.py` internal_intent wiring). Active when eLo self-initiates. |
| `cognitive_state_focal` | **B — integrated but unverified** | Built into `executive_context.py:185` and `spine.py:406`; not confirmed to affect any Executive branch in tests. |
| `surface_affordances` | **B — integrated but unverified** | Populated in `executive_context.py:186`; consumed by `gap_assessment.py:188`; no test confirms Executive reads it. |
| `wm_mode` | **B — integrated but unverified** | Flows through `executive_context.py:177,177,505,520`; whether the Executive prompt uses it to change behaviour is unconfirmed. |
| `wm_budget` | **B — integrated but unverified** | Same path as `wm_mode`. Budget value flows in but no test proves the Executive responds to it. |
| **11 of 13 `LiveWorldState` domains** | **B — integrated but unverified** | Domains assembled every turn: `user`, `unity`, `browser`, `files`, `internet`, `music`, `calendar`, `environment`, `weather`, `location`, `sun` (11). **Two are confirmed read:** `desktop.available` (Executive reads at `executive.py:475`) and `gaze` (`desktop/spatial_state.py:282`). The other 11 are assembled but no turn confirms the Executive or prompt_builder reads them to change a decision. Board ruling needed on whether the assembly cost is justified. |
| `capability_learning.py` | **B — integrated but unverified** | Imported by `spine.py:196`, `server.py:5566/6128`, `self_improvement/unlearn.py:141`. Has callers — NOT orphaned. But failure_streak effect on Executive decisions is unverified. |
| `decision_journal.jsonl` | **A — participating** | Written by `_bypass_journal()` + `_dj_record()` every non-silent turn. Read by diagnostic paths. Active. |
| `last_reflection_lesson` | **B — integrated but unverified** | Written at `server.py:9013-9021`; read by `self_interpret.py:96`. The D5 save race means the written value may be immediately clobbered. |
| `significance_faculty.py` | **A — participating** | Imported by `main.py:413`, `server.py:1079`, `executive_context.py:457`. Called every turn for significance score. |
| `vault_layer.recall_context` | **B — integrated but unverified** | Called at `server.py:6627`. Returns a context dict that is injected into the prompt. Integration path is plumbed; whether the content affects LLM output is unverified. |
| `personality_evolution_faculty` | **C — implemented but orphaned** | Imported by `reflection_faculty.py:355` and `spine.py:1188`, but card 0019 + 0028 established `apply_delta`'s return value is discarded and `_try_personality_delta` has 6 defects. The whole path is unreachable dead code at runtime despite import references. **F candidate — send to board for retirement ruling.** |

---

## Board decisions requested

1. **D2**: Accept `elo_self_state.surface` as single authority? Remove hardcoded `surface="mac"` from LiveWorldState?
2. **D5**: Assign one owner for EloSelfState saves; or add file lock to all 7+ `_self_save` call sites?
3. **D6**: Remove "where are you" from `_SIGNAL_WORDS`?
4. **D7**: Sanctioned post-processing (label it) or move into Executive?
5. **D8**: Veto or proposal for `intent_gatekeeper`?
6. **11 LiveWorldState domains**: Keep assembling all 13 at the cost of sensor latency, or prune to confirmed-read domains?
7. **`personality_evolution_faculty`**: Retire (F)? Or fix the 6 defects to make it actually run?

*Builder 1 · 2026-10-11*
