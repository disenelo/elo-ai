# WO-CANON-XXV — Temporal Cognition: finish the faculty, add the envelope + lifecycle, and WIRE IT (it is dead code today)

**Owner:** Builder (eLo OS — `faculties/temporal/`). **Priority:** P3 — Tier B.
**Status:** DONE — 2026-08-27 (29/29 ATs pass; wiring verified: spine.py:837 + ambient_engine.py:590; envelope, lifecycle, cadence, thread all implemented). Board 2026-08-10 ruling: "awaiting David sign-off" retired for build queue. Previously re-opened 2026-08-13 as dead code — now fully wired and tested.

> ### ⚠ THE BOARD'S "DONE ✅" FOR VOL XXV IS FALSE
> `DISPATCH_BOARD.md:1469` reads *"**DONE ✅** auto-verified (test_canon_xxv_temporal.py 19/19) → IN_REVIEW,
> commit `e562401`"*. Verified 2026-08-13 by reading the code: **the shipped build is dead code.** The 19
> tests pass because they import the module directly. Nothing else does. This line must be corrected to
> **IN_PROGRESS / dead-code** on the board (Architect lane) and must not be carried into `COMPLETION_LOG.md`.

**Canon refs:** Volume XXV — Ch.1 `01_Time_Perception_and_Circadian_Scheduling.md` (§1.3 object, §1.7
contract, **§1.8 lifecycle**, **§1.9 envelope**, §1.11 tests), Ch.2
`02_Planning_Horizons_Deadlines_Future_Simulation.md` (§2.2 object, §2.3 horizons, §2.5 **Anticipation**,
§2.6 contract, **§2.7 lifecycle**, **§2.8 envelope**), Ch.3 `03_Memory_Ageing_and_Retrospection.md`
(§3.3 natural age, §3.4 fidelity, **§3.5 Vol XXI thread**, §3.6 contract, **§3.7 lifecycle**, **§3.8
envelope**). `Volume_V/CONTRACTS.md` §2/§3/§4. ADR-Exec-006 (The Moment) · ADR-Exec-001 (Verified Speech) ·
Runtime Invariant 7 (Memory Ownership). Scope amendment 2026-08-10: **one person — David.**

---

## IRV — what shipped (verified 2026-08-13 by reading `faculties/temporal/faculty.py`, 17,664 bytes)

