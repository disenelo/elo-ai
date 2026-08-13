---
chapter: 1
title: "The Turn Loop — The Canonical Order, Transcribed From Live Code"
volume: IV
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: LIVE (this chapter describes what runs today; it does not instruct it)
audit_status: OPEN
grounded_in: runtime/spine/spine.py · runtime/spine/plan.py · runtime/contracts.py · server.py
irv_date: 2026-08-13
dependencies:
  - Volume_IV/00_Metadata.md (the status vocabulary — Ch.1 is a transcription, not an instruction)
  - Volume_IV/02_Ordering_Guarantees_and_Invariants.md (what this order GUARANTEES; the law half)
  - 16_runtime_contracts.md (the contract vocabulary)
  - Volume_XVI/02_Executive_Assembly_One_Plan.md · Volume_VII/02_Executive_Assembly_and_The_Moment.md
---

# Chapter 1: The Turn Loop

## 1.0 Purpose

**This chapter turns a comment into a contract.**

Until 2026-08-13 the turn order existed in exactly one place: the comment block at
`runtime/spine/spine.py:331–337` and the section dividers beneath it. Four written volumes
(XII, XV, VI, XVI) and one ADR (Exec-006) state guarantees that are true *only because of that
order*, and nothing outside the file recorded it. Reorder two lines and four ratified-track
volumes become quietly false.

What follows is the order **as it actually runs**, read line by line on 2026-08-13. Every step
carries its file and line. Where the code disagrees with existing canon, the disagreement is
stated in place, **the code is marked current truth**, and the gap is named.

> **Precedence note (Vol IV §Status vocabulary).** `16_runtime_contracts.md` says *"If code
> conflicts with this document, the document is right."* That does not apply to this chapter.
> This chapter is the *record* of the live order; Chapter 2 is the *law* about it. Where they
> differ, Chapter 2 names a violation and an owner — it does not pretend the code already
> complies.

## 1.1 The turn has a prologue that is not in the spine

The single most important structural fact, and the one no document previously stated:

**`spine.run()` is not the whole turn. It is the second half of it.**

```
server.py  (the "pre-spine prologue" — NOT in runtime/spine/)
  :2321   attention_model = attn.compute(raw, _memory_pack, _state, loop_detected=False)
  :2322   exec_decision   = exec_decide(attention_model, loop_detected=False, user_input=raw)
             ▲ THE REAL EXECUTIVE DECISION — runtime/executive.py:262 decide()
             │ Nothing has been assembled at this point in the turn.
          ⋮  (~600 lines of turn handling: overrides, tool routing, prompt assembly)
  :2925   _attention_with_exec["_exec_decision"] = exec_decision
  :2926   _plan = _spine_run(raw, state=_state, attention=_attention_with_exec,
  :2927                      memory_pack=_vault_ctx)
             │
             └──────────► runtime/spine/spine.py:321  def run(...)
  ⋮
  :3346   _spine_update(raw, response)      ← spine.py:514 update_session() — continuity write
```

Three consequences that every other volume must reason with:

- **Memory is READ before the spine is entered**, not inside it. `_memory_pack` and `_vault_ctx`
  are built in `server.py` upstream of `:2321` and handed to `spine.run()` as the
  `memory_pack` argument (`spine.py:325`). The spine never reads memory itself.
- **Attention (`core/attention.py`) is computed before the spine**, at `server.py:2321`, and
  arrives as the `attention` dict (`spine.py:326`). Per **Ruling B** this module is a *Memory
  Relevance Filter* — a **supplier**, not the attention driver. The actual attention
  competition runs inside the spine at `spine.py:398` (§1.2.3).
- **The Executive decision is made before the spine is entered**, at `server.py:2322`, and is
  smuggled in as a dict key on the attention argument (`server.py:2925`). This is the runtime
  violation of Ruling C. See §1.2.8 and Ch.2 §2.3.

**Naming (proposed — `IV-3`):** the `server.py` section from the memory read through
`server.py:2925` is **the pre-spine prologue**. Naming it is not an endorsement of it; it is so
that "the turn order" has one name for the whole turn instead of describing only the part that
happens to live in `runtime/spine/`. Closing IV-1 (moving `decide()` into the spine) is the act
that dissolves the prologue.

## 1.2 The canonical order — `spine.run()`, step by step

