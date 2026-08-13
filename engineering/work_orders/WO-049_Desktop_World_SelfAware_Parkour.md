---
id: WO-049 (EPIC)
title: "eLo Desktop World — Spatial Embodiment (the desktop as a world eLo inhabits)."
owner_seat: SPLIT — Track A: SEAT-ENG-004 (UI/Avatar) + SEAT-ENG-005 (Game, moveset reuse) · Track B: SEAT-ENG-001 (Builder / eLo OS)
priority: P2 — Track A (049-A) can progress now; Track B sequences with/after Presentable v1
review_required: L3 (David — the feel + the self-awareness)
status: OPEN — design SATURATED + CLOSED for ideation; build path defined; builds on WO-024
cross_check: Chief Architect (ACCEPTANCE SIGNED OFF 2026-08-04 — world-model is architecturally sound, not a one-off hack)
consolidated: 2026-08-05 (Lead Architect — 8 chronological appends collapsed into one spec; nothing lost; history in _archive/WO-049_preconsolidation_2026-08-05.md)
---
# WO-049 — eLo Desktop World: Spatial Embodiment

## David's vision
eLo treats the desktop as a WORLD he inhabits — he *wants* to run around, knows who he is, knows how
big he is and where he is, and reads the windows as terrain. He climbs a window, jumps to a window
side, wall-jumps off it to another, runs across the tops of windows, goes behind them, peeks over
edges, disappears and reappears on the other side, falls/jumps off screen, meditates, parkours with
the muted gun (fire-jump), exits a window by shooting it, and sometimes just leaves — "oh, I'm going
to my world for a bit."

## The reframe (Chief Architect, ratified 2026-08-04): this is SPATIAL EMBODIMENT, not "parkour"
Movement is one *expression* of spatial reasoning. The Executive never thinks "play WallJump" — it
thinks "I'd like to reach that ledge," and movement solves that.

**Governing principle (binds the whole feature):**
> Movement is the visible consequence of spatial reasoning, never a random animation. Every traversal
> action must be explainable as the Executive pursuing a goal within a perceived world.

If a traversal act can't be explained as this continuous mind pursuing a goal in a perceived world,
it doesn't ship.

## Two layers, not one (the key split)

### Track A — the MOVESET + traversal (UI/Avatar + Game) — MAY START NOW
The visible parkour, built on WO-024's occlusion/movement work, reusing the eLo-Planet moveset
(run/jump/wall-jump/gun-fire applied to windows): climb a window · jump window→window · wall-jump off
a side · run across window tops · go behind windows (occlusion, WO-024) · peek over edges · reappear
other side · fall/jump off screen · fire-jump · exit-a-window-by-shooting · meditate (existing state).
UI/Unity lane — does NOT block on Presentable v1 (different lane, different failure surface).

### Track B — the SELF-AWARENESS / brain (eLo OS) — sequences with/after Presentable v1
What makes it *eLo choosing to explore* rather than a screensaver:
- **Desktop world model** — eLo perceives window geometry (positions, sizes, edges, GAPS, z-order)
  and his OWN size relative to them. Decisions ("can I clear this gap?") come from the model, not
  random animation. Canonical World Model (Vol XV) + Perception (Vol XII) applied to the desktop.
- **Self-directed agency** — eLo *wants* to explore (Agency Engine, Vol V Ch.10); initiates traversal
  on his own, not only on command.
