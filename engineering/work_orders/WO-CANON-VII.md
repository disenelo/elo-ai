# WO-CANON-VII — Executive Cortex: close Ruling C, gate speech on tiers, build the dual-intent queue, enforce the UP-relay

**Owner:** Builder (eLo OS — `server.py` call site, `runtime/spine/`, `runtime/cognitive_snapshot.py`,
`runtime/the_moment.py`, `self/decision_journal.py`). **Priority:** **P1** — Volume VII is the volume three
other volumes defer to; the audit calls it *"THE hole."* **Status:** OPEN — raised 2026-08-13; the volume is
written (5 chapters, READY FOR REVIEW). Board line 1480 reads *"▶ RELEASED — volume now written."*

**Canon refs:** Volume VII — Ch.1 `01_The_Executive_and_One_Plan_Per_Turn.md`, Ch.2
`02_Executive_Assembly_and_The_Moment.md` (§2.3 **the ordering gap**), Ch.3
`03_Epistemic_Tiers_and_Verified_Speech.md` (§3.2 tiers, **§3.4 the Speech Gate**), Ch.4
`04_Intent_Queue_and_Why_Did_I_Do_That.md` (§4.2 **the dual-intent queue**, §4.3 arbitration, §4.4 journal),
Ch.5 `05_Brain_Body_Brain_The_Closed_Loop.md` (§5.5 ACK before belief, §5.7 the `EmbodimentLoop` contract).
**`CANON_RULINGS_2026-08-10.md` Ruling C** · ADR-Exec-001 (Verified Executive Authority) · ADR-Exec-003
(Embodied Truth) · ADR-Exec-004 (Situated Self) · ADR-Exec-006 (Executive Assembly) · `FREEZE_V1_LOCK.md`.

---

## IRV — verified 2026-08-13 by reading the code

| Anchor | Verified finding |
|---|---|
| **🔴 Ruling C is NOT closed** | `server.py:55` — `from runtime.executive import decide as exec_decide`. `server.py:2322` — `exec_decision = exec_decide(attention_model, loop_detected=False, user_input=raw)`. `server.py:2906` — `_plan = _spine_run(raw, state=_state, attention=_attention_with_exec, …)`. **The decision is taken ~584 lines before the spine assembles anything.** Inside `spine.py` the order is now correct (`build_snapshot` → `assemble_cognitive_state` → `_executive_faculty`), but `_executive_faculty()` does not decide — it reads a decision handed to it via `attention["_exec_decision"]`. **Net: eLo still decides before he assembles.** *(Vol VII Ch.2 §2.3 cites `server.py:2888` for the spine call; it is at **2906** today — the citation has drifted by the edits since.)* |
| Post-decision overrides | `server.py:~2335` mutates `exec_decision` after `decide()` returns (`sm.is_stabilisation_forced` → `exec_decision.update({...})`). Ch.1 §1.6 names three such sites (stabilisation, WO-020 Seam-A routing, WO-029 greeting); they are honestly *recorded* but are structurally edits to the one decision, made outside the Executive module. |
| Epistemic tiers | `runtime/the_moment.py:24–34` ships **five** markers: `verified · inferred · last-known · live · unknown`. David's verbatim names **six**: Verified · Inferred · **Remembered** · **Possible** · Unknown · **Unavailable**. Two vocabularies, neither a subset of the other (`OQ-VII-1`). |
| **🟠 Tiers annotate, they do not gate** | The `[SITUATED SELF]` block instructs the model (*"Never invent; if a field is unknown say so"*) and ships per-field markers. **Nothing verifies the output against a licence.** Ch.3 §3.4's `LICENCE` and `VERIFY OUTPUT` steps do not exist. A model that ignores the instruction produces an unverified claim and nothing catches it. |
| **🔴 The dual-intent queue does not exist** | `runtime/cognitive_snapshot.py:73` declares `pending_intentions: tuple`, and **line 163 is the only writer**: `pending_intentions.append(("sit", "cursor"))`. `BodySchema.queued_intent` (L34) parks one movement intent behind a pending sit. There is **no lane distinction, no `pressure`, no `feasible`, no `boundary_ok`, no internal lane, and no arbitration.** The name exists; the mechanism does not. |
| Journal | `self/decision_journal.py` is real: `alternatives_rejected` (L101), `explain_last()` (L160). *"Why did I do that?"* works for actions. It has nothing to say about **wants** (no losing intents are recorded, because there is no queue). |
| **🟠 UP-relay unenforced** | `blender/unity_events.json` is read in `server.py`, `ambient/ambient_engine.py` and `faculties/window_event_faculty.py`, but **no test, no bus rule and no review gate asserts that a body perception must relay UP**. Canon now says it must (Ch.5 §5.7 L1); nothing checks it. |