`runtime/spine/spine.py:321` — `def run(raw, state, memory_pack, attention, pending_sit) -> CognitivePlan`

The file's own docstring (`spine.py:331–337`) declares this pipeline:

```
[WO-052] CognitiveSnapshot (assembled first, pushed to Executive) →
Language → Relationship → Capability → System →
Executive → [COGNITIVE PLAN] →
Executive Faculty (enrich: relationship + emotional vector) →
Light Engine → [PRESENCE PLAN] →
Conversation Faculty
```

**That docstring is incomplete.** It predates WO-CANON-XII/XV/VI and omits the first three
stages entirely, and it omits `build_embodiment_state`. The real order, verified line by line,
is the fourteen positions below. *(Gap: the docstring should be brought up to this list —
Builder lane, cosmetic, not load-bearing.)*

---

### Position 1 — PERCEPTION · `spine.py:353–359`

```python
# ── WO-CANON-XII: perceive() first — sensation caches → frozen PerceptionResult ─
_perception = None
try:
    from faculties.perception.perception_faculty import perceive_from_live_state as _perceive
    _perception = _perceive()          # spine.py:357
```

| | |
|---|---|
| **Runs** | first, before anything else in the spine |
| **Produces** | `PerceptionResult` (frozen — `faculties/perception/perception_faculty.py:157`) |
| **Contributes to `CognitiveState`** | **indirectly only** — it is passed to world assembly (§1.2.2), which copies fields out of it |
| **Owning volume** | XII (Perception) |
| **On failure** | `_perception = None`, logged at DEBUG, turn continues |

**⚠️ Gap found (IRV 2026-08-13).** The comment at `spine.py:462` reads *"WO-CANON-XV/XII: Store
frozen world + perception on plan"*, but line 463 stores **only** `plan.world = _world`. There
is no `plan.perception`. `PerceptionResult` survives the turn **only** through whatever
`assemble_world_state()` copied out of it. **Code is current truth: perception is not pinned.**
Consequence: nothing downstream — including the decision journal and any future
`ExecutionReport` — can inspect what was actually perceived this turn.

---

### Position 2 — WORLD STATE · `spine.py:361–368`

```python
# ── WO-CANON-XV: LiveWorldState — assembled FIRST, frozen, read by all faculties ─
# Copies PerceptionResult fields into domain slices (Ch.3 §3.2 copy step).
_world = _assemble_world(turn_id=raw[:32] if raw else "", perception=_perception)   # spine.py:366
```

| | |
|---|---|
| **Runs** | second — **after** perception, **before** every faculty |
| **Produces** | `LiveWorldState` (frozen — `world/live_world_state.py:129`; assembled by `:156`) |
| **Contributes to `CognitiveState`** | yes — `world_state=` (`spine.py:450`), lands in `CognitiveState.world_state` (`contracts.py:157`) |
| **Also pinned to** | `plan.world` (`spine.py:463`) |
| **Owning volume** | XV (World Model) |
| **On failure** | `_world = None`; every consumer sees `None` and must not fabricate |

**Guarantee delivered:** Vol XV §1.4 — *"Assembly runs once, at the top of the turn, before
faculties reason."* ✅ **Satisfied.** This is the position that makes it true.

**⚠️ Gap found — `IV-4`.** `turn_id=raw[:32]` is the user's text, not a turn identifier. Two
identical inputs share a turn id; a silent turn yields `""`. Vol XV §1.8 requires `expires` /
perishability keyed on the turn. **Code is current truth; the identifier is wrong.** Fix
recommendation in `00_Metadata.md` (IV-4).

---

### Position 3 — WORKING MEMORY + ATTENTION · `spine.py:370–418`

```python
# ── WO-CANON-VI: Working Memory + Attention — top-of-turn, before faculties ─
# core/attention.py = candidate/signal supplier. WM competition = sole driver.
_carry      = _wm_load_carry()                                       # spine.py:384
_wm         = _wm_seed(current_task=…, continuity_summary=…, open_threads=…)   # :385
_wm_candidates = [ AttentionCandidate(raw[:80], …) ] +
                 [ AttentionCandidate(m, …) for m in attention["high_priority_memory"][:4] ]  # :392–396
_distress   = attention["emotional_context"]["inferred_state"] == "distress"    # :397
_attn_state = _wm_attn(_wm_candidates, budget=0.5, distress=_distress)          # :398
_frame      = CognitiveFrame(frame_id=…, content=raw[:200], turn=0, significance=0.5)  # :400
_wm_updated = _wm_update(_wm, _frame)                                # :405
_wm         = WorkingMemory(…, attention=_attn_state, …)             # :406–416  ← re-frozen
```