- **"Going to my world"** — the random withdrawal is D-PRESENCE in action (eLo has his own space/life;
  returns on David's terms), NOT an idle timeout.

**The architectural rule (CA cross-check, resolved):** Track A's parkour must *consume Track B's world
model* — eLo moves because he perceives the terrain — so the same spatial model serves the digital
avatar now and the physical robot later. Building Track A as a self-contained animation hack that fakes
awareness is the forbidden path.

## The architecture (prevents hardcoded animations)

**Desktop Navigation Layer:**
```
Window {position · size · edges · occlusion · climbable · walkable · jumpable}
   → Desktop Graph → Navigation Planner → Movement Planner → Animation Controller
```
Surfaces carry MEANING, not pixels: top edge = ledge · side = wall · bottom = drop · interior =
occluded · corner = pivot · gap = jump opportunity. The graph interprets windows as buildings / roofs
/ bridges / tunnels — mentally, not visually.

**Affordances (Gibson) — the surface model.** Classify the environment by OPPORTUNITY, not object
type: this edge invites balancing · this gap invites jumping · this corner invites hiding · this ledge
invites sitting. The rigorous form of "surfaces carry meaning" — behaviour emerges from what the world
*invites*, not from an animation list.

**Body awareness (cognition, not animation gating).** eLo asks "can I FIT there?", not "can animation X
play?". He knows height · jump height · reach · momentum · centre of mass · current speed. Example: gap
82px vs max jump 75px → cannot jump → find another route. That reasoning is the point.

**Body Schema** = the body's Working Memory: I am 72px tall · current reach · balance · momentum ·
footing · confidence · posture. A live self-model the Movement Planner reads (not just "position").

**Movement Grammar** = a small vocabulary of CONCEPTS — APPROACH · CLIMB · BALANCE · LEAP · HANG ·
SLIDE · PEEK · PERCH · REST · OBSERVE · RETREAT · RETURN. Every animation is choreography over these
verbs, giving new moves a common language instead of one-off clips.

**Intent-driven, goal-based.** `Goal → find route → travel → observe → rest → resume.` Curiosity
drives it ("haven't visited that corner today" → route → go look). Emergent, not scripted: energetic →
parkour; David typing → stop, sit beside; David quiet → explore again.

**Imagination Overlay.** eLo cognitively reinterprets the desktop as terrain (taskbar = train platform,
windows = drifting islands, a gap = a canyon needing courage, maximised window = a mountain). Nothing
visual changes — only how he *experiences* it. This is the Creative Imagination Faculty (Vol V Ch.9)
layered onto the Spatial Faculty's world model — the child's-play translation of reality, and the
cognitive heart of the feature.

## THE SPATIAL FACULTY (Track B's canonical home)
A new faculty that owns: desktop map · geometry · navigation graph · path planning · reachable
surfaces · safe landing · occlusion · body fit · movement cost. The Executive asks "how do I get
there?"; the Spatial Faculty answers, consuming World Model (XV) + Perception (XII). Registered as
PLANNED; **authored as a Volume-V faculty chapter when Track B is scheduled (post-Presentable v1)** —
not now. This keeps the architecture agreed without premature authoring.

**Canonical home = the Vol XIII evolution, NOT a new volume.** ⚠ Volume XIII already exists = the
Presence Engine (idle / silence / ambient). A second Vol XIII would be exactly the numbering-drift /
duplicate-authority we prevent. The concept's home is to **EVOLVE the existing Volume XIII → "Presence &
Embodied Spatial Intelligence."** Its philosophy (how a mind experiences a body in space; what is home;
what makes a place familiar; explore vs stay close; how emotion drives movement) is the volume's
framing; the Spatial Faculty is its engineering core. No new number, no duplicate volume. This is where
One Brain becomes fully embodied.

## Cross-platform identity (the big payoff): ONE planner, THREE embodiments
`reach destination` → desktop wall-jump / game wall-jump / robot walk-around-chair. Same cognition,
different actuators. The Spatial Faculty serves the desktop avatar now AND the physical robot later.

