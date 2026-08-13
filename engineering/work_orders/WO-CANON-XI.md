# WO-CANON-XI — Motor Cortex: formalise the DOWN command / UP ACK contract + movement-grammar parity

**Owner:** **Designer** (Unity — channel validation, verb realisation, reflex reporting) **+ Builder**
(eLo OS — `blender_bridge/state_writer.py`, `avatar/`, the ACK/timeout path in `server.py`).
**Priority:** P2 — the body layer of `brain > body > brain` had **zero canon contract** until now.
**Status:** OPEN — raised 2026-08-13. Board line 1482: *"▶ RELEASED — volume now written."*
**One item inside carries David L3** (see §D): the generalised verb channel changes a DOWN contract David
personally signed.

**Canon refs:** Volume XI — Ch.1 `01_Motor_Cortex_and_the_Body_Contract.md` (§1.2 channels, §1.3 action
protocol, **§1.4 command envelope DOWN**, §1.5 event envelope UP, **§1.7 the "no local driver decides" law
+ audit rule**, §1.10 acceptance tests), Ch.2 `02_Movement_Grammar_and_Embodiment_Parity.md` (§2.2 **the
twelve verbs**, §2.3 realisation, §2.4 **the PEEK precondition**, §2.5 the two risk constraints, §2.7
tests). **`docs/architecture/UNITY_ELOOS_IO_CONTRACT.md` (David L3, 2026-08-06)** · ADR-Exec-001 (Verified
Speech) · ADR-Exec-003 (Embodied Truth) · WO-035 · WO-040 · WO-041 · WO-054 · WO-063 · WO-086 ·
**Volume XIII Ruling D-XIII-1** (this volume carries the field that makes it safe).

---

## IRV — verified 2026-08-13

**LIVE and working (do not rebuild — extend):**
- **DOWN channel:** `blender/blender_state.json` via `blender_bridge/state_writer.py`.
  `write()` / `write_with_presence()` emit `sit_command` (L126/L214), `move_command` (L133/L221),
  plus `leave_command` / `return_command`.