| Canon requirement | Shipped state |
|---|---|
| `TemporalState` / `FutureFrame` / `Deadline` / `Retrospection` / `FramedMemory` | **Present** (L73/101/91/119/110), plus `TemporalOutput` (L129) and `compute()` (L397). The derivations (`_interaction_gap`, `_sleep_pressure`, `_deadline_proximity`, `_natural_age`, `_fidelity_from_strength`, `_active_horizon`) are real and readable. This part is good work. |
| **`Anticipation` class** (Ch.2 §2.5 — cited `basis`, confidence-weighted, `spoken` false by default, baseless ⇒ dropped) | **DOES NOT EXIST.** The word appears once, in a docstring at L17. There is no anticipation type, no `basis` field, no drop rule in code. |
| **`PlanningHorizon` as a lens over Agency's tiers** (Ch.2 §2.3 — extend, never duplicate) | **DOES NOT EXIST** as a type. Only a private `_active_horizon()` string helper. |
| **`expires` as a perishability timestamp** (Ch.1 §1.9: `"expires": "<now_ts + turn_ttl>"`) | **Shipped as `expires: bool = True`** on four dataclasses (L86/105/124/134) and `expires=True` at six construction sites. **A bool is not an expiry.** Nothing can be tested for staleness against it; a prior-turn frame cannot be rejected. |
| **Message envelope** (Ch.1 §1.9 / Ch.2 §2.8 / Ch.3 §3.8 — `sender: TemporalCognitionFaculty`, `receiver: "*"`, `priority`, `context.memory_instruction`, `payload.type`, `confidence`, `expires`, `trace`) | **ABSENT.** Zero occurrences of `sender`, `trace`, `payload`, or `receiver`. The faculty returns plain dataclasses and never publishes on the Faculty Bus. Only `memory_instruction_store: bool = False` survives — the right value, in the wrong shape. |
| **Faculty lifecycle** (Ch.1 §1.8: `INITIALISING → ACTIVE → PROCESSING → ERROR_RECOVERY → LEARNING/UPDATING → STABLE`) | **ABSENT.** Zero lifecycle states in the module. |
| **Cadence model** (Ch.1 §1.8 + scope amendment: track David's actual days; **stated outranks learned**; nothing inferred from silence) | **ABSENT.** No `learned_cadence`, no cadence tracking, no stated-overrides-learned rule. `anticipate()` in Ch.2 §2.5 takes `learned_cadence` as an input that does not exist. |
| **Vol XXI thread integration** (Ch.3 §3.5: `retrospect(query, TemporalState, thread=IdentityState[], memory=VaultRefs)`; order and frame the `continuity/` meaning-memory; `autobiography.jsonl` PENDING but specified) | **ABSENT.** `_build_retrospection(world_state, now_ts)` takes no thread and no vault refs. Nothing reads `continuity/identity_state.py`, `continuity_engine.py` or `continuity_summary.py`. The whole Ch.3 §3.5 half is missing. |
| **WIRING — something imports and uses it** | **NOTHING IMPORTS IT.** Repo-wide grep for `faculties.temporal` / `TemporalCognitionFaculty` returns **only `tests/test_canon_xxv_temporal.py`**. It is not in `runtime/spine/spine.py`, not in `runtime/contracts.py`, not in `ambient/ambient_engine.py`, not in `server.py`. `temporal_appropriateness()` (L425) — the function whose entire purpose is to advise ambient cadence and Agency's `InternalTick` — **has no caller.** |
| Upstream it depends on | `LiveWorldState` is assembled and pinned (WO-CANON-XV) but **also has no consumers**, so even the "reads the clock verbatim" path is exercised only by tests. |

**Net:** three frozen slices are computed correctly, in private, for nobody. This is exactly the failure
class the volume's own §1.1 ("One Clock, Read Once") exists to prevent — except the clock is read once by
no one.

## Problem / Goal

eLo needs to reason about the present (what part of day, how long since we last spoke), forward (deadlines,
planning horizons, cited anticipations) and backward (how a memory ages, and where we've come from) — from
**one clock, read once**, with **no autonomous loop** (the only heartbeat is Agency's `InternalTick`,
Vol V Ch.10). Today he cannot, because the faculty that does it is not connected to anything.

Goal: complete `TemporalCognitionFaculty` to the full three-chapter spec — including the envelope, the
lifecycle, the cadence model and the Vol XXI thread — and **wire it into the turn so a real consumer reads
it**, with a test that fails if nothing imports it.

## Scope to DoD

**A. The missing types (Ch.2).**
- Build **`Anticipation`**: `{statement, basis ∈ {learned_cadence, pattern_memory, calendar_gap},
  confidence, spoken: bool = False, ref}`. **Baseless anticipation is DROPPED, not softened** (§2.5).
  Confidence-weighted; low-confidence stays private context or is dropped; never rounded into a claim.
  It never triggers an action — it surfaces to Agency/Executive as context (§2.1).
- Build **`PlanningHorizon`** as a **lens over Agency's existing tiers** (immediate / short_term /
  long_term / identity_goals) — **extend, never duplicate**. Horizon is chosen by the nearest binding
  constraint, not by mood. `priority` may rise to `high` only when `nearest_deadline.proximity == imminent`
  (§2.4) — still context, never a command.
- Keep the existing `Deadline` rule: every deadline MUST carry a `ref` (calendar event id / goal
  `success_condition` / stored user statement); no ref ⇒ not a deadline. Calendar deadlines read from the
  frozen `LiveWorldState.calendar`, never from the calendar agent directly; surfaced without the sensitive
  title when there is no downstream need. Passed deadline hands off to Ch.3 (no double ownership).

**B. The envelope — replace `expires: bool` (Ch.1 §1.9 / Ch.2 §2.8 / Ch.3 §3.8).**
- Emit a real envelope per `Volume_V/CONTRACTS.md §2`: `sender` MUST be `TemporalCognitionFaculty`;
  `receiver: "*"` (the temporal frame is part of The Moment → broadcast); `priority: normal`;
  `payload.type ∈ {temporal_state, future_frame, retrospection}`; `confidence == <slice>.confidence`;
  **`expires = now_ts + turn_ttl` (a timestamp, not `True`)**; `trace: ["TemporalCognitionFaculty@ts"]`;
  `context.memory_instruction.store` MUST be `false`.
- `expires: bool` is **retired**, not aliased. A frame from a prior turn must be rejectable as expired —
  that is the whole point of perishability and it is untestable against a bool.

**C. The lifecycle (Ch.1 §1.8 / Ch.2 §2.7 / Ch.3 §3.7).**
- Implement the universal lifecycle: `INITIALISING` (load the default circadian curve + threshold table;
  attach to the continuity cadence) → `ACTIVE` (idle, **no self-timer — this is the whole point**) →
  `PROCESSING` (on assembly: read `LiveWorldState.time` → derive → contribute to The Moment) →
  `ERROR_RECOVERY` on a time-domain fault (neutral circadian, `circadian_phase=active`, energy 0.5,
  **never block**) → `LEARNING/UPDATING` (integration window only) → `STABLE` → `ACTIVE`.
- The only `UPDATING` is threshold/curve tuning and tracking David's rhythm. It proposes **no**
  `PersonalityDelta` — a tracked rhythm is a preference, not an identity change (Vol V Ch.7 owns traits).

**D. The cadence model (Ch.1 §1.8 scope amendment + Ruling XXVI, 2026-08-10).**
- Track **David's** actual days (one person; no user segmentation, no "daily vs monthly user", no settings
  surface). Learned cadence is the **fallback**.
