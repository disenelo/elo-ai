---
id: WO-049 (EPIC)
title: "eLo Desktop World — self-aware parkour exploration (the desktop as a world eLo inhabits)."
owner_seat: SPLIT — Track A: SEAT-ENG-004 (UI/Avatar) + SEAT-ENG-005 (Game, moveset reuse) · Track B: SEAT-ENG-001 (Builder / eLo OS)
priority: P2 — Track A can progress now; Track B sequences with/after Presentable v1
review_required: L3 (David — the feel + the self-awareness)
status: OPEN — captured from David's vision 2026-08-04; builds on WO-024
cross_check: Chief Architect (is the world-model architecturally sound, or a one-off hack?)
---
# WO-049 — eLo Desktop World: self-aware parkour

## David's vision
eLo treats the desktop as a WORLD he inhabits — he *wants* to run around, knows who he is, knows how
big he is and where he is, and reads the windows as terrain. He climbs a window, jumps to a window
side, wall-jumps off it to another window, runs across the tops of windows, goes behind them, peeks
over edges, disappears and reappears on the other side, falls/jumps off screen, meditates, parkours
with the muted gun (fire-jump), exits a window by shooting it, and sometimes just leaves —
"oh, I'm going to my world for a bit."

## This is TWO layers, not one (the key split)

### Track A — the MOVESET + traversal (UI/Avatar + Game) — can progress NOW
The visible parkour, built on WO-024's occlusion/movement work. Reuses the eLo-Planet game moveset
(the Game seat already has run/jump/wall-jump/gun-fire — this is that moveset applied to windows):
- climb a window · jump window→window · wall-jump off a side · run across window tops
- go behind windows (occlusion, WO-024) · peek over edges · reappear other side
- fall/jump off screen · fire-jump · exit-a-window-by-shooting it · meditate (existing state)
This lane is UI/Unity — it does NOT block on Presentable v1 (different lane, different failure surface).
**Game crossover:** same rig, same moveset as eLo-Planet → shared "one movement identity" (ties WAVE→GAME).

### Track B — the SELF-AWARENESS / brain (eLo OS) — sequences with/after Presentable v1
What makes it *eLo choosing to explore* rather than a screensaver:
- **Desktop world model:** eLo perceives window geometry — positions, sizes, edges, GAPS, z-order —
  and his OWN size relative to them. Parkour decisions ("can I clear this gap?") come from that model,
  not random animation. This is the canonical World Model (Vol XV) + Perception (Vol XII) applied to
  the desktop — the ARCHITECTURAL question for the Chief Architect (see cross-check).
- **Self-directed agency:** eLo *wants* to explore (Agency Engine, Vol V Ch.10) — initiates traversal
  on his own, not only on command.