| | |
|---|---|
| **Runs** | third — after world, **before** any faculty |
| **Produces** | `WorkingMemory` (frozen, carrying `AttentionState`) — `runtime/working_memory.py:85` / `:61` |
| **Contributes to `CognitiveState`** | yes — `working_memory=` (`spine.py:450`) → `CognitiveState.working_memory` and `.attention_state` (`contracts.py:160–161`, extracted at `spine.py:574`) |
| **Also pinned to** | `plan.working_memory` (`spine.py:465`) |
| **Owning volume** | VI (Working Memory / Attention) |
| **On failure** | `_wm = None`; `attention_state` becomes `None` |

**Ruling B is satisfied in code, and this is where.** `core/attention.py`'s output arrives from
the prologue as *candidates* (`spine.py:394`) and as a distress *signal* (`:397`); the winner is
decided by `run_attention_competition()` at `:398`. One competition, one answer to "what is eLo
attending to."

**Note on the re-freeze at `:406–416`.** `update_working_memory()` returns a new frozen object
without the new attention state, so the spine constructs a **second** `WorkingMemory` carrying
both. There is exactly one frozen WM that leaves this block. This is correct but non-obvious;
recording it so it is not "simplified" away.

---

### Position 4 — SNAPSHOT / `UnifiedCognitiveState` · `spine.py:420–426`

```python
# ── WO-052: CognitiveSnapshot — assembled BEFORE any faculty decides ──────
_snapshot = _build_snap(attention=attention, pending_sit=pending_sit)   # spine.py:424
```

| | |
|---|---|
| **Runs** | fourth — before every faculty |
| **Produces** | `CognitiveSnapshot`, aliased **`UnifiedCognitiveState`** (`runtime/cognitive_snapshot.py:41`, alias at `:97`, builder at `:102`) |
| **Carries** | self-model · faculty health · attention (intent/valence/momentum) · `BodySchema` (incl. `pending_sit`) · `pending_intentions` · affordances · perception scope · `confidence` · `assembled_ts` · `turn_id` |
| **Contributes to `CognitiveState`** | **NO** — it is *not* passed to `assemble_cognitive_state()` |
| **Pinned to** | `plan.snapshot` (`spine.py:459`) — **after** the Executive |
| **Owning volume** | VII Ch.2 (the ordering law) · XVI Ch.2 (the mechanism) |

**⚠️ Four assembled objects ride the plan, not one.** `plan.snapshot`, `plan.cognitive_state`,
`plan.world`, `plan.working_memory` (`spine.py:459–465`). Vol VII §2.2 names this precisely:
*"Four objects that should be one is the residual shape of the problem Ruling C exists to
end."* **Code is current truth: convergence has not happened.** Volume IV records the shape; the
convergence is WO-CANON-XVI / VII's work, by **extension** of `cognitive_snapshot.py`, never a
parallel assembler.

---

### Position 5 — LANGUAGE FACULTY · `spine.py:428–429` (impl. `:29–70`)

```python
language = _language_faculty(raw)        # spine.py:429
```

Internally, three sub-stages, each independently degradable:
`meaning_engine.normalise()` (`:43`) → `typo_engine.repair()` (`:52`, applied only at
`confidence ≥ 0.80`) → `intent_engine.detect()` (`:61`).

| | |
|---|---|
| **Produces** | `dict{original, meaning, register, social, intent, intent_chain, confidence}` |
| **Contributes to `CognitiveState`** | `raw_input` ← `original` · `intent_signal` ← `intent` · `register` · `social_signal` (`spine.py:577–580`) |
| **Rule** | *"Never chooses. Only interprets."* (`spine.py:26`) |
| **On failure** | each sub-stage falls back independently; `confidence` is the running `min()` |

**⚠️ Note.** `register` is initialised `""` at `spine.py:38` and **never written** by the
language faculty. It is populated later — from the Executive's output at `spine.py:173`, then
back-synced into the frozen `CognitiveState` at `spine.py:478–483` via `dataclasses.replace`.
That back-sync is the **only mutation of a frozen contract in the entire spine**, and it is
explicitly justified in-code as "AC-5". Recorded here rather than left as a surprise; Ch.2 §2.7
rules on whether it is permitted.

