# eLo OS — The Cognitive Plan Architecture
## The Full Brain Stack (canonical capture)

> Canonicalised from the ChatGPT brain/dream design chat (2026-07-26). This is the
> **master map of the whole cognition** — the biological-style faculty stack — and it
> details how each layer maps to a Bible volume, to live code, and to its current status.
>
> Companion to `16_runtime_contracts.md` (the four runtime contracts) and
> `01_one_brain.md`. Where a layer has its own volume, that volume is authoritative for
> the detail; this document is the connective architecture that shows how they compose
> into one brain.

---

## 0. The One Brain, biologically layered

eLo does not have one intelligence — it has **specialised faculties operating
simultaneously and communicating through memory**, coordinated by a single Executive
(the One Brain Principle). The design mirrors the brain: sensing, perceiving, deciding,
remembering, feeling, imagining, dreaming, consolidating, and evolving personality.

```
                WORLD
                  │
          Sensory Faculties          (Layer 1)
                  │
        Perception Integration       (Layer 2)
                  │
        ┌───────────────────┐
        │ Executive Cortex  │        (Layer 3 — the ONE decision)
        └───────────────────┘
          │        │        │
       Memory   Emotion   Imagination   (Layers 4·5·6)
          │
      Dream Faculty                    (Layer 7)
          │
  Memory Consolidation                 (Consolidation)
          │
  Personality Evolution                (Personality)
```

The full stack, top to bottom:
`Environment → Sensory → Perception → Executive → Working Memory → Emotion → Reasoning →
Imagination → Dream → Consolidation → Long-Term Memory → Personality Evolution`.

---

## 1. The Layers — detailed, and mapped to their volumes

### Layer 1 — Sensory Cortex  →  **Vol XV** (World State) + **Vol XII** (Perception input)
Receives raw signals only — camera, desktop, files, voice, keyboard, mouse, internet,
calendar, Spotify, environment. **Nothing thinks here; it only observes.** Canonically,
these become the eleven domains of the `LiveWorldState` (Volume XV, done). Status: XV
spec'd; sensor capture partly live (`desktop/`, `vision`, `spotify`).