- **UP channel:** `blender/unity_events.json`, discrete + timestamped.
- **ACK gating of speech is real:** `server.py` gates on `sit_complete` (L2593–2606, comment: *"WO-041:
  verify-before-speak — eLo NEVER claims 'I'm sitting' until Unity writes sit_complete=true"*),
  `move_complete` (L2710), `exit_complete` (L2772–2781), each with a `_ts > since` guard and a
  `_PENDING_*` slot (L106).
- **Channel law is ratified:** `UNITY_ELOOS_IO_CONTRACT.md` — *"Emotions, moods, states, new actions are
  **FIELDS inside an existing channel, never new files**"*; *"Neither seat changes a file's purpose or a
  field's channel without updating THIS doc."*
- **Bridges:** `avatar/unity_bridge.py`, `avatar/animation_router.py`. **Robot path scaffolding:**
  `avatar/motor_abstraction.py`, `avatar/safety_controller.py`, `avatar/robot_simulator.py`.

**PENDING / gaps (verified):**
- **`move_command` carries only `{type, _ts}`** — **no `route`, no `issued_by`** (`state_writer.py:133`,
  `:221`). The Vol XI §1.4 generalised shape does not exist yet.
- **The Movement Grammar is not a real vocabulary.** The twelve verbs live in WO-049 prose and in Ch.2;
  **nothing in the channel validates them.** There is no closed verb set in code.
- **The PEEK precondition is not enforced anywhere** — not at the planner (which does not exist yet), not
  at the channel, not at realisation. A blind jump is currently representable.
- **The §1.7 audit rule is not implemented.** `EloDesktopNav._route` selecting a traversal locally is the
  known open violation; `DesktopBuddy`'s survival re-attach is a **legal** bounded reflex but **must emit
  `resurfaced` UP** (WO-094 §A: must not regress).
- **Channel drift:** `blender/elo_spatial.json` exists and carries continuous sensed state UP (position,
  height, screen size, current window), read by `desktop/spatial_state.py` — but the IO contract names the
  third channel `blender/unity_state.json` *"only if needed."* **An undocumented channel is exactly the
  drift class the contract exists to prevent** (`OQ-1.1`).
- **No `.cs` in this repo** — Unity work is the Designer seat's, relayed via
  `blender/agent_bus/design/START_HERE`.

## Problem / Goal

The down/up motor contract was real and working in code and in `UNITY_ELOOS_IO_CONTRACT.md`, but it had no
home in canon — so five WOs (035/040/041/063/086) each restated a piece of it and nothing bound future work
to it. Volume XI is now that home. Two things must become mechanically true: **the channel must carry and
validate a route grammar** (which is what makes Volume XIII's navigator demotion safe), and **"the body
never decides" must be auditable** rather than aspirational.

Goal: generalise the DOWN/UP envelope additively, make the twelve-verb grammar a closed, channel-validated
vocabulary with the PEEK precondition enforced at three layers, and implement the §1.7 audit rule.

## Scope to DoD

### §A — Generalise the DOWN envelope (additive; this is the field WO-CANON-XIII depends on)
- Extend `move_command` per Ch.1 §1.4 with **`route`** — ordered legs
  `{verb, to:{surface_id, anchor{x,y}}, precondition[], expected_ms}` — and **`issued_by`**.
- **Additive only.** A `move_command` with `type` and no `route` behaves **exactly as today**; a one-leg
  route *is* today's behaviour. This is what makes the Vol XIII migration safe (parity first, removal
  second — `OQ-2.1` there).
- `issued_by` is **mandatory** on any command implying traversal and MUST be `SpatialFaculty`; **the body
  rejects a route from any other issuer.** This is the mechanical enforcement of "one owner of spatial
  reasoning" (Ruling D-XIII-1).
- **No new files.** New concerns are fields in an existing channel. `emotions.json` / `movement.json` are
  forbidden. Read-merge-write discipline: writers merge, nobody clobbers another owner's block.
- The body executes the route **leg by leg** and ACKs each leg. It does **not** re-order, substitute or
  shortcut legs.

### §B — Formalise the UP envelope
- Events per Ch.1 §1.5: `{type, leg, at:{surface_id, pos}, ok, detail, _ts}` on
  `blender/unity_events.json`. **`at` is mandatory on any motion ACK** — the brain re-reads the *real*
  position rather than assuming the commanded one. That is the "brain reads that back" half of the loop.
- **Reflex events are mandatory:** `landed`, `resurfaced`, `collided`. *A local safety action that is never
  reported is indistinguishable from the body deciding, and is forbidden.*
- Perceptions travel this same channel (`window_opened`, `user_idle`) — **reports, never decisions**.
- Events are **consumed**; nothing may re-read a consumed event and act again. Keep the existing `_ts >
  since` guard: a stale event may never false-trigger.
- **Timeouts:** honest failure — *"I tried to X but couldn't"*; never claim success, never go quiet as if
  it worked. Timeout derived from the route's `expected_ms` sum plus slack, not a fixed constant
  (`OQ-1.3` recommendation — a three-leg route legitimately takes longer than a sit).
- **Leg ACKs:** per-leg (`move_complete{leg:2}`) for verification and learning granularity, **plus** a
  terminal `arrived` the Executive gates speech on (`OQ-1.4` recommendation; pairs with Vol XIII `OQ-2.3`).

### §C — The twelve-verb Movement Grammar, closed and validated
- The vocabulary: **APPROACH · CLIMB · BALANCE · LEAP · HANG · SLIDE · PEEK · PERCH · REST · OBSERVE ·
  RETREAT · RETURN**. Every route leg carries exactly one verb. **The set accepted by the channel is
  exactly these twelve; adding one requires a canon change.**
- **Verbs are parameterised, not multiplied:** `APPROACH` at speed 0.3 vs 1.0 is the same verb — there is
  no separate WALK/RUN. This is why *"walk → jog → run → leap → recover"* reads as one body rather than
  clip swapping.
- **Composite named moves are compositions** (fire-jump, shoot-to-exit, wall-jump chimney) —
  `APPROACH + LEAP` with a body-specific realisation, never a thirteenth verb.
- **A body declares which verbs it supports.** The planner never emits an unsupported verb; it routes
  around it. A robot with no `LEAP` simply never receives one.
- **Routes are verbs, never assets.** No animation or clip name may appear anywhere in the command payload.
  **The realisation layer chooses the asset; the brain never does.** Realisation ≠ decision: picking *how*
  to render a commanded `LEAP` is legal; deciding *whether* to leap is a §1.7 violation.

### §D — The PEEK precondition, enforced at three layers ⚠ contains the David L3 item
- David's build rule 1, promoted from flavour to contract: *"Peek before EVERY jump — hard precondition…
  No blind jumps."*
- **Layer 1 planner** (Vol XIII) emits `PEEK` as a precondition on every `LEAP` leg.
  **Layer 2 channel** (this volume) rejects a route containing a `LEAP` without a preceding `PEEK`, emits a
  rejection event UP, and **executes nothing**. **Layer 3 realisation** asserts the peek occurred — failing
  loudly, never silently. *Deliberately redundant: a rule that lives only in the planner is lost the first
  time anything else issues a route.*
- **⚠ `OQ-1.2` — DAVID L3.** Adding `route` + `issued_by` to `move_command` is additive and backwards
  compatible, but it **changes the DOWN contract David personally signed** (`UNITY_ELOOS_IO_CONTRACT.md`,
  2026-08-06). Confirm the change **and** the sequencing: **ship the field, prove parity, then** remove
  Unity's local route selection — never both at once.

### §E — The "no local driver decides" law, made auditable (Ch.1 §1.7)
- Implement the audit as a **standing check, not a one-off**:
  ```
  For every observable behaviour B the body performs:
    1. Is there a <action>_command DOWN with issued_by set, whose _ts precedes B?  → LEGAL (commanded)
    2. Else, is B in the bounded-reflex list AND did it emit an event UP?          → LEGAL (reflex)
    3. Else                                                                        → VIOLATION
  ```
- Known state to encode: `EloIdleBehaviour` mouse-idle — **CLOSED** (WO-086, routed UP) ·
  **`EloDesktopNav._route` — OPEN, the largest violation** (Ruling D-XIII-1 demotes it; **WO-CANON-XIII
  owns that retirement, not this WO**) · `DesktopBuddy` survival re-attach — **LEGAL, keep**, but it MUST
  emit `resurfaced` UP.
- **Commanded state owns the body** (WO-035/WO-040 `_sitHeld`): while a command is in flight, autonomous
  behaviour may not overwrite it. One authority at a time.
- **Autonomous and commanded are one capability**: whatever eLo does on his own must be drivable by the
  Executive through the *same* underlying capability. Two code paths would let "eLo exploring" and "eLo told
  to explore" drift apart.

### §F — Embodiment parity and the two risk constraints (Ch.2 §2.5)
- **No driver port.** The game `PlayerController` must not move to the desktop, nor vice-versa. *"Porting it
  = the forbidden animation hack that fakes awareness."*
- **No identical asset/rig coupling as the sharing mechanism.** Sharing baked clips and identical rig
  binding is a big risk with silent failure — the seats already hit a missing `c_arm_fk` and a head-bone
  mis-reference. **Per-gesture code ports bind bones by name and MUST FAIL LOUDLY** if a bone is absent —
  never a silent no-op.
- **The feel is shared; the assets are not.** Desktop and game should read as the same creature; they must
  not share clips or rig binding.
- **Body-local axes:** eLo faces the camera ~180° from world; peek pitch, wall-jump direction and head aim
  are all expressed in his body frame.
- **No eyes.** Expression is orientation, posture, glow and the single curved mouth. This volume carries no
  eye channel and none may be added. HeadAim is a **realisation of `OBSERVE`/`PEEK` weighting**, not a
  decider.
- **Channel hygiene (`OQ-1.1`):** recognise `blender/elo_spatial.json` **as** the IO contract's third
  (UP sensed-state) channel rather than adding `unity_state.json` beside it. **Needs both seats' sign-off**
  — both signed the contract.

## Files to TOUCH
- `blender_bridge/state_writer.py` (L133, L221 — additive `route` + `issued_by`; validation before write)
- `server.py` (ACK path: per-leg + terminal `arrived`; derived timeouts; honest failure wording)
- `avatar/unity_bridge.py` · `avatar/animation_router.py` (verb → realisation mapping; closed verb set)
- `avatar/motor_abstraction.py` (robot realisation of the same verbs; supported-verb declaration)
- `docs/architecture/UNITY_ELOOS_IO_CONTRACT.md` — **Architect lane**: record the additive fields and the
  `elo_spatial.json` channel, **after David L3** (§D)
- `tests/test_canon_xi_motor.py` — **NEW**
- Unity: `EloDesktopNav` leg execution + reflex reporting, `DesktopBuddy` `resurfaced` emission —
  **Designer seat**, via `blender/agent_bus/design/START_HERE`

## Files MUST-NOT-TOUCH
- The **survival re-attach** safety net and landing physics (WO-094 §A: must not regress)
- `runtime/executive.py` (FROZEN) · `world/live_world_state.py` (WO-CANON-XV) · `faculties/spatial/`
  (WO-CANON-XIII decides; this volume only delivers and confirms)
- Any **new** channel file — `emotions.json` / `movement.json` / a second sensed-state file are forbidden
- Unity's route **selection** — its retirement is WO-CANON-XIII §E, gated on David L3, not this WO

## Definition of Done
- `move_command` carries `route` + `issued_by`; a legacy `type`-only command is byte-identically unchanged.
- The channel validates: unknown verb ⇒ rejected · `LEAP` without a preceding `PEEK` ⇒ rejected with an UP
  rejection event and **no partial execution** · `issued_by != SpatialFaculty` ⇒ rejected.
- Every motion ACK carries `at`; per-leg ACKs plus a terminal `arrived`; timeouts derived from
  `expected_ms`; failure is spoken honestly and never as success or silence.
- Every bounded reflex emits an event UP, including `resurfaced` from the survival path.
- The §1.7 audit rule runs as a standing check and reports uncommanded, unreported behaviour as a
  VIOLATION — **including flagging `EloDesktopNav`'s local selection until WO-CANON-XIII §E lands.**
- The twelve verbs are a closed set in code; no clip or animation name appears in any command payload; a
  missing bone fails loudly.
- **This WO does not confer DONE and does not promote Volume XI to RATIFIED** — the volume's own DoD needs
  the CA cross-check (Ch.1 ×4, Ch.2 ×3) and David L3 on the generalised verb channel.

## Tests (`tests/test_canon_xi_motor.py` — NEW; from Ch.1 §1.10 / Ch.2 §2.7)
**Ch.1 Functional** — **FT-1** command DOWN → no claim → `sit_complete` with `_ts > since` → self-model
updates → only then may he say it · **FT-2** a stale ACK (`_ts <= since`) does not clear pending and claims
nothing · **FT-3** timeout ⇒ honest failure, pending cleared, no success recorded anywhere · **FT-4** a
duplicate command while one is in flight does not re-emit `_ts` (WO-054) · **FT-5** commanded state owns the
body (a held sit is not overwritten by ambient) · **FT-6** a route with a `LEAP` and no preceding `PEEK`, or
`issued_by != SpatialFaculty`, is **REJECTED** with an UP rejection event and **no partial execution**.

**Ch.1 Stability** — **ST-1 no new files** (a new concern appears as a field; assert no new channel file
exists) · **ST-2** body offline degrades honestly (eLo converses, claims no action, writes nothing as if
delivered) · **ST-3** dormant/dragged body: wake → un-steer → re-attach → execute (WO-063), ACK still gates
belief · **ST-4** every bounded reflex is reported with the body's **actual** position and the brain
re-plans from it · **ST-5 (the additive guarantee)** a `move_command` with `type` and no `route` behaves
identically to the current live system.

**Ch.1 Integration** — **IT-1** the closed loop: decide → DOWN → execute → ACK UP → belief → speech
permitted; **assert removing the ACK removes both the belief and the speech — there is no path from intent
to assertion that skips the body** · **IT-2** the §1.7 audit rule finds violations: every behaviour is
commanded or a reported reflex, **and `EloDesktopNav`'s locally-selected traversal is reported as a
VIOLATION until D-XIII-1 lands** · **IT-3** autonomous and commanded are one capability — no second code
path.

**Ch.2** — **FT-1** every leg names one of the twelve verbs and no clip name appears in the payload ·
**FT-2** the PEEK precondition is refused independently at planner, channel and realisation · **FT-3**
composites decompose into existing verbs; no thirteenth verb exists · **FT-4** slow vs fast `APPROACH` is
one verb with parameters, and the transition is continuous · **FT-5** a body declaring no `LEAP` never
receives one · **FT-6** `OBSERVE`/`PEEK` realise as head/chest orientation + posture + glow in body-local
axes, **no eye target** · **ST-1** a missing bone raises loudly, never a silent no-op · **ST-2** no driver
port between game and desktop · **ST-3** body-local axes hold under the ~180° camera-facing rotation ·
**ST-4** the accepted verb set is exactly twelve · **IT-1** same creature across bodies with no shared baked
clip or rig binding · **IT-2** the grammar survives the round trip (verb DOWN → realise → `<verb>_complete`
UP with the actual position → per-verb-and-affordance learning, so Vol XXVIII trains on it unchanged) ·
**IT-3 no regressions** — perch · roam · drag · click-through · gun-runoff all still work.

## Dependencies + blocked-by
- **Blocked by:** **David L3 on `OQ-1.2`** — the generalised verb channel changes the DOWN contract he
  signed (2026-08-06). §A/§D do not ship without it. The UP-envelope work (§B), the audit rule (§E) and the
  parity constraints (§F) are not blocked.
- **Both-seat sign-off** on `OQ-1.1` (recognise `elo_spatial.json` as the third channel) — Builder and
  Designer both signed the IO contract.
- **CA** on `OQ-1.3` (derived timeouts) and `OQ-1.4` (per-leg vs terminal ACK — recommend both), and on
  Ch.2 `OQ-2.1` (are twelve the right verbs — the union of WO-049's list and David's roam source, treated as
  closed), `OQ-2.2` (where the verb-support declaration lives — recommend the embodiment binding),
  `OQ-2.3` (`EXIT_SCREEN` as a composition, not a thirteenth verb).
- **Paired with WO-CANON-XIII:** this WO ships the `route`/`issued_by` field; **XIII uses it and owns the
  navigator's retirement.** Ship the field **once**, here. XIII §A depends on this.
- **Coordinates with:** WO-CANON-VII (the brain-side UP-relay enforcement and the same audit rule) ·
  WO-086 (the emit-then-retire precedent; its Designer half is gated on David) · WO-094 §A (`resurfaced`
  must not regress) · Vol XXVIII (per-verb outcome capture).
- **Architect lane, relayed:** `CANON_BUILD_PROGRAM.md` line 44 must drop XI from *"already live — verify
  only"*; `00_CANON_INDEX.md` must stop calling XI *"✅ Live — `avatar/` (code)"* — it is canon + partial
  implementation.
- **Gate:** David L3 (§A/§D — the signed DOWN contract) + CA cross-check of the seven OQs.

## Lane
Designer (Unity — channel validation, verb realisation, reflex reporting; via
`blender/agent_bus/design/START_HERE`). Builder (Python — `state_writer` envelope, ACK/timeout path,
`avatar/` realisation mapping, the audit-rule check, tests). Architect coordinates, carries `OQ-1.2` to
David, and owns the `UNITY_ELOOS_IO_CONTRACT.md` / Canon Index updates after the ruling.
