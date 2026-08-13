# Embodied Cognition — grounded reconciliation + scope (Lead Architect, 2026-08-05)

David's instruction: *read what's there, align what's possible, show what interlinks — not the
skeleton, the real scope.* This is that. Every "EXISTS" below is a real file in the repo.

## The leap, in one line
The Executive today asks **"what should I say?"** It should ask **"what exists, what can I perceive,
what am I capable of, what have I actually done — and only then, what do I say or do?"** That's the
shift from a chatbot driving an avatar to an embodied companion with a truthful sense of being.

## Two principles this establishes (proposed for canon)
- **Embodied Truth** — eLo believes it has acted only when its *body confirms* the action. Extends
  Verified Speech (ADR-Exec-001) into embodiment: `Thought → Decision → Body → Confirmation → Belief
  → Speech`, never `Thought → Speech → hope the body catches up`.
- **Embodied Cognition** — eLo always reasons from an accurate model of *self, world, and capability*
  before choosing speech or action. Every behaviour begins with awareness, not animation.

---

## What ALREADY EXISTS (grounded — ~70% of the "Cognitive Self Model" is built)

| CA concept | Reality in the code | Status |
|---|---|---|
| Capability Registry ("what can I do?") | `runtime/capabilities/registry.py` — **48 capabilities** | ✅ EXISTS |
| Cognitive Self Model ("who am I / mood / energy") | `self/elo_self_model.py` + `self/elo_self_state.json` — tracks mood, curiosity, satisfaction, inner-events, session-read, threads; fed to the prompt via `self_block` (server.py:2448) | ✅ EXISTS |
| LiveWorldState ("what exists around me") | `world/live_world_state.py` — `assemble_world_state()` builds a typed world object **with per-domain `confidence` + `source` + `live/cached/stale/absent` status, and a rule: "never fabricated."** Holds DesktopState (active app/window), avatar_online, presence_mode, part_of_day | ✅ EXISTS (this is Vol XV, realised) |
| Memory confidence ("never say 'I think' unless confidence is low") | The confidence+source+status pattern is **already built into LiveWorldState** — just not yet applied to memory *recall* | ⚠️ pattern exists, apply to recall |
| Faculty Health page ("Movement DEGRADED → don't promise movement") | `runtime/faculty_health.py` (WO-042) — `mark_degraded/mark_recovered`, reasoning faculty tracked | ⚠️ building (WO-042) |
| Verify-before-speak / movement ACK | `server.py:95` — **`_PENDING_SIT` tracker already exists**: "set when a sit/move intent fires, cleared on timeout or when Unity ACKs completion" (WO-041) | ⚠️ scaffold started, ACK loop open |
| Reflection (for Capability Learning) | Vol V Ch.6 Reflection & Growth | ✅ EXISTS |

**The headline:** eLo already has an inner self-model, a confidence-scored non-fabricated world state
with desktop awareness, a 48-capability registry, a faculty-health registry, and a started sit-ACK
tracker. The "Embodied Self Faculty" the CA describes is largely these parts — **unassembled.**

---

## What's genuinely MISSING (the real, small net-new)

1. **ASSEMBLY — the Cognitive Self Model.** The parts above live as separate objects. Compose them into
   ONE object the Executive reads **every cycle** before it speaks or acts: `SELF (self-model) · BODY
   (schema) · WORLD (LiveWorldState) · FACULTIES (health) · TOOLS/CAPABILITIES (registry) · SYSTEM
   (backend/health)`. This is integration, not new faculties.
2. **ACK LOOP closure (Embodied Truth core).** `_PENDING_SIT` waits for a Unity ACK Unity doesn't send.
   Wire: Unity emits movement-completion → clears pending → Executive gains permission to speak. Fixes
   the sit say/do gap (WO-040/041) — the single biggest live bug.
3. **BODY SCHEMA (Embodied Self).** LiveWorldState has the world; it lacks the *body*: height, feet,
   bounding box, current surface, velocity, and **affordances** (can climb/jump/vault/wave here). This
   is WO-049's Body Schema + the Spatial Faculty. eLo reasons "can I fit there?", not "play sit."
4. **Memory recall confidence.** Apply the LiveWorldState confidence+source pattern to `memory/vault_
   layer.lookup()` → recall returns `{memory, confidence, timestamp, source}` or "unable — memory
   offline", never a vague "I think…".