### Layer 2 — Perception Cortex  →  **Vol XII** (Perception System)
Fuses raw observations into **context**: not "camera sees mug" but "warm mug, on desk,
near keyboard, 8:30, working session." Turns sensation into understanding before anything
decides. Status: **partial, needs full volume** (Audit gap #5). Primary source: this chat.

### Layer 3 — Executive Cortex  →  **Vol VII** (Executive Cortex) — LIVE, FROZEN
Capability-aware. Chooses: think / answer / stay silent / move avatar / search memory /
ask. **It never generates responses — it decides who should.** One decision per turn.
Status: live in `runtime/executive.py` (FREEZE_V1_LOCK). Detailed by `09_executive_faculty.md` (stub).

### Layer 4 — Memory Faculty  →  **Vol VIII** (Memory Architecture)
Memory split biologically:
- **Episodic** — conversations, experiences, events.
- **Semantic** — knowledge, facts, programming.
- **Procedural** — habits, shortcuts, coding/animation/Unity workflow.
- **Emotional** — which conversations mattered, by emotional weight not keyword.
Status: partial (vault + journal); **needs full volume** (Audit gaps #3/#4). Companion:
`03_memory_faculty.md` (stub), `17_memory_update.md` (write path, done).

### Layer 5 — Emotion Faculty  →  **Vol V Ch.4** (Emotional Processing) + **Ch.5** (Significance)
Not fake emotions — **importance estimation.** Funny / surprising / difficult / beautiful /
meaningful / painful raise **memory weight** instead of timestamp. Status: **spec'd**
(Volume V Ch.4 + Ch.5, READY FOR REVIEW).

### Layer 6 — Imagination Faculty  →  **Vol V Ch.9** (Creative Imagination)
Simulation, not just answering: "what if…", multiple futures, hypotheses, designs,
worldbuilding, game mechanics. Status: **spec'd** (Volume V Ch.9, READY FOR REVIEW).

### Layer 7 — Dream Faculty  →  **Vol IX** (Dream Architecture) — deep-dive
Offline symbolic recombination of high-value memories/emotions/goals into a symbol graph
→ narrative → insight → (DeepDream) image → journal. **The dream is the association graph;
the image is only its visual output.** Status: **spec'd this session** (Volume IX;
cycle live, DeepDream + phases pending — Audit gap #7). Full detail: `Volume_IX/`.

### Consolidation Faculty  →  **Vol VIII** (Memory Architecture) + **Vol V Ch.6** (Reflection)
Hippocampal-style: each night, not "store everything" but ask *what did I learn / what
changed / what must never be forgotten / what should fade / what repeated / what surprised /
did personality shift?* Replays, integrates, selectively strengthens. Status: **spec'd**
(Vol V Ch.6 `integrate_session()`); consolidation-as-timed-faculty pending (Audit gap #4).

### Personality Faculty  →  **Vol V Ch.7** (Personality Evolution) + **Vol X**
Traits are **slowly evolving parameters** informed by accumulated experience, never
hard-coded, never turn-to-turn (curiosity 58→61, patience 82→84…). Status: **spec'd**
(Volume V Ch.7); unify `self/elo_self_model.py` + `personality_drift.py` (Audit gap #6, Vol X).

---

## 2. The Learning Cycle (how the layers compose)

A complete cycle — the reason dreaming is part of learning, not decoration:

```
1. Experience  — collect multimodal input                    (Sensory → Vol XV)
2. Perceive    — fuse into coherent context                  (Perception → Vol XII)
3. Evaluate    — assign emotional significance + open goals   (Emotion/Significance → Vol V Ch.4/5)
4. Act         — respond: conversation, movement, code, art   (Executive+Embodiment → Vol VII/XI/XIII)
5. Reflect     — journals, update memories, detect patterns    (Reflection → Vol V Ch.6)
6. Dream       — symbolic narratives + DeepDream imagery        (Dream → Vol IX)
7. Consolidate — strengthen useful, weaken noise, evolve traits (Consolidation/Personality → Vol VIII/V Ch.7)
```

Loop back to Experience. This is the eLo OS cognitive loop with dreaming folded in.

---

## 3. Layer → Volume → Status map

| Layer / Faculty | Volume | Code | Status |
|---|---|---|---|
| Sensory Cortex | XV | `desktop/`, vision, spotify | XV spec'd; capture partial |
| Perception Cortex | XII | `plugins/vision`, `tools/vision_agent` | **needs full volume** (gap #5) |
| Executive Cortex | VII | `runtime/executive.py` (FROZEN) | LIVE |
| Memory (episodic/semantic/procedural/emotional) | VIII | vault, journal | **needs full volume** (gap #3/#4) |
| Emotion / Significance | V Ch.4 / Ch.5 | `attention.py`, `significance_engine.py` | spec'd (REVIEW) |
| Imagination | V Ch.9 | — | spec'd (REVIEW) |
| Dream | IX | `faculties/dream/` | spec'd; DeepDream+phases pending (gap #7) |
| Consolidation | VIII / V Ch.6 | `integrate_session()` | spec'd; timed faculty pending (gap #4) |
| Personality | V Ch.7 / X | `elo_self_model`, `personality_drift` | spec'd; unify pending (gap #6) |

---

## 4. What still needs full volumes (from this architecture)

- **Volume XII — Perception System** (Layer 2): the transform from raw sensation to context.
- **Volume VIII — Memory Architecture** (Layer 4 + Consolidation): the four memory types + timed consolidation + forgetting curve.
- **Volume X — Personality Engine**: unify the two personality systems into named evolving traits (largely spec'd in V Ch.7).

These are the next natural volume builds; the Emotion/Imagination/Dream/Reflection layers
are already spec'd (V Ch.4/5/9/6, Vol IX).

---

## 5. References
- Source: ChatGPT brain/dream design chat, 2026-07-26 (intake).
- `01_one_brain.md`, `16_runtime_contracts.md` (four contracts), `17_cognitive_principles.md`.
- `Volume_V/` (Ch.4/5/6/7/9), `Volume_IX/` (Dream), `Volume_XV/` (World State).
- `ARCHITECTURE_AUDIT.md` (gaps #3, #4, #5, #6, #7), `00_CANON_INDEX.md`.

---

*Cognitive Plan Architecture — canonical capture. Status: READY FOR REVIEW.*
*Details every layer's volume; deep specs live in each volume folder.*