---

### Position 6 — RELATIONSHIP FACULTY · `spine.py:431–437`

```python
relationship = rel_analyse(raw, memory_pack)     # spine.py:435
```

| | |
|---|---|
| **Produces** | relationship analysis (`runtime/spine/relationship_faculty.py`, 187 lines) |
| **Contributes to `CognitiveState`** | 🔴 **NOTHING.** It is not an argument to `assemble_cognitive_state()` (`spine.py:448–451`) |
| **Consumed by** | `executive_faculty.enrich(plan, relationship, attention)` at `spine.py:470` — **after** the Executive |

**🔴 Canon-vs-code disagreement.** `16_runtime_contracts.md` lists *"Relationship Faculty"* in
the `CognitiveState` assembly chain, and `contracts.py:106–112` declares five relationship slots
(`person_id`, `relationship_type`, `familiarity`, `trust`, `expression_posture`).
**None of them is ever written.** Relationship reaches the *plan*, not the *state*, and it
arrives after the decision. **Code is current truth: relationship does not inform the decision.**
Full treatment in Ch.3 §3.4.

---

### Position 7 — CAPABILITY FACULTY · `spine.py:439–440` (impl. `:78–117`)

```python
capabilities = _capability_faculty(language["meaning"], language["intent"])   # spine.py:440
```

Scores `ALL_CAPABILITIES` by verb match (`:87–98`), then boosts router-confirmed candidates by
`+5` via `agent_router.route()` (`:105–113`), sorts, returns **top 4** (`:117`).

| | |
|---|---|
| **Depends on** | Language (position 5) — it consumes `meaning` and `intent` |
| **Produces** | `list[dict{id, category, score, requires_confirmation, health}]` |
| **Contributes to `CognitiveState`** | `capability_candidates` as a tuple of `(name, available, latency_ms)` (`spine.py:569–572`) |
| **Rule** | *"Never chooses which capability to use. Lists candidates."* (`spine.py:75`) |

**⚠️ Shape mismatch.** The tuple builder reads `c.get("name")`, `c.get("available")`,
`c.get("latency_ms")` (`spine.py:570`) but `_capability_faculty` emits `id`, `health`, and no
latency (`spine.py:92–98`). The `or c.get("id", "unknown")` fallback saves the name; **every
candidate is therefore reported `available=True` and `latency_ms=0` regardless of its real
`health`**, including `OFFLINE`. Ch.3 §3.3.

---

### Position 8 — SYSTEM FACULTY · `spine.py:442–443` (impl. `:124–131`)

```python
system_det = _system_faculty(language["meaning"])     # spine.py:443
```

Returns `(action, arg)` or `None` from `tools.system_agent.detect()`. Depends on Language.

---

### Position 9 — 🔴 ASSEMBLY · `spine.py:445–453` (impl. `:544–588`)

```python
# ── WO-CANON-XVI / ADR-Exec-006: Assemble unified cognitive state BEFORE Executive ──
_cognitive_state = assemble_cognitive_state(
    language, memory_pack, attention, capabilities, None, state,
    world_state=_world, working_memory=_wm,
)                                                     # spine.py:448–451
```

| | |
|---|---|
| **Produces** | `CognitiveState` — **frozen** (`contracts.py:73`) |
| **Position** | **before** `_executive_faculty()` at `:456`. ✅ *Within this file, Ruling C holds.* |
| **Confidence** | degrades: `−0.15` no attention · `−0.05` no capabilities · `−0.05` no memory (`spine.py:561–567`) |
| **Populates** | 11 slots of ~50 (`spine.py:576–588`) — see Ch.3 §3.3 |

**Note the fifth positional argument: `None`.** That is `vault_result` (`spine.py:549`) — the
vault contribution is hard-coded absent. And `memory_result` (= `memory_pack`) is used **only**
for the confidence deduction at `spine.py:566`; not one memory field is copied into the state.

---

### Position 10 — 🔴 EXECUTIVE FACULTY · `spine.py:455–456` (impl. `:139–206`)

```python
# ── Executive Faculty — ONE DECISION ─────────────────────────────────────
plan = _executive_faculty(raw, language, attention, capabilities, system_det)   # spine.py:456
```