5. **MOVEMENT QUEUE.** Overlapping requests ("Sit? Seat? Sit?") need a queue with current/queued/
   cancelled — not silent drops. New, small.
6. **CAPABILITY LEARNING.** After a failure, record a rule-candidate ("movement promise failed, no ACK,
   ×12 today → rule: never announce movement before ACK") → memory candidate → after N, eLo proposes a
   WO. Operational self-improvement; sits on Reflection/Growth.

---

## The SCOPE you're pushing for (beyond the desktop skeleton)

DesktopState today = active app + window. You want eLo to perceive and act on the **real digital
world** and use it to genuinely help + self-improve:
- **Perceive:** open Chrome tabs · browser history · open documents · files · calendar · company state.
- **Link:** history ↔ open tabs ↔ documents ↔ company details — so "what were we doing?" is answered
  from the actual environment, not a guess.
- **Act (capability registry, made real):** open a tab, read a doc, search files, query company status
  ("ask eLo how's the company" — WO-048), execute — each gated by faculty health + Embodied Truth.
- **Improve:** capability learning turns repeated friction into WOs and preference.

This is a **World Model + Perception scope-expansion** (Vol XII/XV) + a **real Capability layer**, not
new cognition. The Cognitive Self Model is the frame; this fills it with the real world.

---

## How it INTERLINKS (one continuous mind)
```
Perception (XII) + Desktop/App sensors ─┐
                                        ├─► LiveWorldState (XV, exists) ─┐
Body Schema (Embodied Self, WO-049) ────┘                               │
Self-Model (self/, exists) ─────────────────────────────────────────────┤
Faculty Health (WO-042) + Capability Registry (exists) ─────────────────┤
                                                                        ▼
                              COGNITIVE SELF MODEL  (the assembly — net-new)
                                                                        │
                              Executive reads it EVERY cycle ───────────┤
                                                                        ▼
        Embodied Cognition: decide from self+world+capability  →  Embodied Truth: act → Unity ACK →
        belief → speak.   Reflection/Growth (VI Ch.6) → Capability Learning → self-improvement.
```
Ties directly to: One Brain · ADR-Exec-001 (Verified Speech) · ADR-Exec-002 (Single Cognitive Truth) ·
Vol XII Perception · Vol XV World Model · Vol XIII Presence→Embodied Spatial Intelligence · Spatial
Faculty · Capability Registry · Reflection/Growth. It is the **runtime embodiment of One Brain**.

---

## Sequencing (grounded, not blue-sky)
- **NOW (already the sprint):** the ACK loop + command-turn fix (WO-040/041/032) IS Embodied Truth's
  first step. The Builder is on it. No new work needed to *start*.
- **Post-Presentable:** assemble the Cognitive Self Model (wire the existing parts) + Body Schema +
  memory-recall confidence + movement queue.
- **Then scope-expansion:** desktop/app perception (tabs, history, docs, company) + real capability
  actions + capability learning.
- **Home:** Vol XIII evolution (Presence → Embodied Spatial Intelligence) + the Spatial/Embodied-Self
  Faculty chapter. Authored when scheduled — NOT now.

**Bottom line:** you're not missing the architecture. You're missing the *assembly* of what you already
built, plus the ACK loop and the scope-expansion into the real digital world. That is a far smaller,
more tractable leap than "build an embodied mind" — and it's the exact bridge from truthful *speech*
to truthful *being*.

---
## Chief Architect review — the "cooperation" inputs (2026-08-05, reconciled)

CA's key meta-point (accepted): the board has moved from *making systems EXIST* to *making systems
COOPERATE*. The next milestone is the Executive assembling ONE verified state from self · world ·
capability · health · **affordances · intentions** before it speaks or moves. That is exactly this
document's thesis ("the parts exist — unassembled"). Four concepts the CA added, reconciled:

- **AFFORDANCES** — perceive opportunity, not geometry ("that window affords climbing"). **Already
  canon** (WO-049 surface semantics: edge=ledge, gap=jump). ELEVATE to a first-class field on the
  World Model: `window → affordances{stand·run·jump·wall-run·climb·hide·peek·enter·exit}`. Then the
  Executive searches POSSIBILITIES, never animations. Governed by the new principle *Affordance Before
  Action*.
- **INTENTIONS ≠ Intent.** Intent = external ("David asked me to sit"). Intention = internal drive
  ("I'd like to explore / rest / observe / meditate / watch / return home"). An **Intent Queue** with
  BOTH streams; the Executive chooses between them. Home = **Agency Engine (Vol V Ch.10)** + the
  Cognitive Self Model. This is what makes eLo self-directed without being intrusive (D-PRESENCE bounds it).
- **CURIOSITY LOOP** — novelty → internal-state change → exploration ("unknown window → curiosity up →
  walk over → learn"). **Parts exist:** the self-model ALREADY tracks a `curiosity` field
  (`elo_self_state.json`); wire it to World-State novelty → Intention. Not new cognition — a wire.
- **SPATIAL MEMORY** — "Claude is on the right today." Windows have *usual* positions; eLo notices
  deviations. Extends **Memory** + LiveWorldState (learn typical layout → flag change). Surprisingly
  human, cheap to add on the existing memory.

**Cognitive Self Model — full input set (the assembly):**
`SELF (self-model) · BODY (schema) · WORLD (LiveWorldState) · AFFORDANCES · CAPABILITIES (registry) ·
FACULTY HEALTH · INTENTIONS (external + internal) · SYSTEM`. The Executive reads this every cycle,
then decides (Embodied Cognition) and acts→confirms→speaks (Embodied Truth). Affordances + Intentions
are the two the CA added; both fit the existing frame — no new faculty, more assembly + two small wires.

---
## Chief Architect additions (2026-08-05) — reconciled + THE MOMENT + design closure

CA's closing truth (accepted, and it ends the ideation): *the challenge is not more faculties — it is
that every decision comes from ONE continuously-updated cognitive state.* That is this document.
Reconciling the 9:

- **Situated Cognition** → NEW principle (constitution). Completes the Embodied trio: reason relative
  to environment + capability + relationship, never in isolation.
- **Executive receives a compiled snapshot, doesn't search faculties** → this IS the Cognitive Self
  Model — its defining property is **push, not pull**: state is pre-assembled each cycle; the Executive
  READS "sit=available · ledge=true · movement=online" and decides, never queries mid-decision.
- **Internal Narrative** → NEW (small): an internal thought stream ("that looks climbable", "David seems
  focused") that mostly never becomes speech. Feeds the Executive; ties "the Executive grows quieter".
- **Attention** → ALREADY EXISTS (Vol VI Working Memory & Attention). Elevate to a live snapshot field
  (things compete: David · window · Spotify · conversation · movement).
- **Self-confidence (per-faculty: movement 0.96 · memory 0.48)** → ALREADY the pattern (WO-042 health +
  LiveWorldState confidence). Expose per-faculty confidence in the snapshot → "memory 0.48 → ask, don't claim."
- **Drives (curiosity/comfort/rest/play/observe/relationship/explore)** → = INTENTIONS (already added →
  Agency Engine). Affordances satisfy drives. Same climb, different internal reason. Reconciled.
- **Presence is a cognitive state, not an animation** → NEW principle (constitution).
- **The MOMENT** → the canonical NAME for the assembled state. eLo lives in *moments*, not turns: a
  Moment = {time · environment · relationship · attention · memory · goals · health · mood · capability
  · affordances · intentions}. The Executive reasons over the Moment; then the next Moment begins.
  **The "Moment" and the "Cognitive Self Model / Cognitive Snapshot" are the same object** — Moment is
  its human name, and it reframes the runtime from request→response to continuous cognition.
- **Desktop as home (Chrome=building · VS Code=workshop · Obsidian=library)** → = the Imagination
  Overlay + window-personalities ALREADY in WO-049. "I'm going to the workshop" not "opening VS Code."

## ⛔ DESIGN CLOSURE — Embodied Cognition is now fully specified
The target is complete: the Executive assembles ONE Moment (self · body · world · affordances ·
capabilities · faculty-health/confidence · intentions/drives · attention · memory) each cycle, decides
(Embodied/Situated Cognition), acts → body confirms → believes → speaks (Embodied Truth). Further ideas
are refinements of the Moment, not new architecture, and should not extend this doc. **The next act is
BUILDING the assembly, not describing it** — and its first step (the sit ACK loop) is already shipping.
