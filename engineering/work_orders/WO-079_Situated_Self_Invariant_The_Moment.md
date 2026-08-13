# WO-079 — The Situated Self Invariant (The Moment binds the cognitive cycle)

**Owner:** Builder (eLo OS — `core/executive.py` / spine) · Architect coordinates. **Priority:** P1 — core
cognitive invariant. **Status:** OPEN — spec'd 2026-08-08 (Chief Architect, from David's Situated Self blueprint).
**Canon home:** sharpens **ADR-Exec-004 (Situated Self)** + **ADR-Exec-006 (Executive Assembly)** — reconciled
onto `SITUATED_SELF_v1_assembly.md`. **NOT a new Volume XXIX, NOT a new module** (Check-Before-Build). The
invariant itself may warrant its own ADR ratification at David L3.
> **Renumbered from the CA's "WO-075" → WO-079:** WO-075 is already Desktop Gravity/Screen-Wrap. This is the
> Situated Self Invariant. (Number collision caught + resolved.)

## The core invariant
> **Before eLo may THINK, ACT, or SPEAK, the Executive Assembly must hydrate `The Moment` (a live state
> object) and read identity/position/capability/status FROM it. eLo is forbidden from hallucinating those
> from LLM training data — they come from system-verified state.**

## A. The Moment — ephemeral live state (`self/state/the_moment.json`), injected EVERY turn
Temporal anchor (epoch + local time) · embodiment (`desktop_sprite | r_and_d_robot | headless_server`) ·
spatial node (from `unity_events.json`, e.g. `Claude_window_bottom_edge`) · affordance array (valid actions
from current boundaries: sit/wall_jump/perch…) · pose · mood/energy/curiosity · last action + result ·
current intention. Compiled fresh each turn, injected into the prompt window.

## A2. Body map (`self/state/body_map.json`) — ME ↔ WORLD ↔ RELATIONSHIP
Deterministic self-metrics feed The Moment: `metrics` (height_px·width_px·scale) · `kinematics`
(pose·velocity·current_surface·orientation·reach·jump-height/distance) · `capabilities` (per-faculty
status + confidence). Plus the RELATIONSHIP layer — for each nearby surface/window: reachable · jumpable ·
climbable · sit-able · safe · interesting · unknown. So behaviour emerges from affordances ("that ledge is
reachable" → intent → capability → plan → execute), NOT `if gap<200: play_walljump`.

## A3. Epistemic tiers — "I know" vs "I think" (the honesty upgrade)
Every self/world claim carries a verification tier, and eLo's language reflects it:
- **Verified** (hardware/OS fact): "I am on Claude." (active-window handle)
- **Inferred** (probabilistic): "I think David is working." (mouse activity over a window)
- **Remembered** (log): "David likes these little walks." (`growth_journal`)
- **Possible** (geometry math): "A 140px gap is within my ~200px range."
- **Unknown**: "I haven't inspected what's behind that window."
- **Unavailable**: "I can't reach my file-writing faculty right now."
→ turns "I can see the movie" into "Chrome's active and YouTube's visible, but I haven't inspected the video
yet." This is self-awareness through epistemic state (ties ADR-Exec-001 — never assert unverified as fact).

## B. Capability introspection (`core/capability_registry.py`) — hard-block, not narrate
"Can you search/write files?" → check the functional registry (`FILE_WRITE.status == DEGRADED`). If a tool
is < ONLINE, the Executive HARD-BLOCKS generation of an action token for it. (Extends WO-055 + the registry.)

## C. Execution / ACK loop — the "sit" fix, universalised (already our architecture — ADR-Exec-001 · WO-041)
intent (external OR internal) → verify against the live affordance array → serialise into the 9-field Faculty
Bus envelope → dispatch to Unity/robot → **GATE: blocked from speaking/state-update until a verified ACK
returns** → on ACK SUCCESS: update `the_moment` pose + emit affirmative speech ("I'm sitting on Claude now.")
→ on TIMEOUT/FAILURE: state-drift alert + honest failure speech ("I tried to sit, but my movement engine
didn't confirm."). This is the sit chain we built — now the universal rule for every action.

## D. Autobiographical engine (`self/journals/growth_journal.jsonl`) — ties WO-059 + Vol V Ch.6 + WO-055
Sliding 50-action window → eLo can discover his own ticks ("I've been idle-waving a lot"). Post-action
significance > 0.75 → triggers a reflection turn → updates persistent capability confidence weights.

## Check-Before-Build rules (CA's — kept verbatim, they're right)
1. **No rogue singleton.** Do NOT build a standalone "Self-Awareness Daemon." Refactor `core/executive.py`
   so compiling The Moment payload is a MANDATORY argument to the router invocation pass.
2. **Schema compliance.** Any self-reflective update maps back to the canonical 9-field envelope (ADR-0001).
3. **Deterministic over generative.** If a value is queryable from the OS/Unity frame (location, window
   focus, file availability), it is RETRIEVED from code, never estimated by the LLM.

## Definition of Done
1. State invariant enforced — a turn FAILS CLEANLY if `the_moment.json` can't be built/verified at the boundary.
2. Deterministic response — "Where are you?" returns a value parsed directly from `the_moment`, not generated.
3. Execution gating live — affirmative action text is blocked until the Unity/hardware ACK clears the bus.
4. Passes the 10-question Situated Self test (`SITUATED_SELF_v1_assembly.md`) on the REAL brain.

## Honest scoping + gate
- **Partly already built:** the ACK-gate (sit chain, ADR-Exec-001, WO-041) and state-derived answers (WO-059).
  NEW work = The Moment hydration + the mandatory-arg refactor of `core/executive.py` + capability hard-block
  + universalising the ACK-gate to every action.
- **The INVARIANT core is Presentable-relevant** (it's the "does what it says / self-aware of state / honest"
  bars). The EMERGENT richness on top — internal-intention engine, curiosity matrix, autonomous exploration —
  is **POST-Presentable** (don't calibrate curiosity params until the invariant + real brain are live).
- **Verbal testing gated on WO-073** (real brain) — the state exists, but eLo can't verbalise from it on the mock.
- Reconciles with: `SITUATED_SELF_v1_assembly.md` (this is its execution spec) · WO-077 (return loop) ·
  WO-076 (no fabricated links).
