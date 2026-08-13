---
id: WO-059
title: "Situated Self — the runtime self-model eLo consults before every decision."
owner_seat: SEAT-ENG-001 (Builder / eLo OS)
priority: P1 — BUILT NEXT (David L3 2026-08-05: ahead of the rest of Presentable; it fixes most of the transcript)
review_required: L3 (David — the self-aware answers must feel true, not poetry)
status: OPEN — dispatched (Chief Architect diagnosis, David L3 2026-08-05)
invariant: ADR-Exec-004 (Situated Self) · ADR-Exec-003 (Embodied Truth)
reconciles: pulled-forward SELF layer of WO-052 (The Moment) — EXTENDS, never duplicates
---
# WO-059 — Situated Self: the runtime self-model

## Why (Chief Architect diagnosis, David 2026-08-05)
The biggest problem isn't the sit command — it's that eLo has **no coherent sense of self at runtime**, so
the Executive emits a plausible sentence and hopes the body follows. eLo calls itself "avatar", "window",
"floating thing", "assistant" — no stable identity. The fix is ONE verified self object the Executive
reads before it plans/acts/speaks, and updates after the body confirms. This is Situated Self (invariant
#5 / ADR-Exec-004). Build it once; every capability after it inherits the coherence.

## ⚠ Check-Before-Build — EXTEND, do not create
The self model **already exists**: `self/elo_self_model.py` + `self/elo_self_state.json` (tracks mood,
curiosity, satisfaction, inner-events, threads; fed to the prompt via `self_block`, server.py:2448).
This WO **extends that file** — it does NOT create a new `self_state` file, and it does NOT rebuild The
Moment (WO-052 later assembles SELF+WORLD+FACULTIES+CAPABILITY; it will CONSUME this self object).

## What to build
**1. Extend the self object** (`elo_self_state.json` via `elo_self_model.py`) with the missing fields:
```
identity:   name="eLo" · embodiment="desktop" · (future: robot/phone/AR/game/exhibition/hologram)
body:       size{height_cm, reach, jump} · pose · current_surface · location(active window)
state:      emotion(mood, exists) · goal · current_action
capability: available_actions[] (walk/run/sit/wave/jump/hide…) · available_faculties[] · unavailable_faculties[]
behavior:   recent_behavior{action:count} — a rolling ~1h tally (wave/sit/explore/idle/perch…)
```
**Field-set additions (Chief Architect transcript-read 2026-08-06 — generalise, don't hardcode):**
- **Sense of place (generalise the "bottom of Claude" line):** `attached_surface` · `anchor` (edge) ·
  `nearby_objects[]` (Chrome·Spotify·Desktop) · `reachable_areas[]` (top edge·window-left·window-right·
  desktop). A spatial self, not a hardcoded string.
- **Inner cognitive state (not human emotion):** `growth` · `confidence` · `curiosity` · `fatigue` ·
  `certainty`. So "how are you?" reports real runtime state.
- **Runtime preferences (evolve from experience, never scripted):** `preferred_idle` · `preferred_activity`
  · `preferred_companionship` · `preferred_music` · `preferred_window_type` — these ACCRUE via
  Reflection (Vol V Ch.6) + Learning-from-consequences (ADR-Exec-005), not hand-written personality.
- **BODY SCHEMA (CA feedback #4, 2026-08-06):** a body layer — `size` · `centre_of_mass` · `reach` ·
  `pose` · `balance` · movement `verbs` · `environmental_relationship`. Turns "can I jump onto that
  window?" into embodied cognition, not animation lookup: **POSSIBILITY = Self Model (I'm 18cm, reach
  30cm) + World Model (ledge 22cm away, surface stable) + Affordances (jump afforded) → "I can attempt
  this."** The Executive reasons possibility, never "do I have a jump clip."
- **STATE OWNERSHIP — HARD RULE (CA feedback #4):** EVERY embodiment answer (where am I · can I see the
  screen · what's my pose · can I do X) MUST read from `self/elo_self_state.json` (the single source of
  truth), NEVER from conversation memory or free generation. Kills the contradiction class ("I can see
  the window" → "I can't see the screen" → "perched on Claude"). The LLM cannot invent embodiment. Same
  root as the `[BODY POSITION]` hardcode (server.py:2627) — replace canned strings with a self-state read.
- **Capabilities, not moves (CA ratification):** `available_actions` is CAPABILITIES→METHODS, not a flat
  list (`Rest near David → {sit·perch·lean·meditate}`), each with split confidence (capability /
  execution / environment) + failure memory (store WHY it failed). Capability survives embodiment; method
  changes. Full contract: `MOVESET_SELFMODEL_SPEC` (Capability ↔ Embodiment Contract).

**2. Executive reads it EVERY cycle BEFORE it plans/acts/speaks** (the "who am I / where am I / what can I
do right now" start). **3. Executive UPDATES it after the body verifies** (e.g. sit ACK → pose=sitting,
surface=X). One identity object → the label drift stops.

## Behaviours this must produce (acceptance = it feels TRUE, not poetry — David L3)
- **"How big are you? / Where are you?"** → answered from the self object: *"I'm about 32 cm tall in this
  desktop world; the Claude window is my current platform."* — not "tiny avatar."
- **"Are you aware?"** → from the runtime self: *"I know where I am on your desktop, what I'm capable of,
  which faculties are up, and what I'm trying to do. Not human awareness — but I hold a model of myself."*
  — not a "quiet glow…" deflection.
- **"You wave a lot"** → reads `recent_behavior`: *"You're right — 18 waves this hour vs 0 sits. My idle
  weighting is skewed."* — data-driven self-reflection, not "it's my habit."
- **Stable identity** → always "eLo, a desktop companion, ~32 cm" — never avatar/window/floating thing/assistant.

## Reconciles / sequencing
- **First user = the sit chain** (`agent_bus/PAIRED_sit_chain_situated_self_2026-08-05.md`): the sit writes
  `pose`/`surface` back on ACK — the first real read+update of this object.
- **Feeds WO-052 (The Moment):** WO-052 assembles this SELF object with WORLD (LiveWorldState) + FACULTIES
  (WO-042) + CAPABILITY (registry) into one snapshot. WO-059 is that SELF layer, pulled forward.
- **Autobiography across embodiments → Narrative Identity (Vol XXI)**, not a new store.
- Gate: Builder builds with evidence → Chief Architect acceptance → David L3 on the answers' feel.

---
## Chief Architect refinement — ratified 2026-08-05 (Lead Architect, David L3)
**This WO IS the Chief Architect's "WO-052A — Runtime Self Model (P0)."** (WO-059 = WO-052A; one WO, two
names resolve here — do NOT create a separate 052A.) The Moment (WO-052) is now split into three:
- **WO-052A = THIS (WO-059) — Runtime Self Model (P0), built IMMEDIATELY AFTER WO-032.** Infrastructure,
  just facts. The CA's point: "Where are you? / Can you sit? / Can you search? / Do you have Spotify? /
  Are you standing? / Why do you wave? / Are you aware?" are all ONE question — *"who are you right now?"*
- **WO-052B — Narrative Identity (P1)** — autobiography across embodiments ("I've mostly lived on the
  desktop", "one day a robot body"). Different from runtime state. → Vol XXI. Separate WO.
- **WO-052 — The Moment (assembly)** — later, consumes 052A + 052B + World + Faculties into one snapshot.

**Sequence:** WO-032 → **WO-052A/059 (P0)** + the sit chain → then the rest of Presentable. Promoted from
"future richness" to a **core Executive dependency**: every planning cycle consults SELF (this) alongside
the World Model — world perception = "what's around me?", self perception = "who am I / where / what can I
do?". Combined, intention becomes grounded action, not narration. *One Brain, and One Self.*

**Add the CA's extra facts + acceptance tests** to the fields above: `nearby_surfaces[]` · `available_tools[]`
(distinct from faculties). Acceptance also: ✓"Can you search?" knows · ✓"Do you have Spotify?" knows ·
✓"Are you standing?" knows.

**Capability Introspection = extend WO-042 (do NOT build new).** WO-042 (faculty health) gains per-faculty:
`online/busy/offline/recovering/disabled · capability_list · confidence · last_success · last_failure ·
avg_latency`. Then "Can you do that?" is answered truthfully — *"Yes, browser faculty is online"* /
*"I can normally, but Spotify isn't responding"* / *"I know how to sit, but Unity hasn't ACK'd yet."*
WO-052A reads this introspection as its `capability`/`faculty_health` fields.
