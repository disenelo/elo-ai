# Capability ↔ Embodiment Contract — how eLo knows, chooses, and reports his capabilities
### (was "Moveset ↔ Self-Model Spec"; renamed per Chief Architect — it is a CAPABILITY system, not a movement system. Movement is the first proof; the same contract carries waving · sitting · idle · expression · voice · robot gestures · AR · exhibition. The body is the current expression of the One Brain.) **STATUS: ✅ Architect-approved (CA 2026-08-06), sharpenings applied below.**
**For SEAT-ENG-001 (Builder / eLo OS) + SEAT-ENG-004 (Designer / UI-Unity). Lead Architect draft, 2026-08-06 — for Chief Architect cross-check → David L3.**

> David: *"make the free-form moves commandable so I can test them like sit/move — and spec how the self-model works."*
> Designer (current state): free-form moves (fire-jump · wall-jump · step-back→run→fire) fire AUTONOMOUSLY by chance in roam, so they can't be isolated/tested; only directional moves (left/right/up/down/shift) route through eLo OS. Fix = make each a commandable `move_command` sub-type.

This spec is the connective tissue between three things already ratified — the **Free-Form Moveset Contract**, the **IO Contract**, and the **Self Model (WO-052A/059)** — reconciled, not new. It answers David's two asks: (1) make every move commandable + testable, and (2) define how the Self Model drives them.

## 1. The layered flow (one loop, every move)
```
SELF MODEL (what can I do + can I do it now)      ┐
AFFORDANCES (what does this terrain invite — WO-056)├─► EXECUTIVE selects a move (free-form)
GOAL / intent (where am I trying to get)          ┘         │
                                                            ▼
                                    move_command {type, target} DOWN  (IO Contract)
                                                            ▼
                                    Designer executes the Unity state (reference-not-clone)
                                                            ▼
                                    move_complete {move:<sub-type>} UP  (ACK)
                                                            ▼
        EXECUTIVE verifies → UPDATES Self Model (pose · surface · recent_behavior · confidence) → speaks truthfully
```
Nothing is narrated before the ACK (Embodied Truth). A move eLo can't confirm, he doesn't claim.

## 2. How the Self Model works (David's core ask)
The Self Model is not a flat list — each move is a **capability record** the Executive reads before it acts:
```
available_actions: [
  { verb: "fire_jump",  unity_state: "Gun-Jump-Fire", gun: "shown-muted",
    faculty: "movement", status: "online|degraded|offline",   # from faculty health / capability introspection (WO-044)
    confidence: 0.0-1.0,        # grows with verified success (ADR-Exec-005 learning)
    last_success: ts, last_failure: ts },
  { verb: "wall_jump",  unity_state: "Parkour+_wrWallJump", ... },
  { verb: "step_back_run_fire", unity_state: "backingUp→run→Gun-Jump-Fire", ... },
  { verb: "drop" | "peek_leap" | "jump_left/right/top/bottom" | "shift" | "sit", ... }
]
```
- **eLo KNOWS his moveset:** "Can you fire-jump?" → answered from this record ("Yes — movement faculty is online" / "I can, but I haven't landed one cleanly yet" / "not right now, movement is degraded"). That is Situated Self (ADR-Exec-004) + Capability Introspection.
- **The Executive DECIDES from the assembled state (The Moment / ADR-Exec-006):** it reads `available_actions` (can I?) + faculty health (can I *now*?) + affordances (what does *here* invite?) + goal → picks the move (or free-form chain). Not a script, not a random clip.
- **After the ACK it UPDATES the Self Model:** `pose`, `surface`, `recent_behavior{move:count}`, and `confidence` (success ↑, failure ↓). Over time confidence + recent_behavior make the choice *learned* and the self-report honest ("I've landed 9 of my last 10 wall-jumps").

## 3. Commandable sub-types (so David can test each in isolation, like sit)
Extends the existing move channel — FIELDS, no new files (IO Contract §rule):
- DOWN `blender_state.json`: `move_command {"type": "fire_jump"|"wall_jump"|"step_back_run_fire"|"drop"|"peek_leap"|"jump_left"|"jump_right"|"jump_top"|"jump_bottom"|"shift"|"sit", "target"?, "_ts"}`
- UP `unity_events.json`: `move_complete {"move": "<sub-type>", "_ts"}`
Each becomes commandable → eLo OS can invoke it → David can command + verify one move at a time (the sit/move arbiter, per sub-type).

