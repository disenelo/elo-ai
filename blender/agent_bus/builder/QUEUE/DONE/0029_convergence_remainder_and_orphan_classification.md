# 0029 — The rest of the convergence audit. **Every remaining finding, carded.**

**Seat:** builder · **Priority:** P1 after `0028` · **Gate?** none
**Graph:** `Output/ONE_BRAIN_CONVERGENCE_AUDIT.md`. `0028` holds the top five; this card holds the rest so
**nothing sits in a document waiting to be relayed back.**

---

## 🔴 D — AUTHORITY CONFLICTS (two systems, one role)

| # | Fix |
|---|---|
| **D1** | **Two intent authorities, disjoint vocabularies.** Executive decides on `core/attention.py:65,313` intent; the journal + prompt report `intent_engine.py:226` intent (`spine.py:158`). **The recorded "why" can name an intent the Executive never saw.** ⇒ one intent authority, or an explicit named translation. **Say which you chose.** |
| **D2** | **Two "where am I" authorities.** `live_world_state.py:214` hardcodes `surface="mac"`; `elo_self_state.surface` says `"top edge of Spotify"` (from Unity `perch_state.json`, `server.py:3193`). **Only the second reaches speech.** ⇒ one authority; the other becomes a projection |
| **D3** | **Three capability-health systems.** `Capability.health_state` (no writer — `0028` A1) · `faculty_health.py` (4 faculties, different enum) · `capability_learning.py` (**imported by nothing**). ⇒ one, with the other two either feeding it or retired |
| **D5** | **Two self-model load/save cycles racing.** `truth_sync.py:147-149` vs `server.py:99` global + **7× `_self_save`**. **Live clobber evidence: `last_reflection_lesson=""` against 905 growth-journal rows.** ⇒ one owner, or read-modify-write under a lock |
| **D6** | **`server.py:438` `_SIGNAL_WORDS` turns "where are you" into a body command** before any cognition. A perception question consumed as locomotion. ⇒ questions must not be intercepted as movement |
| **D7** | **`server.py:2456-2472`/`:2483-2496` regex rewrites the Executive's action after the fact.** Honestly journalled as `original_action`, but it makes `server.py` a second decider. ⇒ move the rule into the Executive or record it as sanctioned post-processing |
| **D8** | **`server.py:3405-3413` `intent_gatekeeper` can veto the Executive's entire capability decision.** ⇒ demote to a *proposal* the Executive confirms |

## 🔴 A — GAPS (nobody owns it)
- **A2 · Executive emits no alternatives.** `executive.py:138-235` evaluates nine and returns one; 129/130 journal rows have `alternatives_rejected: []`. **Nothing can populate it at decision time.** *(Extends `05b_WO-112` — that card records the set, this one requires the set to exist.)*
- **A3 · No Goal anywhere.** `working_memory.active_goals` never appended (`:246`); `elo_self_model.goal` has no writer (live `""`). **eLo cannot want anything that survives a turn.**
- **A4 · Governance ladder is docstring-only** (`emergent_cognition.py:17-18`). No arbitration function exists. **Needed before agency can be safe.**
- **A5 · No Event layer.** `window_event_faculty.py` has **zero non-test callers**; significance scores raw strings.
- **A6 · `identity_meaning.py:164 flag_value_change`** — the one sanctioned identity-change route — **zero callers.**
- **A8 · Where eLo was is never remembered.** No `plan.world` → memory path.

## 🔴 B — INTEGRATION FAILURES
- **B3 · `outcome=` still not supplied.** `journal_router.py:105,122` forwards it correctly; **`server.py:3539` omits it** ⇒ `embodiment`/`efficiency`/`safety`/`reward` never scored. **One argument at one call site.** *(I previously counted this fixed — the plumbing was, the caller wasn't. My error.)*
- **B4 · `stability` + `cognitive_load` dropped** between `executive.py:386-388` and `plan.py:34-41` ⇒ `prompt_builder.py:413` stability directive is **unreachable**; journal `cognitive_load` is `""` on every recent row.
- **B5 · `live_world_state.py:350-355` reconstructs `DesktopState` without `available=`** ⇒ defaults back to `True`. **This is the one world field the Executive reads.** Use `dataclasses.replace()`.
- **B6 · `_IDENTITY_POOL` is 7 hardcoded strings** (`server.py:1333-1345`), not rendered from `identity_name`. **Change the name in state and the answer doesn't change.** And `"what's your name"` isn't even a trigger.

## 🔴 C — ROUTING
- **C3 · Dead capability choices.** `wikipedia`, `camera`, `terminal`, `app_launch`, `volume` have registry entries and **no `_AGENTS` function** (`tool_router.py:827-849` vs `:856-881`). The Executive can select an executor that cannot exist. ⇒ **assert at startup that every registry id has an executor.**
- **C4 · "What can you do" never reads the registry.** `server.py:1077` → `spine.py:350` → a 7-string pool at `:1079`, while `server.py:3861-3876` shows the **real** list in a Unity panel on the same turn. Two answers to one question.
- **C5 · Agency written 650 lines too late.** `plan.internal_intent` set at `server.py:3055` — after the Executive at `:2401`. **Temporally impossible to consult.** Move the emergent-intent computation before the spine, or accept it as next-turn input and label it so.

## 🟡 G · `lifetime_threads` is stopwords
Live contents: `["stand",2] ["didn't",2] ["doing",2] ["should",2]`, max 2 against a threshold of 3
(`identity_meaning.py:66`). **The long-term identity anchor has never fired, and its contents are
meaningless.** It's an untokenised word-frequency counter. ⇒ tokenise and stopword-filter, or replace the
input.

---

## 🟠 E/F · THE ORPHAN CLASSIFICATION — **classify, do NOT rewrite**
Per the Chief Architect: *"Not rewritten. **Classified.**"* Assign each one label:
**A** participating · **B** integrated but unverified · **C** implemented but orphaned · **D** canon-only ·
**E** superseded · **F** dead/deprecated.

`plan.embodiment_state` · `plan.cognitive_state` · `plan.internal_intent` · `cognitive_state_focal` ·
`surface_affordances` · `wm_mode` · `wm_budget` · **11 of 12 `LiveWorldState` domains** ·
`capability_learning.py` · `decision_journal.jsonl` · `last_reflection_lesson` ·
**`significance_faculty.py`** *(a complete second significance authority nothing imports)* ·
`vault_layer.recall_context` · **`personality_evolution_faculty`** *(entire faculty)*.

> *"That will probably reveal the repository is far more complete than the runtime — and that a significant
> amount of code can be retired. **That is healthy.**"*

**Deliverable: the table with a label and one line of reasoning per row. Not fixes. Not deletions.**
**F-labelled items come to me for a retirement ruling — do not delete anything yourself.**

## Reporting standard
Four labels only: **ORPHANED · NON-PARTICIPATING · UNVERIFIED · CLAIMED-NOT-PROVEN.**
**Never upgrade UNKNOWN.** Transcripts, not test counts.