- **David's stated direction outranks anything learned, and nothing is inferred from silence.** A rhythm
  David has stated wins over a rhythm continuity inferred. This rule must be enforced in code, not in a
  comment.
- Cadence feeds `temporal_appropriateness(behaviour_kind, TemporalState) -> {allow, reason}` as **advice**.
  Cadence stays owned by `ambient/ambient_engine.py`; the dream stays owned by Vol IX. `sleep_pressure`
  scales toward Vol IX's live thresholds (`DREAM_IDLE_THRESHOLD=600`, `DREAM_COOLDOWN=3600`) as **context
  only — it NEVER fires the dream.**

**E. Vol XXI thread integration (Ch.3 §3.5 — the whole half that was dropped).**
- `retrospect(query, TemporalState, thread, memory)` where `thread` is Vol XXI's `IdentityState` meaning-
  memory (theme · emotional_direction · active_project · what_changed · what_stayed · what_matters) read
  from `continuity/identity_state.py` / `continuity_engine.py` / `continuity_summary.py`, and `memory` is
  vault refs (Vol VIII).
- Temporal Cognition **orders and frames** that meaning in time — `thread_arc` for *"how far have we come?"*,
  `window` for *"what have we been doing lately?"* — and **does not own the thread**, does not restate
  transcripts (there are none), never writes memory, never adjusts `strength`, never runs decay.
- Every `FramedMemory` MUST carry a `ref` to a real stored record. `fidelity` (`vivid/clear/faded`) derives
  from **strength, not age**; identity-level/pinned memories always read ≥ `clear`. `natural_age` frames by
  calendar/part-of-day boundaries ("yesterday" = the calendar day flipped), never raw deltas. `gaps` are
  stated honestly and never filled; a faded memory is narrated as faded, never confidently reconstructed.