## Problem / Goal

Volume VII is the cognition volume for the decider, and three volumes (VI §4.6, XVI §1.5/§4.4,
`Volume_V/CONTRACTS.md` §1, all three of Vol XX) defer their contracts to it. It is now written. Four of
its laws are **stated in canon and unenforced in code**, and the first of them inverts the volume's core
claim: *the self is assembled, not generated* — but today the decision precedes the assembly, which makes
the assembled self a post-hoc description of a choice already made.

Goal: close Ruling C, turn the epistemic tiers from prompt annotation into a runtime gate, build the
dual-intent queue the Executive is supposed to arbitrate, and make the brain>body>brain UP-relay an
enforced invariant rather than a sentence in a WO.

## Scope to DoD

### A. HEADLINE — close Ruling C (Ch.2 §2.3)

- **Move the `decide()` call site** so it runs *after* `build_snapshot()` within the turn, and pass the
  frozen `UnifiedCognitiveState` in as the decision's input. Order becomes:
  `ASSEMBLE → FREEZE → DECIDE → PROJECT`.
- **`runtime/executive.py` is FROZEN** (`FREEZE_V1_LOCK.md`) — this is a change to **where and with what
  `decide()` is called**, not to its logic. That distinction is what keeps the change small and the freeze
  intact. Do not edit `runtime/executive.py`.
- **One name:** `UnifiedCognitiveState` is canonical; `CognitiveSnapshot` is the retired alias. The alias
  already exists in `runtime/cognitive_snapshot.py` — keep it as an alias, do not resurrect it as the name.
- **The three post-decision override sites** (`server.py` ~L2335 / ~L2360 / ~L2383): per Ch.1 §1.6, declare
  them **Executive policy** and fold them *inside* the one decision, or retire them. They must not survive
  as silent mutations of a decision made elsewhere. **Which of the two (fold vs retire) is `OQ-VII-2` and
  needs David + CA** — until it is ruled, keep them but make each one **journalled with its override
  reason**, so no mutation is silent.
- **Do not "fix" the ordering by assembling twice.** One assembly per turn is the law (Vol XVI Ch.2, Vol XV).
  Coordinate with WO-CANON-XV.
- **Sequencing is `OQ-VII-3`:** moving a call site around a frozen module — confirm with David whether this
  lands before or after Presentable v1 before starting.

### B. Epistemic tiers must GATE, not annotate (Ch.3 §3.4)

- Build the two missing stages: **LICENCE** — the Executive emits, alongside the one plan, the set of
  claims permitted this turn, each with its maximum tier; and **VERIFY OUTPUT** — anything asserted outside
  the licence is a **violation, not a style issue**, and is caught before it reaches David.
- Enforce the gate rules: a claim inherits **the tier of its weakest source** · unqualified present-tense
  assertions about self/body/world require `VERIFIED` · a hedge is **semantic, not decorative** ·
  `UNAVAILABLE` is spoken in system terms, never as a leaked implementation detail · **absence is never
  filled** by a neutral default spoken as fact · **no action claim without an ACK** (before ACK the tier is
  `POSSIBLE` at best) · private state is sayable *as private state* at `VERIFIED` · **the tier travels with
  the claim into memory** (an `INFERRED` claim may become a remembered inference; it never becomes a
  verified memory — this is what stops eLo learning his own guesses, ADR-Exec-005).
- **Vocabulary (`OQ-VII-1`) blocks this sub-scope.** Five shipped markers vs David's six. The Architect's
  recommendation is David's six as canon, `live` folded into `verified`, `last-known` = `remembered`.
  **Do not pick one and build** — this is David's call and it changes what eLo is allowed to say.

### C. The dual-intent queue (Ch.4 §4.2/§4.3)

- Build `IntentQueue` as an Executive-owned component of `UnifiedCognitiveState`:
  `{external: [Intent], internal: [Intent], committed: Intent | null}`, with `Intent =
  {id, lane, kind, content, origin, pressure, requires[], feasible+reason, boundary_ok+reason, status,
  created_ts, last_seen_ts, expires}`.
- Replace the one hard-coded `("sit","cursor")` tuple with real entries on both lanes. Preserve today's sit
  behaviour exactly through the migration (parity assert).
- Queue rules: **faculties propose, the Executive admits** (a faculty may never self-commit) · **one
  committed intent at a time** · feasibility (capability) and boundary (D-PRESENCE) checks precede
  commitment, never follow it (ADR-Exec-003, Affordance Before Action) · an expired intent is `abandoned`
  **with a reason, and the abandonment is journalled** — so *"why didn't you go and look?"* is answerable.
