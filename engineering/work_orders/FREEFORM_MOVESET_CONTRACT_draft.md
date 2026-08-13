# Free‑Form Moveset Contract (DRAFT) — eLo strings his moves organically
**For SEAT‑ENG‑001 (Builder / eLo OS) + SEAT‑ENG‑004 (Designer / UI‑Unity). David L3 2026‑08‑06.**

> Filed by Designer per David: *"he can do the fire‑jump into a drop, walk backwards (stepback already coded) run gunjumpfire (muted weapon)… this would make eLo more free‑form — wire this to the board for a contract with Builder and the Designer."*

**Why:** eLo's traversal should read as *him choosing* — combining the EXISTING move verbs free‑form (fire‑jump into a drop, step‑back → run → fire‑jump), not fixed clip sequences. Builds on the ratified **049‑A moveset contract** (reference‑not‑clone, verbs, no PlayerController port) + the **IO Contract** (`<action>_command` DOWN → execute → `<action>_complete` UP → verify → speak).

## The verb vocabulary — EXISTING Unity states, reuse don't rebuild
| Verb | Unity state | Gun | Where it lives |
|---|---|---|---|
| walk / run / idle | Walk · Run · Idle | hidden | base locomotion |
| leap (across) | eLo_LongJ | hidden | `PlayJump` |
| WALL‑JUMP (up) | Parkour + `_wrWallJump` | **hidden** | springy tall arc `wallJumpArcMul`; `PlayParkour` (Parkour isn't a gun state → weapon hidden) |
| step‑back windup | `_backingUp` (reverse Walk) + run‑up (`runUpSecs`/`parkourRunUpSecs`) | hidden | already coded, gated to up‑wall‑jumps |
| FIRE‑JUMP | Gun‑Jump‑Fire | **shown** (muted) | `PlayGunJumpFire` |
| fire‑run | GunFire‑Run | shown | `PlayGunRun` |
| drop | eLo_LongJ (elongated fall) | hidden | walk‑to‑edge `_wdActive` |
| peek | `PeekPitch` (HeadLook) | — | look toward target / down before a leap |

## The free‑form combos (Designer builds the body)
1. **Peek‑at‑target → leap** — ✅ BUILT this session (walk to take‑off edge, `_wdHop` peek toward target, leap).
2. **Fire‑jump → drop** — ◐ PARTLY BUILT (`freeroamFireJumpChance` makes a walk‑to‑edge DROP a `Gun-Jump-Fire`, gun shown just for the leap). Extend: chain into the fall cleanly.
3. **Step‑back → run → fire‑jump** — ▶ NEW: reuse the `_backingUp`/run‑up windup (already coded for up‑wall‑jumps) then chain into `Gun-Jump-Fire` (muted weapon) — a *running fire‑jump with a windup*.
4. **Wall‑jump (gun‑hidden, up)** — ✅ EXISTS (`PlayParkour` + `_wrWallJump`).
These **combine organically per terrain** (peek → step‑back → run → fire‑jump → drop → wall‑jump), chosen by chance/affordance — free‑form, never a fixed sequence.

## The Builder ↔ Designer split (the IO‑Contract loop)
- **DESIGNER (UI):** build each combo in DesktopBuddy's roam as a variant reusing the existing states (`Gun-Jump-Fire`, `Parkour`, `_backingUp`, `PeekPitch`); autonomous roam picks them per terrain + a tunable chance. On a **commanded** move, emit `move_complete` ACK to `unity_events.json` tagged with the move sub‑type (per IO Contract). No new avatar driver — extend the existing roam.
- **BUILDER (eLo OS):** register these as **capabilities** in the self‑model (eLo KNOWS he can fire‑jump / wall‑jump / step‑back‑run); the Executive DECIDES when to string them (free‑form intent) → emits `move_command` DOWN with the sub‑type; gates the *"I moved / went down there"* line on `move_complete` UP; honest on no‑ACK.
- Both: **reference‑not‑clone**, verb vocabulary, no PlayerController port (049‑A contract).

## Schema (extends the existing move channel — NO new files, per the IO Contract)
- DOWN `blender_state.json`: `move_command: {"type": "fire_jump" | "wall_jump" | "step_back_run_fire" | "drop" | jump_left/right/top/bottom | shift, "_ts", "target"?}`
- UP `unity_events.json`: `{"type":"move_complete", "move":"<sub-type>", "_ts"}` (already direction‑tagged; sub‑types added).

## Now / Later
- **NOW (Designer, Track A):** the autonomous free‑form combos in the roam (build the body). Started this session: peek‑at‑target, fire‑jump‑down; wall‑jump already exists. Remaining: step‑back→run→fire‑jump chain + fire‑jump→drop polish.
- **LATER (Builder, post‑Presentable):** the Executive DECIDING the combos (Spatial Faculty / Agency picks moves per goal + terrain), each gated on the ACK.

## Change control
Both seats sign. New move sub‑types are FIELDS on `move_command`/`move_complete` — never new files (IO Contract §governing rule).

---
## ✅ ARCHITECT RATIFIED — 2026-08-06 (Lead Architect, David L3 path — same as the 049-A contract)
Cross-checked; RATIFIED. Consistent with canon on every axis:
- **049-A moveset contract** — this EXTENDS it (free-form chaining of the SAME verbs); reference-not-clone,
  no PlayerController port. Not a duplicate (Check-Before-Build ✓).
- **IO Contract** — `move_command` DOWN / `move_complete` UP, sub-types as FIELDS not files ✓.
- **Affordance Before Action (WO-056)** — combos chosen by affordance/terrain, not a fixed sequence ✓.
- **Spatial Faculty (Track B)** — the Executive DECIDING the chaining is correctly placed post-Presentable ✓.
- **Emergence-over-scripting / Learning (ADR-Exec-005)** — free-form, not scripted; later the chaining is
  exactly what RL's Movement domain (Vol XXVIII) can LEARN ✓.

**Two sequencing sharpenings (adjustments, not blockers):**
1. **NOW (Designer, Track A)** = the autonomous free-form combos in roam — a PARALLEL lane; it must NOT
   delay the Presentable-6 sit/movement close (sit = Builder's semantic-intent fix; Designer's build currency).
2. **Split the Builder half:** CAPABILITY REGISTRATION (eLo KNOWS he can fire-jump / wall-jump /
   step-back-run) folds into **WO-052A Self Model** (near-term — it's `available_actions`). The Executive
   DECIDING the free-form chaining = **Track B / post-Presentable** (Spatial Faculty + Agency).

Ratified as part of the 049-A moveset program (no new driver, no new files). Both seats sign; new
sub-types are fields on the existing channels.

---
## Implementation approach (Designer, 2026-08-06) — the ONE BRAIN drives the body
David's systemic point: *"look how much is built and NOT verified to be used by eLo OS."* The rule this
locks in: **the one brain must drive the body — moves, expressions, exits — nothing fires autonomously
divorced from eLo OS** (UI and the one brain must not drift apart; canonised in ARCHITECTURAL_PRINCIPLES,
"Autonomous and commanded are one capability").
- **Commanded reuses the autonomous resolver — no new logic (reference-not-clone at its cleanest).** The
  inline jump logic already resolves parkour / wall-jump / drop from the TARGET GEOMETRY (DesktopBuddy
  ~1293-1294: `parkour = … hopDist ≤ ParkourReach()`; `_wrWallJump = parkour && dyL > combatLevelStep`).
  A COMMANDED free-form move just supplies the right TARGET + a STYLE FLAG (force wall-jump / fire-jump)
  and rides the SAME resolver the autonomous roam uses → commanded == autonomous, exactly, no divergence.
  Guard: confirm the parkour-CHAIN start (`wrParkourLeft`) doesn't run away when a single move is forced.
- **Exits (WO-045):** take-five is an embodied EXIT move coordinated with eLo OS (jump_off/run_off via the
  existing `ExitSequence`), ACK'd, THEN speak. Full flow: self-model spec §9.
- **Expressions:** the autonomous micro-expression / `EloExpression` layer must likewise be self-model-
  drivable (→ WO-062) — same rule, expression side.
- **Built ≠ driveable ≠ verified:** a move counts as DONE only when eLo OS can command it AND it's been
  tested (the sit/move arbiter, per sub-type). Autonomous-only = not done.
Companion self-model spec: `MOVESET_SELFMODEL_SPEC_draft.md` (how the Self Model knows / decides / updates).