- `self/journals/autobiography.jsonl` (WO-078) is **not live** — spec how retrospection *would* consume it
  (each entry a `ref`-bearing `FramedMemory`), mark the path **PENDING**, and work from vault + IdentityState
  until it exists. Do not spec it as built.

**F. WIRING — the requirement the old WO omitted, and the reason this shipped dead.**
- The faculty MUST be **imported and used by the running turn**: `compute(...)` called during assembly in
  `runtime/spine/spine.py`, its output pinned onto `CognitiveState` / the plan (alongside `world_state`,
  `runtime/contracts.py:157`), so The Moment carries the temporal frame (ADR-Exec-006).
- **At least one real consumer must read it.** Minimum: `ambient/ambient_engine.py` consults
  `temporal_appropriateness()` before a cadence decision (quiet hours suppress ambient, never a direct
  turn). A second consumer (Agency `InternalTick`) is desirable, not required for this WO.
- It stays **asked, not looping**: no background tick, no background nostalgia, no autonomous prediction
  loop. Wiring means "called during assembly", never "given a timer."
- Upstream reality: `LiveWorldState` currently has no consumers either (WO-CANON-XV). If Vol XV's
  `TimeState`/`CalendarState` are still empty when this lands, the faculty must degrade honestly
  (`interaction_gap = unknown`, no false "welcome back") — **not** fall back to `time.time()` mid-turn,
  which is an illegal re-sense.

## Files to TOUCH
- `faculties/temporal/faculty.py` (Anticipation · PlanningHorizon · envelope · lifecycle · cadence · thread)
- `faculties/temporal/__init__.py` (export the new types)
- `runtime/spine/spine.py` (call during assembly; pin the frame onto the plan)
- `runtime/contracts.py` (carry the temporal frame on `CognitiveState`, as `world_state` is carried)
- `ambient/ambient_engine.py` (the consumer — consult `temporal_appropriateness()` for cadence)
- `tests/test_canon_xxv_temporal.py` (extend — see Tests)
- `engineering/work_orders/DISPATCH_BOARD.md:1469` — **Architect lane**, relayed: correct the false DONE ✅.

## Files MUST-NOT-TOUCH
- `memory/` and anything that writes long-term memory (`memory_instruction.store` stays `false`; Vol VIII
  owns decay and writes — this faculty reports, never adjusts)