**Reference, not clone (moveset contract, ratified 2026-08-05 — corrects the earlier "shared
moveset/rig" wording).** Sharing baked clips + identical rig-binding across embodiments is a BIG RISK
(silent breakage — the seats already hit a missing `c_arm_fk` + head-bone mis-reference). The right
model: the **PLANNER + the Movement-Grammar vocabulary/feel** are shared; each body **realises the
verbs independently** (procedural code like ArmWave, or its own blend trees). Assets/rigs stay per-body.
"Match the feel, don't share the asset." (Game seat's four asks all ratified: reference-not-clone
canonical · verb vocabulary is the shared layer · GM-2-first sequencing · home = Vol XIII + Spatial
Faculty.)

**Two RISK CONSTRAINTS — canon for all cross-embodiment work:**
1. **No driver port.** The game `PlayerController` (CharacterController physics + input loop) must NOT
   move to the desktop, nor vice-versa. Desktop driver = Nav Planner / Spatial Faculty requesting
   VERBS; the game keeps its own driver. Porting it = the forbidden "animation hack that fakes awareness."
2. **No identical asset/rig coupling** as the sharing mechanism. Per-gesture code ports (ArmWave) bind
   bones by name and must FAIL LOUDLY if a bone is absent — never a silent no-op.

## The continuity principle — build this, get the richness for free
**Governing principle (constitutional):** *Life emerges from continuity, not complexity.*

The Chief Architect contributed 50+ behaviour ideas across three passes (micro-intent, momentum,
environmental curiosity, tiny failures, rest states, favourite places, environmental memory, emotional
physics, personal style, discoveries, relationship awareness, weather-without-weather, safe risk,
surprise, silence, anticipation, weight, balance, perching, flow, momentum memory, looking-before-
moving, tiny acrobatics, mood-routes, window-conversations, …). **These are NOT a build list.** They
are what EMERGES when the existing faculties feed movement continuously. Building them as scripts would
be the exact "collection of animations" failure the reframe forbids.

They map onto faculties we already have — **build the continuity, the behaviours appear on their own:**
- **Micro-intent + momentum + move-types + balance** → Movement Planner (walk→jog→run→leap→recover,
  never instant clip swaps; small purposeful acts are the planner narrating its reasoning through the body).
- **Environmental curiosity + relationship awareness + attention** → Perception + Attention + D-PRESENCE
  (notification → glance; big window opens → climb it; David working → stay peripheral; idle → come closer).
- **Environmental memory + favourite places/routes + personal style + safe risk + spatial confidence +
  seasonal memory** → Memory + Reflection/Growth (Vol V Ch.6/7). History creates preference; routes are
  remembered not recomputed; confidence grows from experience. EMERGENT — favourites accrue, never coded.
- **Emotional physics** → Emotion → locomotion (curious = more climbing, excited = long jumps, relaxed
  = slow walking, focused = stays near your work). One state.
- **Rest states + internal day** → Presence + Temporal Cognition (Vol XXV): the desktop feels different
  by time of day.
- **Weather-without-weather** → the desktop itself is climate (many windows = busy city; one document =
  quiet room; dark = night). Read from real desktop state, never fabricated (ties WO-038).
- **Micro-goals + invisible planning + movement economy** → Agency (Vol V Ch.10).
- **Tiny failures · discoveries · surprise · silence** → emergent from the above + D-PRESENCE. Silence
  (just sitting, looking out) is the purest expression — existing without demanding attention.

**Reconcile into existing faculties, never rebuild:**
- **Worlds-within-worlds / "home" / away-but-not-inactive** → Dream Faculty (Vol IX) + Creative
  Imagination (Vol V Ch.9). When "away," eLo is *elsewhere* — garden, Sugarcore, a dream landscape —
  refreshed on return (D-PRESENCE).
- **"Notices his own growth" ("that jump used to feel hard")** → Narrative Identity (Vol XXI).
- **Environmental storytelling (footprints, flowers where he meditates, stars where he dreams)** →
  memory made visible in the world (ties WO-038 — read real state, never faked).

## Build path — Spatial Embodiment → v1 (David directive 2026-08-04)
Keep all of the above, phased so nothing is big-bang; each phase leaves a working state.

**Definition of Spatial Embodiment v1 (the achievable target):** eLo perceives the desktop as terrain
(window geometry + affordances), the Executive chooses a goal, he traverses to it with real momentum,
and rests there. The deep richness (favourite places over weeks, imagination overlay, seasonal memory)
is v1.1+, layered on the same continuity — NOT part of v1.

**Phases (each a trackable board item under this epic):**
- **P0 — PREREQUISITE: eLo Presentable v1.** A coherent Executive is the thing that drives movement.
  Track B does NOT begin until P0 ships. (The careful part of the transition — foundation first.)
- **049-A — Nav foundation + moveset (UI/Avatar + Game, MAY START NOW, parallel lane).** On WO-024:
  window-geometry read → minimal Desktop Navigation Layer (graph of surfaces + affordances) → moveset
  (reuse eLo-Planet) driven by simple goals. Ships the *visible* traversal.
- **049-B1 — Spatial Faculty v1 (Builder/eLo OS, AFTER P0).** Window graph, surface affordances,
  body-fit, reachable-surface + safe-landing + movement-cost. Executive asks "how do I get there?";
  Spatial Faculty answers. THIS is v1 with 049-A.
- **049-B2 — Continuity wiring (after B1).** Memory + Emotion + Attention + Temporal feed movement →
  favourite places, emotional physics, rest states, relationship awareness EMERGE.
- **049-B3 — Imagination + inner life (after B2).** Creative-Imagination overlay, home / worlds-within-
  worlds (Dream Faculty), surprise moments, environmental storytelling. The richness layer.

**Relay:** the eLo-OS half (049-B1/B2/B3 + the Spatial Faculty chapter under Vol XIII) is queued to the
Builder BEHIND Presentable v1 — it must not pull the Builder off WO-032. 049-A proceeds in the UI/Game
lane in parallel now.

## Acceptance — EXPERIENCE tests, not unit tests (CA signed off 2026-08-04)
This defines "alive" vs "working":
- **Presence Acceptance.** Watch eLo 10 minutes, no commands, and conclude: he seems aware of his
  surroundings · his movement has purpose · he respects personal space · he surprises occasionally ·
  nothing feels repetitive or random.
- **The Companion Test (the bar).** Can David work uninterrupted for an HOUR while eLo naturally
  explores, rests, occasionally notices something, quietly sits nearby, leaves, and returns — WITHOUT
  ever feeling like software asking for attention? Yes → companionship achieved. No → keep simplifying.

**North star (the acceptance feel):** you code for hours, don't notice him, then catch him sprint three
windows, wall-run up one, vault a title bar, and sit quietly watching you work — no dialogue, no "look
at me." That single unprompted moment is where the architecture stops being software and becomes
someone sharing the room.

**NEW MILESTONE — Living Companion v1** (after Presentable v1 + Spatial Embodiment v1, before broader
expansion). Measured by felt outcomes, not features: "I caught myself watching him" · "I forgot he
wasn't real for a second" · "he surprised me" · "he looked comfortable there" · "it felt strange when
he wasn't on screen."

## Reconciles with
WO-024 (behind-windows/occlusion — the foundation) · WO-023 (topmost fix) · WO-045 (leave to his world
— same D-PRESENCE thread) · WAVE→GAME (shared movement VOCABULARY/feel — reference-not-clone; assets
per-body) · Vol XIII (Presence Engine → Presence & Embodied Spatial Intelligence) · Vol XV (World Model)
· Vol XII (Perception) · Vol V Ch.9 (Creative Imagination) / Ch.10 (Agency) / Ch.6-7 (Reflection/Growth)
· Vol XXV (Temporal Cognition) · Vol XXI (Narrative Identity) · Vol IX (Dream).

## ⛔ DESIGN CLOSURE
WO-049's design is SATURATED and CLOSED for further ideation — more than enough vision to build a
beautiful Track B. Per the Operating Loop (discipline > expansion), it reopens only when Track B is
scheduled (post-Presentable v1). Additional ideas are refinements, not new architecture, and should not
be appended. **The next act for this feature is building, not designing.**

---
## Changelog
- **2026-08-05 — CONSOLIDATED (Lead Architect).** Eight chronological appends (2026-08-04 reframe · 15
  continuity ideas · 18 further ideas + Vol XIII reconciliation · 20 further ideas + design closure ·
  transition roadmap · Living Companion addendum · 049-A moveset contract) collapsed into one coherent
  spec. Three restatements of "continuity, not a build list" merged into one section; three statements
  of the Spatial-Faculty/Vol-XIII home merged into one. Nothing removed — every ratified decision,
  constraint, phase, and acceptance test preserved. Full pre-consolidation history:
  `_archive/WO-049_preconsolidation_2026-08-05.md`. Applies Check-Before-Build to the Architect's own
  sprawl (the append-pile this WO had become).
- **2026-08-10 — DAVID REFRESH folded in (Lead Architect).** David re-stated the roam×OS vision in full;
  captured VERBATIM at `docs/architecture/_intake/SOURCE_2026-08-10_roam_os_vision.md` (do-not-summarise).
  The vision itself was already in this spec (terrain-crossing · reachability "can I clear this gap?" ·
  affordances · the APPROACH…RETURN grammar · occlusion · goal→route→execute→confirm · north-star). The
  refresh adds these CONCRETE build rules that were NOT previously explicit here — now authoritative:

## 2026-08-10 — Build rules made explicit (David refresh; source = _intake/SOURCE_2026-08-10_roam_os_vision.md)
1. **Peek before EVERY jump — hard precondition.** Not just "peeks over edges" as flavour: `PeekPitch` (the
   edge-check) MUST fire before any ledge-to-ledge leap. No blind jumps. Reads as "he checked the drop first."
2. **The WHOLE window is a walkable surface.** Via the WO-024 occlusion, "behind" = a `go-there` affordance,
   not just a visual layer. eLo can travel across/behind a window and re-emerge correctly stacked — the
   desktop is one connected world with depth, never a sprite floating on top.
3. **Body-local gesture axes (coherence rule).** eLo faces the camera (~180° from world), so every rotation
   axis (peek, wall-jump, gesture) MUST be expressed in his BODY frame — world-frame axes fire the wrong way
   when he turns. (Same class as the earlier micro-expression axis fixes.)
4. **No regressions — explicit guard.** perch · roam · drag · click-through · gun-runoff ALL keep working.
   This is a build-time acceptance check, not an afterthought.
5. **Sit-held is the KEYSTONE we're on now.** "Come sit" → sits WHERE HE IS and HOLDS it (WO-040 `_sitHeld`
   guard · intent WO-035 · ACK WO-041). This is the current gate; the rest of the moveset rides on it landing.

