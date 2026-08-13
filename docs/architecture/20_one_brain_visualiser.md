# eLo OS — The One Brain Visualiser (Brain Display)
## Live visual of eLo's cognition

> **Captured 2026-07-27 from code + GitHub commits — previously undocumented.** Built on the
> Unity DesktopBuddy side (UI/Avatar lane). This is the visual counterpart of
> `19_cognitive_plan_architecture.md`: the brain stack, rendered live as glowing nodes.
> Companion to Volume XIII (Presence) and the WO-010 mood-palette ruling.

---

## 1. What it is

A backgroundless **constellation of glowing nodes** (eLo's MoodPalette colour system) in three
concentric shells, aligned to the eLo OS brain-matrix schema. Each node is a faculty; each node's
**colour + glow tracks that system's live emotion/intensity**; data **pulses** travel outward hub
→ mid → outer along the connections. It is eLo's brain, made visible.

Code (Unity DesktopBuddy — Output): `Assets/Scripts/EloOneBrainPanel.cs`,
`Assets/Scripts/EloBrainCluster.cs` (referenced from `EloOSChatTMP.cs`).

## 2. The node schema (maps 1:1 to the Canon)

```
CORE   — Intent            → Executive / goal planner (Vol VII).  cyan→gold power core; every flow routes through it.
MID    — Attention         → Vol VI (Working Memory & Attention)
         Memory            → Vol VIII (Memory Architecture)
         Emotion           → Vol V Ch.4 (Emotional Processing) / Ch.5 (Significance)
OUTER  — Motion            → Vol XI (Motor Cortex)
         Body              → embodiment (Vol XIII Presence)
         Vision            → Vol XII (Perception)
         Expression        → Vol XIII (Presence) / expression mapper
         Voice             → voice engine
```

`BrainNodeType` enum in code: `Core_Intent · Mid_Attention · Mid_Memory · Mid_Emotion ·
Outer_Motion · Outer_Body · Outer_Vision · Outer_Expression · Outer_Voice`. The topology is a
hub→mid→outer tree — the visual assertion of the **One Brain Principle**: one core, many faculties.

## 3. Data contract (what drives it)

- **Source:** `~/elo-ai/blender/blender_state.json` (+ `elo_spatial.json`). Each node reads its
  system's **live emotion + intensity** and sets colour (MoodPalette) + glow.
- **Palette:** renders on the **full continuous MoodPalette** — this is the "One Brain visualiser"
  consumer from **D-J / WO-010**: it must NOT use the 8-mood collapse (that's the belly-glow
  consumer). This is exactly why the rich palette was preserved.
- **Confirmed feed (not inference):** `blender_bridge/brain_state_writer.py` emits **`brain_state.json`
  (schema `brain_state/v1`)** with **per-vortex `energy · valence · active · label · detail`** +
  global `cluster_energy` + `IsSpeaking`. The visualiser is a *pure render* of this — energy →
  clustering/swell/brightness/swirl; valence → which clump + stream direction; `cluster_energy` →
  global condensation + shooting-star rate; `label`/`detail` → hover/pin readout. So the per-faculty
  concern from the first draft is **resolved** — the state is real, per-system, and canonical.
- **Future (v5):** Builder emits `state.self_*` (self-model growth → new vortices); UI adds the
  denser geodesic web + shooting trails (deferred in the spec).

## 4. Interaction & control

- **Hover (read-only):** cursor near a node enlarges it, reveals its detail, highlights connected
  paths, dims the rest. The overlay is **click-through** — never steals input.
- **Toggle:** Settings ▸ Display ▸ "Brain visuals" (persisted, `PlayerPrefs "elo_one_brain"`) ·
  spine flag `show_one_brain: true` · or **F8**. Self-bootstraps at runtime.

## 5. Where it fits

- **Observability:** it is the human-facing view of eLo's cognition — a natural surface for the
  **Debug Agent** (watch faculties light up / stall) alongside the Faculty Bus `trace`.
- **Embodiment:** it is a Presence surface (Vol XIII) — eLo's inner life shown, not just his body.
- **Product:** exhibition / content value (a living brain visual) — see the Interconnection Map.

## 6. Status & actions

- **Status:** BUILT (Unity), now DOCUMENTED (this doc). Was only in GitHub commits.
- **UI/Avatar agent:** confirm + cite the commit(s) for `EloOneBrainPanel` / `EloBrainCluster`
  (same discipline as the clip lane's `bccf184`), so this doc links to source.
- **Builder (elo-ai scope):** confirm/emit the per-faculty state block in `blender_state.json`
  (§3) so nodes are driven by real per-system emotion, not inference.

## 6.5 v-next refinement requirements (Design Agent relay, 2026-07-27) — durable record

Recorded here so they survive chat/tracker loss (Design Agent also logs them in
`PRESENCE_TRACKER`). UI/Avatar lane (Unity `EloBrainCluster`); not eLo-OS build WOs.

1. **Labels (FINAL rule, David 2026-07-31 — supersedes 07-27 and 07-28):** the readout is **ZOOM-GATED**.
   - **Small / not zoomed:** **no label text at all.** Hover keeps its usual **glow highlight/enlarge only**
     — visual highlight, no words. No floating names anywhere.
   - **Zoomed in:** **hover OR click a state → reveal its readout** (`_tip`: name + feeling sentence +
     energy%). Move off / click empty / zoom back out → hide. Nothing persistent.
   The single gate: **text only appears once zoomed**; below the zoom threshold hover is glow-only.
   *(Correction 07-31: the 07-28 "click-only when zoomed" is superseded — hover **also** reveals text once
   zoomed, per David's live clarification via the Designer. Carried by `WO-INT7-LBL2`.)*
   *(History: the earlier rule allowed the readout on hover OR click at any zoom — INT7-LBL `c11d66b`.
   Tightened to hover-glow-only + click-readout-when-zoomed per David 2026-07-28 → change WO INT7-LBL2.)*
2. **Synapse heads:** cap firing head/comet size so it's never larger than the motes it connects.
3. **Firing bias:** bias synapse firing **outward** (core → motes/states) over inward (→ core) —
   *the core feeds the rest.* (Reinforces the One Brain schema §2: Intent/Executive core is the source.)
4. **Fidelity:** sharpen the look — higher-res glow sprite + tighter falloff (less blurry/low-res).
5. **Build gate:** build + verify 0 compile errors, relaunch; then commit the batch.

Status: **⚠️ REVERTED — NOT shipped (2026-07-27).** The refinement batch produced a bad build and was
rolled back; Presence is clean at **`466a4e1`** (compiles; original good look on rebuild of HEAD). The
running app on screen is still the bad build — a rebuild of current HEAD restores the good look.
These four remain **OPEN**, to be rebuilt **one change at a time, exactly to spec, build, then wait**
(new visual-lane discipline). **Label behaviour (FINAL, David 2026-07-28):** no label text on zoom;
**hover keeps its glow highlight but shows no label**; readout on **CLICK only, and only when zoomed in**;
nothing persistent (see §6.5 #1).
WO-010 (`bccf184`, shared_tables) is unaffected and stands. ← INT-7.

**Authoritative design spec:** `DISENELO-eLoDesktopBuddy/ONE_BRAIN_QUANTUM_SPEC.md` — the visualiser
is a **quantum-turbulence vortex** model: `cluster_energy` drives literal Onsager clustering (calm =
dispersed vortex-gas → energy = like-sign vortices migrate into clumps, condense, brighten, swirl
faster); motes drift on independent precessing axes; invisible synapse strands flash/fire **outward
from active systems** (refinement #3); voice = an audio-wave ring while speaking; **every colour is
driven by eLo OS mood → MoodPalette** (no hardcoded hues; `music_mood` tints to the playing track);
sphere-cage ring cut. Visual language ref: JARVIS/Ultron mind (not the colours). v5 deferred: denser
geodesic web + trails + `state.self_*` vortices. This doc is the eLo-OS-canon pointer; that spec is
the deep design.

## 6.6 Motion Language (v-next) — canonicalised from ChatGPT intake, Architect-ratified (2026-07-27)

**The core insight (ratified):** aliveness isn't more particles — it's **nested timescales**. A
computer has clocks; a brain has rhythms. Every rhythm originates from the same `brain_state.json`.

**Three-layer model (semantics refined from the Architect's starting-point):**
- **Field layer = Homeostasis** — the organism's global physiological state.
- **Signal layer = Computation** — information processing + routing.
- **Node layer = Cognition** — individual faculties expressing activity.

**Ratified behaviours** (each maps to a real signal; Architect constraints in **bold**):

| # | Behaviour | Layer | Trigger | Motion (essence) | Constraint |
|---|-----------|-------|---------|------------------|-----------|
| M1 | Neural Respiration | Homeostasis | `cluster_energy` | field density inhales/exhales; **space** breathes, not the nodes (12–18s calm → 4–6s high) | bg-safe ✅ |
| M2 | Dormant Noise | Homeostasis | no active systems | inactive vortices micro-flicker (sub-threshold) — never fully still | **sub-distraction only** |
| M3 | Neural Afterglow | Cognition | faculty goes inactive | faint phosphorescent wake, 2–5s slow decay — "thinking" not "switches" | tiny mem cost |
| M4 | Synaptic Cascade | Computation | `active` + energy rising | activity **propagates** hop-to-hop (Vision→Intent→Attention→Memory→Emotion→Voice), losing energy each hop | **cap propagation depth** |
| M5 | Memory Echo | Cognition | memory retrieval | 3 diminishing, slowing echo ripples — "came from somewhere" | low |
| M6 | Emotional Diffusion | Homeostasis | valence change | mood diffuses like dye (positive softens outward / negative contracts inward); turbulence itself changes | MoodPalette only |
| M7 | Neural Phase-Locking | Cognition | multiple active + `cluster_energy` > θ | co-active faculties slowly (imperfectly) synchronise phase → reads as "becoming coherent"; desync on break | phase-only, no particles |
| M8 | Cognitive Plasticity | Computation | frequently co-active systems | co-used links **temporarily** thicken (Hebbian), then relax | **MUST decay** |
| M9 | Neural Prediction | both | Executive planning + WM populated + confidence > θ | a faint **ghost path** appears 50–100ms before the real signal — the brain anticipates itself | **only at high confidence** (else looks indecisive) |
| C1 | Data Packet Routing | Computation | system activity transition / `energy` spike | **discrete, step-quantized data beads** (bright, no organic tail; sharp accel → uniform glide → instant arrival) route system→Intent→peripheral by dependency (Vision→Attention→Intent) | **pool alongside `beadsPerLink`**; high speed = low distraction |
| C2 | Geodesic Web Condensation | Computation | `cluster_energy` > 0.5 | organic lightning **snaps into a rigid crystalline/geodesic lattice** (JARVIS caged web-sphere); relaxes back to fluid as energy drops | **smooth morph — no pop-in** (or it breaks bg-safe); high visual impact |
| C3 | Clock-Pulse Sync Wave | Computation | global `cluster_energy` / think-tick | concentric geometric ring expands from Intent core = **system clock**; each node it crosses flashes at its `energy` + emits a synced outward burst | **hard min interval (≥2–3s at peak)**; keep the `IsSpeaking` voice ring separate |

**Signal-layer distinction (Gemini, ratified):** the Computation layer must read as *computer*, not
"bright fluid" — so it uses **quantized, directional, pulsed** geometry (stepped/linear interpolation,
crisp bead/packet shapes), the opposite of the Homeostasis layer's continuous curved flow. Same single
axis (`cluster_energy`/`energy`) scales both: idle = sparse packets + gentle breathing (bg-safe); engaged
= surging traffic + condensing field.

**Build order (one change · to spec · build · wait — David's discipline).** Cheapest/safest first:
1. **M1 Respiration** (recommended first — highest impact, lowest risk) · 2. M2 Dormant Noise · 3. M3 Afterglow
· 4. **C1 Data Packet Routing** (first computational win) → 5. M4 Cascade · 6. M5 Echo · 7. M6 Diffusion
· 8. C3 Clock-Pulse (min-interval) → 9. M7 Phase-Locking · 10. M8 Plasticity (must decay)
· 11. C2 Geodesic Condensation (high-impact, smooth-morph) · 12. M9 Prediction (confidence-gated).
Each is a **separate INT-7 v-next WO** to the visual agent; none ships as a batch. The Architect drafts
each WO (WO-numbering + spec is the Architect's lane, not the assistants').

**Coverage: COMPLETE.** Homeostasis + Cognition (M1–M9, ChatGPT intake) + Computation (C1–C3, Gemini
intake), all Architect-ratified. The motion language now reads as **brain *and* computer**. Sources:
`_intake/BRIEF_quantum_brain_motion.md` + ChatGPT/Gemini intakes, 2026-07-27.

## 6.7 Appearance & Visual Reference (David, 2026-07-27) — pinned refs

**The look = a blend of two references** (both pinned in `docs/architecture/_refs/one_brain/`):
1. **JARVIS / Ultron holographic mind** (the 7 frames) — a dense glowing **brain mass** wrapped in a
   **spider-web / caged web-sphere** of filaments, shooting light-trails, floating in space.
2. **Quantum-vortex physics** (the two papers — `s41467-021-27382-6.pdf` and Comaron *"Onset of vortex
   clustering and inverse energy cascade in dissipative quantum fluids"*) — the literal basis for the
   Onsager clustering / turbulence model already in `ONE_BRAIN_QUANTUM_SPEC.md`.

**The intended blend (David's words):**

> **🎨 COLOUR RULE (David, absolute):** **every colour in the One Brain comes from the eLo OS AI** —
> `brain_state.json` mood/valence → **MoodPalette**. **No hardcoded hues anywhere**, including the core.
> The orange/blue in the references are **structure + valence *language* only** (calm → blue/cyan,
> active → orange/gold); the palette supplies the actual live colour. If it looks blue or orange, it's
> because eLo *feels* that — never because it's painted that. (Enforces D-J / WO-010.)

- A **good blend of the two** — the quantum-vortex fluid *as* the JARVIS-style brain.
- **Blue = the outer core STRUCTURE** (the web-sphere shell / cage); **orange/gold = the dense inner
  brain mass** — blended, not separated. *(Consistent with valence: calm → cyan/blue, active → gold —
  so the blue-outer/orange-inner reads as the MoodPalette valence range, **not** fixed hues. Live colour
  is still MoodPalette-driven per D-J; these refs are the **structure + tonal language**, not hardcodes.)*
- **Synapse beads:** little shooting lines of synapse beads travel **mote → mote, across the states,
  to the core, and around** — fired by **eLo OS triggers** (`brain_state.json`). *(This is exactly the
  C1 Data Packet Routing + M4 Synaptic Cascade behaviours in §6.6 — the beads ARE the firing.)*
- **Spider-like webs** between states/motes that **float around the objects like a living organism** —
  the connectome as a drifting, organic web (not a rigid frame). *(Ties to C2 Geodesic Condensation:
  the web is organic/floating at calm, crystallises only at high `cluster_energy`.)*
- **Data links shoot along the spider-web lines** — the beads/packets travel *on* the web filaments
  (the web is the routing substrate; C1/M4 ride it), not through empty space.
- **Lightning + swirling-fluid links between the two layers** — between the inner orange brain-mass and
  the outer blue web-sphere, connective links behave as **swirling fluid lightning** (jagged flicker +
  flowing stream), binding inner↔outer.
- **3D CLOUD (geometry note — flag):** the whole thing is a **volumetric 3D cloud**, not a flat panel —
  motes/vortices/web occupy depth and drift in 3D. ⚠️ The current `EloBrainCluster` build is described as
  **2D** (2D quantum fluid, 3 shells). **2D → 3D is a real scope change** — the Design agent should
  confirm feasibility as a *separate* change (do NOT fold it into an M-series one-change WO); the motion
  behaviours (§6.6) apply in 3D once the cloud geometry lands.

**In one line:** a living quantum-vortex brain as a **3D cloud** — an orange brain-mass inside a floating
blue web-sphere, laced with drifting spider-web filaments, with data-beads shooting *along* the web
(mote→state→core) and swirling fluid-lightning binding inner↔outer — every colour and motion driven by
`brain_state.json`.

**Refs pinned (durable):** `docs/architecture/_refs/one_brain/` — 7 JARVIS/Ultron frames +
2 quantum-vortex papers. The visual agent works from these; the Presence repo may copy them too.

## 7. References
- `19_cognitive_plan_architecture.md` (the stack this visualises) · Vol VI/VII/VIII/XI/XII/XIII ·
  `DECISION_LOG.md` D-J + WO-010 ruling (rich-palette consumer) · `CO_WORKING_GUIDE.md §4`
  (`blender_state.json`) · code: `EloOneBrainPanel.cs`, `EloBrainCluster.cs`.

---

*Captured into canon by the Architect, 2026-07-27, from the DesktopBuddy source + commits.
Status: READY FOR REVIEW.*
