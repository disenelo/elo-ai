# Design Brief — "A Quantum Brain that moves like a brain / a computer"
### For the Planning Assistants (Gemini · ChatGPT). Output → intake → Architect canonicalises into the spec.

**From:** David (via Architect) · **2026-07-27** · **Target canon:** `ONE_BRAIN_QUANTUM_SPEC.md` +
`docs/architecture/20_one_brain_visualiser.md`.

## Status: the motion spec already exists and ChatGPT has it
The authoritative **One Brain motion spec** = the **"Motion model — how it should move"** section of
`DISENELO-eLoDesktopBuddy/ONE_BRAIN_QUANTUM_SPEC.md` (+ `HANDOVER_one_brain.md`). **David has already
handed this to ChatGPT.** So this brief does **not** re-spec motion — it does two supporting things:
1. gives **Gemini a second, complementary angle** (the "computer/data-flow" reading) so we get two
   perspectives, not one;
2. sets the **return path**: both assistants' outputs land in `_intake/`; the Architect merges them
   into `ONE_BRAIN_QUANTUM_SPEC.md` **v-next** and relays **one-change-at-a-time** WOs to the visual agent.

## The ask (framing for both)
Sharpen **how the One Brain moves** so it reads as **both** a living **brain** (organic, neural, fluid)
**and** a **computer** (data-flowing, computational, structured) — *within* the existing Motion model,
not replacing it.

## What already exists (don't reinvent — refine)
The One Brain is a 2D **quantum-turbulence fluid of light**. Nine cognitive systems = **quantized
vortices**: `Intent` (core), `Attention · Memory · Emotion` (mid), `Motion · Body · Vision ·
Expression · Voice` (outer). Live data (`brain_state.json`: per-vortex `energy·valence·active·label`
+ `cluster_energy`, `IsSpeaking`) drives it — it is a **pure render of eLo's cognition, not
decoration**. Built through v1→v4.5:
- **Onsager clustering:** calm = dispersed vortex-gas; rising `cluster_energy` → like-sign vortices
  migrate into clumps, condense inward, brighten, swirl faster.
- **Anchored fluid (v3):** nodes tethered with gentle sine drift — as a background widget it MUST
  NOT dart around; the turbulence moves through the **light** (filament width, scroll, brightness).
- **Motes** swirl around each vortex (bulked-brain cloud); **lightning links** flow Intent→mid→outer;
  **synapses fire outward from active systems**; **voice** = an audio-wave ring while speaking.
- **Colour** = eLo's MoodPalette only (Hawkins/Abraham-Hicks valence scale) — never hardcoded.
- Visual-language reference: **JARVIS / Ultron** holographic mind (web-sphere, trails) — not the colours.

## Hard constraints (any design MUST honour)
1. **Pure render of `brain_state.json`** — every motion maps to a real signal (energy → clustering/
   brightness/swirl; valence → clump/direction; `cluster_energy` → global condensation + firing rate;
   `IsSpeaking` → voice wave). No motion that isn't driven by state.
2. **Background-safe** — it lives behind the desktop; calm = quiet, non-distracting. No darting.
3. **Colours from MoodPalette** — full continuous palette (this is the rich-palette consumer, D-J).
4. **Click-to-pin** stays; labels are **click-only** (no hover/zoom clutter — pending refinement).
5. **Performance-pooled** (motes/beads/synapses capped).

## The two angles (one per assistant)
- **Gemini — the "computer" motion language.** How does it move so it reads as *computation*? Data
  packets routing along links, processing pulses/clock-like rhythms, structured/geodesic web forming
  and resolving, signal propagation core↔systems, "thinking = visible traffic." How does load/att-
  ention look computational?
- **ChatGPT — the "brain / neural" motion language.** How does it move so it reads as a *living
  mind*? Synaptic firing cascades, neural oscillation/breathing, the quantum-turbulence living-cell
  feel, coherence vs dispersal as mood, how emotion ripples through the field.

Each: propose the motion vocabulary, how it ties to the existing signals, and 2–3 concrete
behaviours (with the trigger signal). Say what to **keep**, **change**, or **add** vs the v4.5 state.

## Deliverable format (so I can canonicalise)
```
### <behaviour name>
Reads as:   brain | computer | both
Trigger:    <which brain_state.json signal>
Motion:     <what moves, how>
Keep/Change/Add vs v4.5:
Risk:       <perf / distraction / breaks a constraint?>
```

## Build discipline (David's rule after the last batch)
Once I synthesise both into a v-next motion spec: implement **one change at a time, exactly to spec,
build (0 compile errors), then wait** for review. No multi-change batches. Presence baseline is clean
at `466a4e1`.

---

## Architect's starting-point synthesis (react to this)
My first cut at unifying "brain + computer" — a **three-layer motion model**, each layer one of the
two readings, all driven by state:
1. **Field layer (brain/fluid):** the quantum-turbulence condensate — clustering/dispersal + swirl =
   eLo's overall coherence (`cluster_energy`). Slow, organic, breathing. *The mind's mood.*
2. **Signal layer (computer/data):** discrete pulses travelling the links — routed **from the active
   system outward/inward**, rate ∝ that system's `energy` + global `cluster_energy`. Crisp, directional,
   rhythmic. *The mind computing.* (This is where "moves like a computer" lives.)
3. **Node layer (both):** each vortex breathes (neural) but fires discrete synapse comets (computational)
   when its system activates. Motes = organic; comets = digital. The two textures coexisting is the
   "brain **and** computer" feel.
Idle = field barely breathing, sparse signals (calm). Engaged = field clusters + signal traffic surges.
That single axis (`cluster_energy`/`energy`) scales both the organic and the computational at once.

*Gemini + ChatGPT: sharpen or challenge this. Their returns land in `_intake/`; the Architect merges
into `ONE_BRAIN_QUANTUM_SPEC.md` (v-next) + relays buildable one-change WOs to the incoming visual agent.*