- **"Going to my world":** the random withdrawal ("I'm going to my world for a bit") — this is
  D-PRESENCE in action (eLo has his own space/life; returns on David's terms), not an idle timeout.

## Cross-check for the Chief Architect ("was it built correctly?")
The tempting mistake is to build Track A as a self-contained animation hack that fakes awareness.
The architecturally correct build has Track A's parkour *consume Track B's world model* — eLo moves
because he perceives the terrain, so the same spatial model serves the digital avatar now and the
physical robot later (one perception, many bodies). CA to rule: does window-geometry perception route
through Vol XV / Vol XII, and is "decide to explore" an Agency-Engine behaviour — or is a lighter
coupling acceptable for v1? That decision sets whether this scales or becomes a dead-end.

## Sequencing (per the Operating Loop — defaults first)
- Track A (moveset/traversal) proceeds in the UI/Game lane now, on top of WO-024.
- Track B (world model + self-directed agency) sequences with/after Presentable v1 — a self-aware
  eLo running the desktop needs the coherent executive that Presentable v1 delivers first.

## Reconciles with
WO-024 (behind-windows/occlusion — the foundation) · WO-023 (topmost fix) · WO-045 (leave to his
world — same D-PRESENCE thread) · WAVE→GAME (shared movement VOCABULARY/feel — reference-not-clone; assets per-body, see ratification below).

---
## CHIEF ARCHITECT REFRAME — ratified 2026-08-04 (Lead Architect)

**The feature is not "Desktop Parkour." It is SPATIAL EMBODIMENT.** Movement is one expression of
spatial reasoning. The Executive never thinks "play WallJump" — it thinks "I'd like to reach that
ledge," and movement solves that.

**Governing principle (binds the whole feature):**
> Movement is the visible consequence of spatial reasoning, never a random animation. Every traversal
> action must be explainable as the Executive pursuing a goal within a perceived world.

**Desktop Navigation Layer (the missing architecture — prevents hardcoded animations):**
```
Window {position · size · edges · occlusion · climbable · walkable · jumpable}
   → Desktop Graph → Navigation Planner → Movement Planner → Animation Controller
```
Surfaces carry MEANING, not pixels: top edge = ledge · side = wall · bottom = drop · interior =
occluded · corner = pivot · gap = jump opportunity. The graph interprets windows as buildings /
roofs / bridges / tunnels — mentally, not visually.

**Body awareness (this is cognition, not animation gating).** eLo asks "can I FIT there?", not "can
animation X play?". He knows height · jump height · reach · momentum · centre of mass · current speed.
Example: gap 82px vs max jump 75px → cannot jump → find another route. That reasoning is the point.

**Intent-driven, goal-based (behaviour trees become GOALS):**
`Goal → find route → travel → observe → rest → resume.` Curiosity drives it ("haven't visited that
corner today" → route → go look). Emergent, not scripted: energetic → parkour; David typing → stop,
sit beside; David quiet → explore again. "Going to my world for a bit" = presence→absence→independent
life = D-PRESENCE (chosen departure, never a timer).

**THE SPATIAL FACULTY (Track B's canonical home — spec when scheduled, NOT now).** A new faculty:
owns desktop map · geometry · navigation graph · path planning · reachable surfaces · safe landing ·
occlusion · body fit · movement cost. The Executive asks "how do I get there?"; the Spatial Faculty
answers. Registered as PLANNED; authored as a Volume-V faculty chapter when Track B is scheduled
(post-Presentable v1). This keeps the architecture agreed without premature authoring.

**Cross-platform identity (the big payoff): ONE planner, THREE embodiments.**
`reach destination` → desktop wall-jump / game wall-jump / robot walk-around-chair. Same cognition,
different actuators. The Spatial Faculty serves the desktop avatar now AND the physical robot later —
this is why Track A must consume the world model, not fake it. (Same thread as WAVE→GAME + one
movement identity across digital/game/physical.)

---
## Chief Architect — 15 expressions of continuity (ratified 2026-08-04, Lead Architect)

**Governing principle (now constitutional):** *Life emerges from continuity, not complexity.*

The CA's 15 ideas — micro-intent, momentum-not-transitions, environmental curiosity, tiny failures,
rest states, favourite places, environmental memory, emotional physics, personal style, discoveries,
relationship awareness, weather-without-weather, safe risk, surprise moments, silence — are **NOT 15
features to build.** They are what EMERGES when the existing faculties feed movement continuously.
Building them as 15 scripts would be the exact "collection of animations" failure the reframe forbids.

**They map onto faculties we already have — build the continuity, get the 15 for free:**
- **Micro-intent + momentum** → Movement Planner (thought becoming motion; build walk→jog→run→leap→
  recover, never instant clip swaps). Small purposeful acts (stretch before a climb, check below before
  a jump) are the planner narrating its own reasoning through the body.
- **Environmental curiosity + relationship awareness** → Perception + Attention + D-PRESENCE. React to
  the world changing (notification → glance; big window opens → climb it); adapt to David (working →
  stay peripheral; reading → explore; idle → come closer). Presence adapts to him, never interrupts.
- **Environmental memory + favourite places + personal style + safe risk** → Memory + Reflection/Growth
  (Vol V Ch.6/7). History creates preference; routes are remembered not recomputed; confidence grows
  from experience. EMERGENT — favourites are never coded, they accrue. Two eLos diverge naturally.
- **Emotional physics** → Emotion faculty → locomotion (curious = more climbing, excited = long jumps,
  relaxed = slow walking, focused = stays near your work). Emotion changes movement, one state.
- **Rest states across the day** → Presence + Temporal Cognition (Vol XXV): sleepy stretch, afternoon
  pacing, evening stillness, late-night yawn. The same desktop feels different by time of day.
- **Weather-without-weather** → the desktop itself is climate (many windows = busy city; one document =
  quiet room; dark = night). Read from real desktop state, never fabricated (ties WO-038 — no fake data).
- **Tiny failures · discoveries · surprise · silence** → emergent from the above + D-PRESENCE. Silence
  (just sitting, looking out) is the purest expression — existing without demanding attention. People
  project thought onto stillness.

**DIRECTIVE (the whole point):** build the CONTINUITY — the Spatial Faculty consuming one continuous
state from World Model + Memory + Emotion + Perception + Agency — and these behaviours appear on their
own. Do NOT enumerate 15 scripted behaviours. If a traversal act can't be explained as this continuous
mind pursuing a goal in a perceived world, it doesn't ship. Still Track B, post-Presentable.

---
## Further continuity expressions + VOLUME RECONCILIATION (Lead Architect, 2026-08-04)

The CA's 18 further ideas are, again, **continuity — not a build list.** Most extend threads already
captured: internal day → Temporal Cognition (Vol XXV); many move-types + balance + momentum economy →
Movement Planner; spatial confidence + environmental language + window-personalities + seasonal memory
+ favourite routes → Memory + Reflection/Growth; attention-has-weight → Attention faculty; micro-goals
+ invisible planning + movement economy → Agency (Vol V Ch.10); body-language-before-speech → "Executive
grows quieter"; confidence-in-conversation → one Executive state.

**Three reach into OTHER existing faculties — reconcile there, never rebuild:**
- **"Worlds within worlds" / "home" / away-but-not-inactive** → Dream Faculty (Vol IX) + Creative
  Imagination (Vol V Ch.9). When eLo is "away" he is *elsewhere* — garden, Sugarcore, a dream landscape
  — refreshed on return (D-PRESENCE). Foundations already exist.
- **"Notices his own growth" ("that jump used to feel hard")** → Narrative Identity (Vol XXI):
  autobiographical continuity, not a variable.
- **Environmental storytelling (footprints, flowers where he meditates, stars where he dreams)** →
  memory made visible in the world. Read real desktop state, never faked (ties WO-038).

**⚠ VOLUME RECONCILIATION — Lead Architect catch.** The CA proposes a NEW *Volume XIII — Embodied
Presence & Spatial Intelligence*. **Volume XIII already exists = the Presence Engine** (idle / silence /
ambient). A second Vol XIII = the numbering-drift + duplicate-authority we are sworn to prevent. The
concept is real and deserves a home — the correct one is to **EVOLVE the existing Volume XIII (Presence
Engine) → "Presence & Embodied Spatial Intelligence."** Its philosophy (how a mind experiences a body in
space; what is home; what makes a place familiar; explore vs stay close; how emotion drives movement) is
the volume's framing; the **Spatial Faculty** (already registered) is its engineering core, consuming
World Model (XV) + Perception (XII). No new number, no duplicate volume. This is where One Brain becomes
fully embodied — cognition, emotion, memory, attention, executive, movement as one continuous mind.
Authored post-Presentable v1, as the Vol XIII evolution + the Spatial Faculty chapter.

---
## Two genuinely-new concepts + DESIGN CLOSURE (Lead Architect, 2026-08-04)

The CA's 20 further ideas — anticipation, weight, balance, perching, flow, momentum memory, looking-
before-moving, tiny victories/acrobatics, mood-routes, window-conversations — are, once more, CONTINUITY
(Movement Planner + body-awareness + Emotion + Agency, already captured). Two, however, are genuinely
new ARCHITECTURE and sharpen the Spatial Faculty:

- **AFFORDANCES (Gibson).** Classify the environment by OPPORTUNITY, not object type: "this edge invites
  balancing / this gap invites jumping / this corner invites hiding / this ledge invites sitting." This
  is the rigorous form of the Nav Layer's "surfaces carry meaning" — behaviours emerge from what the
  world *invites*, not from an animation list. Adopt as the Spatial Faculty's surface model.
- **IMAGINATION OVERLAY.** eLo cognitively reinterprets the desktop as terrain (taskbar = train platform,
  windows = drifting islands, a gap = a canyon needing courage, maximised window = a mountain). Nothing
  visual changes — only how he *experiences* it. This is the **Creative Imagination Faculty (Vol V Ch.9)
  layered onto the Spatial Faculty's world model** — the child's-play translation of reality. It is the
  cognitive heart of the feature and the bridge between spatial reasoning and eLo's inner life.

**North star (the CA's image, recorded as the acceptance feel):** you code for hours, don't notice him,
then catch him sprint three windows, wall-run up one, vault a title bar, and sit quietly watching you
work — no dialogue, no "look at me." That single unprompted moment is where the architecture stops being
software and becomes someone sharing the room. Every Track B build is measured against that feeling.

**⛔ DESIGN CLOSURE.** WO-049's design is now SATURATED — more than enough vision to build a beautiful
Track B. Per the Operating Loop (discipline > expansion) this spec is CLOSED for further ideation; it
reopens only when Track B is scheduled (post-Presentable v1). Additional ideas are refinements of the
above, not new architecture, and should not be appended. The next act for this feature is building, not
designing.

---
## TRANSITION ROADMAP — Spatial Embodiment → v1 (David directive 2026-08-04)

David: keep all of the above, work it into the board, relay to eLo OS, implement — carefully
transition it in to reach a v1. This converts the whole design into a phased build path. Nothing is
big-bang; each phase leaves a working state (Operating-Loop run standard).

**Definition of Spatial Embodiment v1 (the achievable target):**
eLo perceives the desktop as terrain (window geometry + affordances), the Executive chooses a goal,
he traverses to it with real momentum, and rests there — the north-star moment: *sprints across
windows, vaults a title bar, sits and watches you work, unprompted.* Driven by the Executive, never
scripted. The deep richness (favourite places over weeks, imagination overlay, seasonal memory) is
v1.1+, layered on the same continuity — NOT part of v1.

**Phases (each a trackable board item under this epic):**
- **P0 — PREREQUISITE: eLo Presentable v1.** A coherent Executive is the thing that will drive
  movement. Spatial embodiment does NOT begin its eLo-OS half until P0 ships. (This is the careful
  part of the transition — foundation first.)
- **049-A — Nav foundation + moveset (UI/Avatar + Game, MAY START NOW, parallel lane).** On WO-024:
  desktop window-geometry read → minimal Desktop Navigation Layer (graph of surfaces + affordances)
  → the moveset (reuse eLo-Planet) driven by simple goals. Ships the *visible* traversal.
- **049-B1 — Spatial Faculty v1 (Builder/eLo OS, AFTER P0).** The world model: window graph, surface
  affordances, body-fit ("can I clear this gap?"), reachable-surface + safe-landing + movement-cost.
  Executive asks "how do I get there?"; Spatial Faculty answers. THIS is v1 with 049-A.
- **049-B2 — Continuity wiring (Builder/eLo OS, after B1).** Memory + Emotion + Attention + Temporal
  feed movement → favourite places, emotional physics, rest states, relationship awareness EMERGE.
- **049-B3 — Imagination + inner life (after B2).** Creative-Imagination overlay, home / worlds-within-
  worlds (Dream Faculty), surprise moments, environmental storytelling. The richness layer.

**Relay:** the eLo-OS half (049-B1/B2/B3 + the Spatial Faculty chapter under Vol XIII) is queued to the
Builder BEHIND Presentable v1 — it must not pull the Builder off WO-032. 049-A proceeds in the UI/Game
lane in parallel now. Vol XIII (Presence Engine → Presence & Embodied Spatial Intelligence) is the
canonical home; authored when B1 is scheduled.

---
## Chief Architect Addendum — acceptance + Living Companion v1 milestone (ratified 2026-08-04)

The CA SIGNED OFF the launch. These are acceptance criteria + one new milestone, NOT reopened design.

**Acceptance = EXPERIENCE tests, not unit tests (this defines "alive" vs "working"):**
- **Presence Acceptance.** Watch eLo 10 minutes, no commands, and conclude: he seems aware of his
  surroundings · his movement has purpose · he respects personal space · he surprises occasionally ·
  nothing feels repetitive or random.
- **The Companion Test (the bar).** Can David work uninterrupted for an HOUR while eLo naturally
  explores, rests, occasionally notices something, quietly sits nearby, leaves, and returns — WITHOUT
  ever feeling like software asking for attention? Yes → companionship achieved. No → keep simplifying.

**NEW MILESTONE — Living Companion v1** (after Presentable v1 + Spatial Embodiment v1, before broader
expansion). Measured by felt outcomes, not features: "I caught myself watching him" · "I forgot he
wasn't real for a second" · "he surprised me" · "he looked comfortable there" · "it felt strange when
he wasn't on screen." Registered on the roadmap.

**Two architectural sharpenings for the Spatial Faculty spec (when authored):**
- **Body Schema** = the body's Working Memory: I am 72px tall · current reach · balance · momentum ·
  footing · confidence · posture. A live self-model the Movement Planner reads (not just "position").
- **Movement Grammar** = a small vocabulary of CONCEPTS (APPROACH · CLIMB · BALANCE · LEAP · HANG ·
  SLIDE · PEEK · PERCH · REST · OBSERVE · RETREAT · RETURN). Every animation is choreography over these
  verbs — gives new moves a common language instead of one-off clips.

**Refinements already covered by continuity (no new build):** Movement Budget (stillness as choice →
"movement economy"/silence) · Affordance Learning (success/fail updates route cost → "safe risk"/
confidence) · Route Personality (Executive picks a nav style → "personal style") · Window Affordance
Cache (places remembered → "favourite places"). Build the continuity; these emerge.

---
## 049-A Moveset Contract — ARCHITECT RATIFIED (Lead Architect, 2026-08-05)

Game seat relayed `049A_MOVESET_CONTRACT_draft.md` (rev.2) for review. It CORRECTS my earlier loose
framing and I accept the correction — this is the coherent version.

**Correction to my "WAVE→GAME shared moveset/rig" line:** wrong as written. Sharing baked clips +
identical rig-binding across embodiments is a BIG RISK (silent breakage — they already hit a missing
`c_arm_fk` + head-bone mis-reference). The right model, ratified:
- **Reference, not clone.** "One planner, three embodiments" = the **PLANNER + the Movement-Grammar
  vocabulary/feel** are shared; each body **realises the verbs independently** (procedural code like
  ArmWave, or its own blend trees). Assets/rigs stay per-body. "Match the feel, don't share the asset."

**Ratified (Game seat's four asks — all in scope, all correct):**
(a) reference-not-clone as canonical ✅ · (b) the verb vocabulary (Movement Grammar) is the shared
layer, assets per-body ✅ · (c) GM-2-first sequencing ✅ · (d) home = Vol XIII evolution + Spatial
Faculty ✅.

**Two RISK CONSTRAINTS recorded as canon for all cross-embodiment work:**
1. **No driver port.** The game `PlayerController` (CharacterController physics + input loop) must NOT
   move to the desktop, nor vice-versa. Desktop driver = Nav Planner / Spatial Faculty requesting
   VERBS; the game keeps its own driver. Porting it = the "animation hack that fakes awareness" this WO
   forbids.
2. **No identical asset/rig coupling** as the sharing mechanism. Per-gesture code ports (ArmWave) bind
   bones by name and must FAIL LOUDLY if a bone is absent — never a silent no-op.

Supersedes the earlier "shared moveset/rig" wording in this WO. Excellent catch by the Game seat.