| | |
|---|---|
| **Produces** | `CognitivePlan` — `runtime/spine/plan.py:22` (**mutable**, not the frozen `contracts.py:175` one) |
| **Reads** | `raw`, `language`, `attention`, `capabilities`, `system_det` |
| **Does NOT read** | 🔴 **`_cognitive_state`.** The assembled object is not an argument. |

**🔴 THE CENTRAL FINDING. `_executive_faculty()` does not decide.** At `spine.py:162`:

```python
exec_out = attention.get("_exec_decision", {})
```

It reads back the decision made at `server.py:2322` and copies `action`, `cal_reason`, `tone`,
`max_sentences`, `response_goal`, `valence`, `momentum`, `mode`, `register` onto the plan
(`spine.py:161–175`). **It transcribes a decision; it does not make one.**

What it *does* decide independently: the execution gate for system actions (`:178–190`) and
capability selection — first candidate whose health is not `OFFLINE`/`AUTH_REQUIRED`/`DISABLED`,
one per turn, two if `intent_engine` found a chain (`:192–204`).

**Consequence:** the assembly at position 9 is a **description of** the decision, not an
**input to** it. Ruling C / ADR-Exec-006 D4 is satisfied on paper inside this file and
**violated in the live turn**. Ch.2 §2.3 is the invariant and its test.

---

### Position 11 — PINNING · `spine.py:458–465`

```python
plan.snapshot        = _snapshot          # :459
plan.cognitive_state = _cognitive_state   # :461
plan.world           = _world             # :463
plan.working_memory  = _wm                # :465
```

Four frozen objects attached to a **mutable** plan, *after* the decision. The plan carries them;
it did not reason from them.

---

### Position 12 — ENRICHMENT · `spine.py:467–483`

```python
plan = enrich(plan, relationship, attention)      # spine.py:470  (executive_faculty.py, 172 lines)
# AC-5 register back-sync into the frozen CognitiveState:
plan.cognitive_state = _dc_replace(plan.cognitive_state, register=plan.register)   # :481
```

Adds the relationship context and the emotional vector to the plan. The `dataclasses.replace`
at `:481` is the single point where a frozen contract is re-created mid-turn (§1.2.5, Ch.2 §2.7).

---

### Position 13 — LIGHT ENGINE → PRESENCE · `spine.py:485–499`

```python
plan = translate(plan)                                              # :489  light_engine
plan = _pf_compute(plan, attention, vision=_vision, session_min=0)  # :497  presence_faculty (452 lines)
```

Emotional vector → `PresencePlan` (movement intent + triggers). **Presence runs after the Light
Engine**, deliberately: presence reads the emotional state the light engine resolved. Note
`session_min=0` is a hard-coded conservative default (`:496`) — the 20-minute calm gate is
therefore never satisfied from this call path. Recorded, not judged; owner is the Presence lane.

---

### Position 14 — 🔴 EMBODIMENT · `spine.py:501–506` (impl. `:591–611`)

```python
plan.embodiment_state = build_embodiment_state(plan)    # spine.py:503
```

Produces the frozen `EmbodimentState` (`contracts.py:270`) from `plan.presence_plan`:
`emotional_state` → `robot_led_state` via `_LED_FROM_EMOTIONAL_STATE` (`spine.py:528–541`),
`motion_command = dict(presence_plan)`, `published_at` = UTC ISO.

**🔴 ORDERING VIOLATION — it runs one position too early.** At `spine.py:599`:

```python
resp = getattr(plan, "direct_response", "") or ""
```