- **The absence rule** (David #9): after N minutes with no interaction, set `absence_awareness` —
  `Attention.David` drops, curiosity rises, internal intents gain pressure and become eligible to commit.
  On return, *"I explored the other side of the desktop while you were away"* is only sayable because the
  exploration was **journalled** — it is a Ch.3 remembered/verified claim, never a story.
- **Arbitration order is FLAGGED INVENTION (`OQ-VII-4`)** — nothing in canon or David's verbatim fixes it;
  he says only *"governance decides priority."* The proposed order (safety/boundary > external explicit >
  standing commitment > external implicit > internal high-pressure > internal curiosity) **requires
  ratification before it is built.** It touches D-PRESENCE, so it is arguably **David L3**. Build the queue
  and the recording of losing intents first; leave the ranking behind the ruling.
- Arbitration happens **inside** the one decision. The **losing** intents are recorded with why — that is
  what makes `alternatives_rejected` truthful for *wants*, not only for actions.
- **Boundary:** Vol XVI §4.2 arbitrates *faculties contradicting each other about the situation*; this
  arbitrates *intentions competing for one body and one voice*. Different inputs, same single decider.
  Do not merge them; do not add a second decider.

### D. Enforce brain > body > brain (Ch.5 §5.7)

- Make the `EmbodimentLoop` MUSTs mechanically checkable: **L1** every body perception relays UP on the
  canonical event channel as a typed report · **L2** commands execute from DOWN only · **L3** every
  commanded action ACKs (success, failure, or timeout — **silence is not an outcome**) · **L4** the body
  yields instantly and completely to a commanded state.
- **The self-model updates from the ACK, not from the command.** A commanded state is `pending` until
  confirmed — which is what makes `pose_tier: "verified" if pose_acked else "last-known"` correct rather
  than decorative.
- **An ACK is a report and goes UP through the normal channel** — there is no ACK back-door that skips
  assembly; a confirmation lands in the next `UnifiedCognitiveState` like everything else.
- Add the standing audit rule (shared with Vol XI Ch.1 §1.7): for every observable behaviour — commanded
  (a DOWN command with `issued_by`, `_ts` preceding it) **or** a reported bounded reflex, **else
  VIOLATION**. This WO owns the *brain-side* enforcement; **WO-CANON-XI** owns the channel side and
  **WO-CANON-XIII** owns the navigator's demotion.
- **WO-086 remains OPEN and gated on David's greenlight** (it touches the sensitive DesktopBuddy avatar
  file and changes autonomous behaviour). Its sequencing is hard and already confirmed: *Designer
  emit+retire lands **with** the Builder brain-decide half, never before* (retire-first = idle-does-nothing
  regression). Do not front-run it.

### E. Explicitly NOT in this WO (named so they are not silently lost)

Thinking modes · interruption policy · goal management · scheduling/resource allocation. All four are in
the Bible's Volume VII scope line and **have no canon** (Ch.1 §1.7 records them as the Ch.6–Ch.8 backlog).
`OQ-VII-7` asks whether they belong in Vol VII chapters 6–8 or elsewhere. **Do not invent David's calls on
them inside this build.**

## Files to TOUCH
- `server.py` (the `decide()` call site ~L2322 and the spine call ~L2906; the three override sites)
- `runtime/spine/spine.py` (decide-after-assemble; licence emission; intent queue on the plan)
- `runtime/cognitive_snapshot.py` (`IntentQueue` as a component; retire the hard-coded `("sit","cursor")`)
- `runtime/the_moment.py` (tier vocabulary — **only after `OQ-VII-1` is ruled**)
- a new speech-gate module for LICENCE / VERIFY OUTPUT (Builder's placement call; not inside the frozen
  Executive)
- `self/decision_journal.py` (journal losing intents, abandonment reasons, override reasons)
- `tests/test_canon_vii_executive.py` — **NEW**

## Files MUST-NOT-TOUCH
- **`runtime/executive.py` — FROZEN** (`FREEZE_V1_LOCK.md`). Move the call site; do not touch the logic.
- `Unity/DesktopBuddy` avatar files (WO-086's, gated on David)
- `world/live_world_state.py` (WO-CANON-XV) · `faculties/spatial/` (WO-CANON-XIII) ·
  `blender/blender_state.json` channel shape (WO-CANON-XI)
- Vol XVI's bus/envelope internals (`core/faculty_bus.py` — WO-CANON-XVI's lane)

## Definition of Done
- **Ruling C closed:** `decide()` is called with the frozen `UnifiedCognitiveState` as its input, after
  assembly, once per turn — provable from the call graph, not from a comment. Exactly one assembly per turn.
- No post-decision mutation of the plan is silent; each is either folded in or journalled with a reason.
- The Speech Gate exists: a claim outside the licence is **caught**, not merely discouraged; no action
  claim survives without an ACK.
- `IntentQueue` carries both lanes with feasibility + boundary results; one committed intent at a time;
  losing and abandoned intents are journalled with reasons.