## 4. Now / Later (autonomous AND commanded coexist)
- **NOW (Designer + Builder):** make each free-form move a commandable sub-type (Designer emits the tagged ACK; Builder registers it as a capability in the self-model + can invoke it by command). Autonomous-by-chance in roam CONTINUES (the "living" feel). Result: David can test each move deliberately, and eLo knows them.
- **LATER (Track B, post-Presentable):** the Executive *decides* the free-form chaining from the assembled Self Model + affordances + goal (autonomous-by-*cognition*, not chance) — Spatial Faculty + Agency. Then RL (Vol XXVIII, Movement domain) *learns* which chain to pick, rewarded by the Significance-vector.

## 5. Split (who builds what)
- **DESIGNER (UI):** each move commandable via its sub-type; emit `move_complete` tagged with the sub-type; keep reference-not-clone (reuse existing Unity states, no PlayerController port). Autonomous roam still picks by affordance/chance.
- **BUILDER (eLo OS):** register each move as a capability record in the Self Model (verb · faculty · status · confidence); the Executive reads the assembled state → selects → emits `move_command` → gates speech on `move_complete` → updates the Self Model. Capability *registration* rides with WO-052A now; the Executive *deciding the chain* is Track B.

## 6. Reconciles with (extend, don't duplicate)
Free-Form Moveset Contract (ratified) · IO Contract · Self Model WO-052A/059 · Capability Registry (`runtime/capabilities/registry.py`) + Capability Introspection (WO-044) · Affordances WO-056 · Movement Faculty WO-060 · The Moment / Executive Assembly (ADR-Exec-006) · Learning (ADR-Exec-005) · Spatial Faculty (Track B, WO-049).

## 7. Expressiveness layer — micro-expressions + squash-and-stretch (David 2026-08-06) → WO-062
David: *"this relates to a lot of things."* It's the ALIVENESS layer ON TOP of the moveset + self-model,
not a separate system. Check-Before-Build: `expression/micro_expression.py` is BUILT (mood-driven 0.3-0.8s
pulses) but NOT wired into the turn loop; Unity already runs autonomous micro-expressions; squash-and-
stretch for eLo's own avatar is NEW (only game enemies have hop/squash).
- **Squash-and-stretch (Designer):** every move executes WITH weight — anticipation squash before a jump,
  stretch on launch, squash-settle on land; same for sit ease-down (partly there), wall-jump, drop. Reuse
  the existing deform rig (eLo_v2, 46 blendshapes) — reference-not-clone. Turns clip-playback into weighted life.
- **Micro-expressions (Builder + Designer):** driven by the Self Model's emotion + inner cognitive state
  (mood · curiosity · confidence · fatigue) — the face reflects what eLo IS, not random. Wire the built
  `micro_expression.py` into the loop + keep Unity's autonomous layer; the Self Model is the driver, so
  expression = truthful internal state, not decoration.
Relates to: the moveset (this spec) · Emotion→expression · Presence (idle aliveness) · face/LipSync ·
"Life emerges from continuity" + emergence-over-scripting. Track A (Designer) where cheap NOW; the
self-model-driven half sequences with the Self Model (WO-052A). Not the Presentable-6 — aliveness polish.

## 8. One capability, two triggers — autonomous = commandable (Designer + David 2026-08-06)
**GOVERNING PRINCIPLE:** everything eLo does autonomously — moves AND expressions — must ALSO be drivable
by the Executive, through the SAME underlying capability. Autonomous and commanded are never two divergent
paths; the one brain drives both. (Corollary of One Brain + Situated Self.)
- **Roam triggers (Designer-confirmed):** (1) `intent: explore|roam|wander|patrol|create` from eLo OS →
  `_biRoam` on → roams on command (DesktopBuddy:753); (2) autonomous presence-gate when David's away/idle
  → hops on his own (DesktopBuddy:943). Both resolve to the SAME move capabilities.