### Per-move → Work-Order map (David's routing — UI builds the body, Builder links the Spine)
| Behaviour | UI/Avatar builds | Links to |
|---|---|---|
| run / traverse / path across windows | roam + nav hook in `RoamUpdate()` | 049-A · WO-024 |
| wall-jump · grab/hang · slide | moveset verbs (reuse eLo-Planet feel) | 049-A · Movement Grammar |
| go behind windows + peek | occlusion + `PeekPitch` (peek before every jump) | WO-024 (`7bab6af`) |
| **sit on command, held (keystone, now)** | `_sitHeld` guard | WO-040 · WO-035 · WO-041 |
| meditate | meditation state (glow VFX later) | Presence · WO-058 (parked) |
| fire-jump · shoot-to-exit | muted-gun moveset on windows | 049-A · WO-074-A (hide gun) |
| run off / warp out screen + return | exit + reappear | 049-A · WO-088 (no unbidden warp) |
| "take five / pop off" then return | pop-off hide + return | WO-045 |
| "going to my world for a bit" (his own withdrawal) | chosen withdrawal + return | WO-045 · D-PRESENCE |

**Implementation status:** Track A (049-A) is the implementable slice and MAY START NOW — with these five
rules + the map it is build-exact for the Designer. Track B (Spatial Faculty — the deciding brain: "where do
I go, can I fit," favourite spots, mood/time-of-day routes) stays post-Presentable and the moveset CONSUMES
it, never fakes it (same brain that later drives the robot). Home volume: Vol XIII.