- The `EmbodimentLoop` MUSTs are asserted by tests; the audit rule flags an uncommanded, unreported
  behaviour as a VIOLATION.
- `UnifiedCognitiveState` is the one name; `CognitiveSnapshot` survives only as an alias.
- **This WO does not confer DONE and does not promote Volume VII to RATIFIED.** The volume's own DoD still
  requires CA/David answers to `OQ-VII-1…7`.

## Tests (`tests/test_canon_vii_executive.py` — NEW)
- **RC-1 (the headline)** Assert the ordering at process level: for one turn, `build_snapshot()`'s
  timestamp precedes the `decide()` invocation, and `decide()` receives the frozen state as an argument.
  *(Fails on today's code — that is the point.)*
- **RC-2** Exactly one assembly per turn; no second `UnifiedCognitiveState` is built to satisfy RC-1.
- **RC-3** The plan is not mutated after the decision without a journalled reason.
- **RC-4** `runtime/executive.py` is byte-unchanged by this WO (freeze respected).
- **ET-1** A claim whose weakest source is `UNKNOWN` cannot be asserted at `VERIFIED` — the gate rejects it.
- **ET-2** No action claim without an ACK: pre-ACK phrasing is `POSSIBLE`-tier; post-ACK is `VERIFIED`; on
  timeout an honest failure is emitted (never silence, never success).
- **ET-3** Absence is never filled: a missing value is said as unknown, not replaced by a spoken default.
- **ET-4** A tier travels into memory: an `INFERRED` claim never persists as a verified memory.
- **IQ-1** Both lanes populate with real intents; `pending_intentions` is no longer a hard-coded
  `("sit","cursor")`; today's sit behaviour is unchanged (parity).
- **IQ-2** A faculty cannot self-commit an intent (proposed → the Executive admits).
- **IQ-3** Only one intent is `committed` at a time.
- **IQ-4** An infeasible or boundary-failing intent cannot be committed, whatever its pressure.
- **IQ-5** Losing and abandoned intents appear in the journal with a reason — *"why didn't you go and
  look?"* is answerable from record.
- **IQ-6** Absence: after the idle threshold, `absence_awareness` is set and internal pressure rises; the
  return report is grounded in a journalled event, never generated.
- **BB-1** Audit rule: every observed behaviour is either commanded (DOWN command with `issued_by` and an
  earlier `_ts`) or a reported bounded reflex — anything else is reported as a VIOLATION.
- **BB-2** The self-model updates from the ACK, not from the command; a commanded-but-unACKed state reads
  `pending` / `last-known`, never `verified`.
- **BB-3** An ACK arrives through the normal UP channel and lands in the next assembled state — no
  back-door path exists.

## Dependencies + blocked-by
- **Blocked by (partial, per sub-scope, not the whole WO):**
  - **§B** blocked on **`OQ-VII-1`** — the tier vocabulary (five shipped vs David's six). **David's call.**
  - **§C arbitration ranking** blocked on **`OQ-VII-4`** — the order is flagged INVENTION; touches
    D-PRESENCE ⇒ arguably **David L3**. The queue itself is not blocked.
  - **§A sequencing** blocked on **`OQ-VII-3`** — before or after Presentable v1 (call-site change around a
    frozen module). **David confirms.**
  - **§D** partially blocked on **WO-086's** David greenlight for the emit+retire half; the audit rule and
    the tests are not blocked.
- **Coordinates with:** WO-CANON-XVI (assembly mechanism + bus — VII states the ordering *law*, XVI states
  the *mechanism*; neither restates the other) · WO-CANON-XV (the `world` component; do not assemble twice)
  · WO-CANON-XI (the DOWN/UP channel and the same audit rule) · WO-CANON-XIII (the navigator is the largest
  UP-relay violation) · Vol VI (working memory + attention, Ruling B).
- **Architect lane, relayed:** `OQ-VII-6` — Volume XVI Ch.2 §2.3 now reads **false** against the code
  (*"assemble_cognitive_state runs after the decision in spine.py"* — inside `spine.py` it no longer does;
  the gap moved up to `server.py`). Correct XVI §2.3. Also correct Vol VII Ch.2 §2.3's `server.py:2888`
  citation to **2906**.
- **Gate:** David on `OQ-VII-1` / `OQ-VII-3`; David L3 (or CA + David) on `OQ-VII-4`; CA on `OQ-VII-2`,
  `OQ-VII-5`, `OQ-VII-7`.

## Lane
Builder (Python — call-site move, speech gate, intent queue, journal extension, enforcement tests).
Architect coordinates, carries `OQ-VII-1…7` to David/CA, and owns the Vol XVI §2.3 + Vol VII §2.3
corrections. Designer only via WO-086, on David's greenlight.