and `plan.direct_response` is set by the **Conversation Faculty at position 15**
(`spine.py:509`). On every direct-response turn, `EmbodimentState.response_text`,
`.display_text` and `.tts_text` are published **empty**. **Code is current truth: the body is
handed an empty utterance.** Fix is a two-line reorder — `build_embodiment_state` must follow
`_conversation_faculty`. Flagged to David as **IV-2**; the Architect does not touch product code
(Rule #3). Ch.2 §2.6.

---

### Position 15 — CONVERSATION FACULTY · `spine.py:508–509` (impl. `:214–314`)

```python
plan = _conversation_faculty(plan)      # spine.py:509
return plan                             # spine.py:511
```

Sets `plan.direct_response` for turns needing no LLM, in this **fixed precedence**
(`spine.py:228–309`): system-immediate → system-confirm → Rasta affirmation → farewell → pure
greeting → how-are-you → thank-you → identity → self-reference. Each branch returns
immediately; register (`PATOIS` / `HYBRID` / `SOUTH_LDN` / neutral) selects the response pool.
If no branch matches, `direct_response` stays empty and `plan.needs_llm()` is `True`.

**Note:** this faculty imports `server` (`spine.py:226`) to reach the response pools — a
runtime→server dependency that inverts the intended layering. Recorded; Volume III §2 owns the
boundary question.

---

### After the return — CONTINUITY WRITE · `server.py:3346` → `spine.py:514–520`

```python
def update_session(user_input: str, elo_response: str = "") -> None:
    from runtime.router.conversation_matrix import push
    push(user_input, elo_response)
```

**This is the memory WRITE, and it happens after the response exists.** It is the only write
the spine performs. Memory read (prologue) → decide → express → memory write. Ch.2 §2.4.

## 1.3 The order, in one block

```
── PRE-SPINE PROLOGUE (server.py) ──────────────────────────────────────────
   memory read (_memory_pack, _vault_ctx)              upstream of :2321
   attention supplier          core/attention.py       server.py:2321
   🔴 EXECUTIVE DECISION       executive.py:262        server.py:2322   ← before any assembly
   inject decision into attention dict                 server.py:2925
   enter the spine                                     server.py:2926

── SPINE (runtime/spine/spine.py:321 run()) ────────────────────────────────
    1  PERCEPTION          perceive_from_live_state()   :357   → PerceptionResult (frozen)
    2  WORLD               assemble_world_state()       :366   → LiveWorldState  (frozen)
    3  WORKING MEMORY      run_attention_competition()  :398   → WorkingMemory + AttentionState (frozen)
    4  SNAPSHOT            build_snapshot()             :424   → UnifiedCognitiveState (frozen)
    5  LANGUAGE            _language_faculty()          :429   → meaning · intent · social · confidence
    6  RELATIONSHIP        rel_analyse()                :435   → (does NOT reach CognitiveState)
    7  CAPABILITY          _capability_faculty()        :440   → top-4 candidates
    8  SYSTEM              _system_faculty()            :443   → (action, arg) | None
    9  ASSEMBLY            assemble_cognitive_state()   :448   → CognitiveState (FROZEN)
   10  EXECUTIVE FACULTY   _executive_faculty()         :456   → CognitivePlan  (mutable)
                                                                 🔴 transcribes :2322, does not decide
   11  PINNING             snapshot/state/world/wm      :459–465
   12  ENRICHMENT          enrich() + AC-5 re-freeze    :470, :481
   13  LIGHT → PRESENCE    translate(); _pf_compute()   :489, :497 → PresencePlan
   14  EMBODIMENT          build_embodiment_state()     :503   → EmbodimentState (frozen)
                                                                 🔴 built before the utterance exists
   15  CONVERSATION        _conversation_faculty()      :509   → direct_response
       return plan                                     :511

── AFTER (server.py) ───────────────────────────────────────────────────────
   response delivered · surfaces read EmbodimentState
   MEMORY WRITE           update_session()             server.py:3346 → spine.py:514
```

## 1.4 What each position contributes to `CognitiveState`

| Pos | Faculty | Writes into `CognitiveState` | Line |
|---|---|---|---|
| 1 | Perception | *(indirect — via world assembly only)* | — |
| 2 | World | `world_state` | `spine.py:585` |
| 3 | Working Memory | `working_memory`, `attention_state` | `:586–587` |
| 4 | Snapshot | 🔴 **nothing — not passed to the assembler** | — |
| 5 | Language | `raw_input`, `intent_signal`, `register`, `social_signal` | `:577–580` |
| 6 | Relationship | 🔴 **nothing** | — |
| 7 | Capability | `capability_candidates` | `:584` |
| 8 | System | 🔴 **nothing — goes straight to the plan** | — |
| — | Attention supplier (prologue) | `momentum`, `valence` | `:581–582` |
| — | Assembler | `assembly_confidence` | `:583` |

Eleven slots written. `contracts.py` declares roughly fifty. Ch.3 §3.3.

## 1.5 What canon says vs. what the code does — the register

| # | Canon says | Code does | Verdict |
|---|---|---|---|
| 1 | ADR-Exec-006 D4 / Ruling C: assembly precedes the decision | `exec_decide()` at `server.py:2322`; assembly at `spine.py:448` | 🔴 **VIOLATED at runtime.** In-file order correct; process order wrong. Owner: Builder (IV-1) |
| 2 | `16_runtime_contracts.md`: Relationship contributes to `CognitiveState` | Relationship reaches `enrich()` after the decision | 🔴 **False.** Code is truth (§1.2.6) |
| 3 | `16_runtime_contracts.md`: `CognitivePlan` "frozen at production" | `spine/plan.py:22` is a plain `@dataclass`, mutated at `:459–465, :470, :489, :497, :503, :509` | 🔴 **False.** Two `CognitivePlan` classes exist; the spine uses the mutable one |
| 4 | `contracts.py`: `CognitiveState` "frozen after assembly — immutable by contract" | `dataclasses.replace` at `spine.py:481` re-creates it mid-turn | ⚠️ **Narrow, documented exception (AC-5).** Ch.2 §2.7 |
| 5 | Vol XV §1.4: world assembled once, top of turn, before faculties | `spine.py:366`, position 2 | ✅ **Satisfied** |
| 6 | Vol VI / Ruling B: one attention competition drives the turn | `spine.py:398`; `core/attention.py` supplies candidates | ✅ **Satisfied** |
| 7 | Runtime Invariant #2: one decision per turn | exactly one `_executive_faculty()` call; no second decider in the spine | ✅ **Satisfied** (the decision is in the wrong *place*, not duplicated) |
| 8 | Vol VII §5.6: DOWN leg — one plan → `EmbodimentState` → surfaces | `spine.py:503`, `_LED_FROM_EMOTIONAL_STATE` | ⚠️ **Satisfied in structure, broken in content** (empty text — §1.2.14) |
| 9 | `spine.py:331–337` docstring pipeline | omits positions 1–4 and 14 | ⚠️ **Stale.** Builder lane, cosmetic |

## 1.6 Line-number drift — a note for future readers

`Volume_XVI/02` cites `server.py:2905/2906`; `Volume_VII/02` cites `server.py:2888`. **Both are
stale.** IRV 2026-08-13 reads: injection `:2925`, `spine.run()` call `:2926`. The decision site
`:2322` has held.

This is the cost of citing line numbers, and it is a cost worth paying — a stale line number is
visibly stale, whereas an unsourced claim is invisibly wrong. **Rule:** every re-verification of
this chapter re-reads the call sites and updates the numbers, and the `irv_date` in the
frontmatter is the only date a reader should trust.

## 1.7 References

- **Code (the authority this chapter transcribes):** `runtime/spine/spine.py` (621 lines) ·
  `runtime/spine/plan.py:22` · `runtime/contracts.py` · `runtime/executive.py:262` ·
  `runtime/cognitive_snapshot.py:41,:97,:102` · `world/live_world_state.py:129,:156` ·
  `runtime/working_memory.py:61,:85,:127,:182,:227` ·
  `faculties/perception/perception_faculty.py:157,:326` · `server.py:2321,:2322,:2925,:2926,:3346`
- `Volume_IV/02_Ordering_Guarantees_and_Invariants.md` — the law half of this chapter
- `Volume_IV/03_CognitiveState_The_Carrier.md` — the carrier
- `Volume_VII/02_*` (ordering law) · `Volume_XVI/02_*` (assembly mechanism) · `Volume_XV/01_*` ·
  `Volume_XI/01_*` · `Volume_VII/05_*`
- `CANON_RULINGS_2026-08-10.md` — Ruling B, C, E, F · `adr/ADR-Exec-006_*` · `adr/ADR-Exec-002_*`

---

```
Chapter 1 — The Turn Loop
Status: READY FOR REVIEW
Method: line-by-line transcription of runtime/spine/spine.py, IRV 2026-08-13
Positions recorded: 15 in the spine + a named pre-spine prologue + the post-turn memory write
Canon-vs-code register: 9 entries — 3 VIOLATED/false, 1 narrow exception, 3 satisfied, 2 stale
🔴 Two live ordering defects recorded: assemble-after-decide (server.py:2322) and
   EmbodimentState-before-utterance (spine.py:503 vs :509)
⚠️ Three quieter gaps: perception never pinned · turn_id is user text · capability health lost
Precedence: this chapter is a RECORD (code is current truth); Ch.2 is the LAW
```

READY FOR REVIEW