- **Free-form moves → commandable sub-types:** today fire-jump/wall-jump/step-back→run→fire are picked by
  CHANCE inside the roam (variants of a hop, not addressable) → can't be isolated/tested. Designer is
  wiring them into `ApplyMoveCommand → ExecuteNav → HandleNav` as sub-types (matches §3 + the ratified
  contract), tracing the autonomous flags (`_wrWallJump`/`parkour`/`_fireJumpNext`, DesktopBuddy ~1293-1594)
  so the COMMANDED version = the autonomous one EXACTLY — no divergence.
- **Expressions too:** the autonomous micro-expression / `EloExpression` layer must be self-model-drivable
  (emotion + cognitive state command it), same principle on the expression side (→ WO-062).

## 9. Take-five / exit = an EMBODIED move coordinated with eLo OS (David 2026-08-06) — fixes WO-045
David: *"exits need to be coordinated with eLo OS so take-five means he UNDERSTANDS it and EXITS the
screen — by jumping off or something,"* not just replying. So take-five is a MOVE, not a `SetVisible`:
```
eLo OS understands "take five / give me a minute" → emits an EXIT move_command (jump_off | run_off —
reuse the existing ExitSequence / run-off-screen choreography) → body performs the exit (a real move) →
move_complete ACK → hidden → ONLY THEN eLo says "stepping away" (Embodied Truth, ADR-Exec-001).
Return: return_command → run/hop back on, ACK, then speak.
```
Autonomous "going to my world" uses the SAME exit capability (principle §8). This is WO-045, reframed as
a moveset sub-type + say/do coupling — the reason it was rejected (it just replied) is exactly this.

## ✅ CHIEF ARCHITECT — RATIFIED with sharpenings (2026-08-06)
CA: this closes the gap between "eLo has animations" and "eLo has a body he understands." **Do NOT let it
become a movement system — it is a CAPABILITY system.** Sharpenings, all applied:
1. **Capabilities, not moves.** The Self Model stores CAPABILITIES with METHODS, not a flat move list:
   `Traverse vertical surface → {wall_jump · climb · leap}` · `Rest near David → {sit · perch · lean ·
   meditate}`. The CAPABILITY survives across embodiments; the METHOD changes (robot: step/climb/balance,
   no "wall_jump"). This is what protects One Brain, Many Embodiments.
2. **Embodiment Translation Layer (the one missing layer).** `Self Model → Embodiment Translator →
   {Desktop · Robot · AR · Game · Exhibition}`. Same INTENTION ("greet David") → different body (desktop
   wave · robot arm · AR hand-gesture · game anim). Future-proofing; desktop is only the first target.
3. **Split confidence:** `capability_confidence` (can I, in principle) · `execution_confidence` (can I do
   it well right now) · `environment_confidence` (is THIS surface/context suitable). "I can wall-jump, but
   not on this icy ledge" = high capability, low environment.
4. **Failure memory — store WHY.** Not "wall jump failed" but "wall jump failed: target outside reach."
   This is where RL connects (Capability Learning · ADR-Exec-005) — reasons, not just outcomes.
5. **Desire vs Decision.** Curiosity creates POSSIBILITIES ("I wonder what's behind that window"); the
   Executive makes DECISIONS ("not now"). Alive without being uncontrolled.
6. **Random → cognitive over time.** The move looks identical, but chance-picking is replaced by
   curiosity + affordance + energy + emotion → Executive → action (Track B). Invisible to the eye,
   everything to the architecture.
7. **Expression coherence:** body · face · voice must agree — one state, one truth (WO-062). No "jumping
   body / neutral face / philosophical voice."
8. **Take-five is the say/do PROOF (§9):** the smallest test that proves the whole architecture.

Priority sequence CONFIRMED: Presentable 6 → sit/move ACK → Self-Model capability registry → commandable
verbs → Embodied Truth → THEN curiosity / RL / free exploration / richer personality.

## Change control
Both seats + both architects sign. New move sub-types are FIELDS on the existing channels + capability records in the existing Self Model — never new files or a new driver.