- Vol IX dream trigger constants / the dream firing path (`sleep_pressure` is context only)
- `runtime/executive.py` (FROZEN)
- `world/live_world_state.py` (WO-CANON-XV's; read it, never re-sense)
- Agency's goal tiers (extend as a lens; do not duplicate or rewrite them)

## Definition of Done
- `Anticipation` and `PlanningHorizon` exist as real types; every anticipation carries a `basis` or is
  dropped; the horizon is a lens over Agency's tiers, not a second tier system.
- A real envelope is emitted with `sender = TemporalCognitionFaculty` and **`expires` as a timestamp**; the
  `expires: bool` field no longer exists anywhere in the module.
- The lifecycle is implemented, including `ERROR_RECOVERY` on a time-domain fault that never blocks a turn.
- Cadence tracks David's actual days, and a **stated** direction demonstrably overrides a learned one.
- Retrospection reads the Vol XXI thread and vault refs, frames without owning, and marks the
  `autobiography.jsonl` path PENDING rather than faking it.
- **`faculties/temporal` is imported by non-test code, called once per turn during assembly, and at least
  one consumer acts on its output.** A build where nothing imports it does **not** satisfy this WO.
- One clock, read once; all derivations deterministic (same inputs → byte-identical output); no autonomous
  tick; the faculty never actuates and never writes memory.
- Architect can then re-check Vol XXV. **This WO does not confer DONE** — `COMPLETION_LOG.md` + David's
  sign-off does, and the current board line must be corrected first.

## Tests (`tests/test_canon_xxv_temporal.py` — the existing 19 stay)
**The wiring tests are the point of this rewrite. Write them first; they must fail before the build.**
- **WT-1 — something imports it.** Assert at least one **non-test** module under `runtime/`, `faculties/`,
  `ambient/` or `server.py` imports `faculties.temporal`. *(This test fails on the currently shipped
  build — that is intentional and is the proof the board line is false.)*
- **WT-2 — it runs in the turn.** Assert `compute()` is invoked during `spine.run()` and the resulting
  frame is reachable from the plan / `CognitiveState`.
- **WT-3 — a consumer acts on it.** Assert `ambient_engine`'s cadence path consults
  `temporal_appropriateness()` and that a quiet-hours verdict suppresses an ambient behaviour (and does
  **not** suppress a direct turn).
- **ET-1 — envelope shape.** `sender == "TemporalCognitionFaculty"`; `payload.type` is one of the three;
  `context.memory_instruction.store is False`; `confidence` equals the slice confidence; `trace` non-empty.
- **ET-2 — perishability.** `expires` is a **number**, not a bool; a frame built with a prior-turn
  `now_ts` is rejected as expired. Assert `expires: bool` no longer exists in the module.
- **LT-1 — lifecycle.** A time-domain fault drives `ERROR_RECOVERY` → neutral circadian → the turn still
  completes; no state machine value is invented outside CONTRACTS §3.
- **AT-1 — anticipation.** An `Anticipation` without a `basis` is dropped (not softened, not hedged);
  `spoken` defaults false; an anticipation never triggers an action.
- **AT-2 — horizon is a lens.** Assert no second tier enum is defined; the horizon maps onto Agency's
  existing tiers; `priority` rises to `high` only at `imminent`.
- **CT-1 — cadence.** A stated direction beats a learned one; nothing is inferred from silence.
- **XXI-1 — thread.** `retrospect()` reads `IdentityState` and returns `thread_arc`; every `FramedMemory`
  carries a resolvable `ref`; a gap is stated, never filled; a pinned memory never reads `faded`; nothing
  writes memory or adjusts strength.
- Plus the existing Ch.1/Ch.2/Ch.3 acceptance tests (clock never re-sensed · overnight needs a night
  boundary · cold start no false reunion · no autonomous tick · deadline without an anchor rejected ·
  calendar absent never fabricates · fidelity tracks strength not age · Vol VIII owns decay).

## Dependencies + blocked-by
- **Blocked by:** **WO-CANON-XV** — `TimeState`/`CalendarState` are hard upstream and **currently have no
  consumers and a broken desktop domain**; this faculty must degrade honestly rather than re-sense while
  that is true. **WO-CANON-XXI** (IdentityState thread) for Ch.3 §3.5; **WO-078** (autobiography timeline)
  stays PENDING and must be marked so, not faked. Agency's goal store (`/goals/…`, Vol V Ch.10) is PENDING
  → goal-sourced deadlines wait; calendar-sourced works today.
- Cross-volume: Vol IX (dream constants — read, never fire) · Vol VIII (forgetting curve owned there) ·
  Vol V Ch.5/Ch.10 · Vol VII (the frame is a component of The Moment).
- **Gate:** **David L3** on proactive deadline reminders (Ch.2 OQ-1, RESERVED-adjacent — allowed only at
  `imminent`, quiet-hours-respecting, Agency-confirmed). Everything else in this WO is ungated. CA on the
  12 flagged Vol XXV OQs before the volume is promoted.

## Lane
Builder (Python — `faculties/temporal/` completion + spine wiring + the ambient consumer; read-only over
Vol XV / VIII / IX / `continuity/`). Architect coordinates, owns the board correction, and carries the
proactive-reminder decision to David.
