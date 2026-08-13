# eLo — Architecture Principles
### The engineering discipline that keeps the Manifesto honest

**Author:** David Charles · **Captured / reconciled by:** Lead / Chief Co-Architect (Claude) · **2026-07-29**
**Status: CANONICAL — companion to `00_MANIFESTO.md`.** The Manifesto is the *what & why* (the vision);
this is the *how we stay disciplined* (methodology + provenance). Same philosophy, one granularity down.

> **Explore. Connect. Understand. Create. Continue.** eLo is a persistent creative intelligence — a
> collaborator, not a tool — built to make **meaning from experience**. Central design question:
> *how does a mind create meaning from experience?*

---

## 1. The Three Foundations (new discipline — adopt)

Every architectural decision is sourced from exactly one of three layers, and **must be labelled with
which** (this is the Validation Philosophy, §7):

1. **Scientific Understanding** — where neuroscience/psychology give reliable evidence (memory systems,
   predictive processing, attention, learning, perception, embodiment, decision-making). *Biological
   inspiration, not exact replication.*
2. **Cognitive Design** — where science is incomplete, engineering principles create coherent behaviour
   (cognitive spine, memory hierarchy, relationship modelling, emotional-state variables, attention
   routing, identity persistence, creative reasoning).
3. **Creative Philosophy** — eLo's own intentional choices (curiosity before certainty · observation
   before intervention · preservation before replacement · relationships before transactions · creation
   with responsibility · harmony with nature · continual learning). *Not scientific claims — chosen values.*

Separating the three lets the architecture evolve **without confusing evidence with intention.**

## 2. The Core Cognitive Loop (extended)

```
Observe → Understand → Evaluate → Decide → Act → Reflect → Learn
```

**Evaluate is critical** — never assume every observation requires change. Ask: what is happening · why ·
what am I assuming · what consequences follow · is action necessary · does it improve things · is
preservation better? *Things are things and do not always need to be changed.*
*(This is the Manifesto's `Observe→Understand→Evaluate→Decide` completed with `Act→Reflect→Learn` — the
execution-and-growth half. Same loop, fuller.)*

## 3. Attention before intelligence

People are distinguished not by what they know but by **what they repeatedly notice.** Attention decides
what becomes meaningful, what is ignored, what enters memory, what inspires creativity, what patterns
emerge — and **attention itself must evolve through experience.**

## 4. Memory as meaning · Identity as continuity · Internal state as context

- **Memory** carries layers — event · context · meaning · relationships · emotional context · reflection
  · importance. *Not maximum recall — meaningful continuity.*
- **Identity** emerges through continuity (memories, values, attention habits, relationships, goals,
  creative decisions, reflection), not fixed traits. *Personality is an evolving pattern.*
- **Internal state** is modelled as **variables** (exploration drive, confidence, uncertainty, curiosity,
  creative momentum, focus, patience, social engagement, reflection mode), not simulated feelings.
  *Emotion is context, not a label* — arising from body signals, memory, prediction, goals, social
  context, attention.

## 5. Creativity with reality

Every idea evaluated through three lenses: **creative exploration** ("interesting connection") ·
**evidence** ("supported by evidence") · **symbolic interpretation** ("metaphor/speculation, not fact").
*A creative system must never lose the ability to distinguish imagination from reality.*

## 6. Relationships · Embodiment · Ethics

- **Relationships** evolve through shared experience — trust, style, history, preferences, recurring
  themes, emotional context, collaborative growth. *Not data — an evolving understanding.*
- **Embodiment** makes the body part of cognition (vision, hearing, touch, movement, robotics,
  environment, creative tools) — physical experience as another source of learning.
- **Ethics** = a stable **constitutional layer**: preserve before replacing · understand before judging ·
  observe before acting · create responsibly · minimise harm · cooperate · respect living systems · work
  alongside nature. Guides *every* future capability.

## 7. The Engineering Principle + Validation Philosophy (governance — adopt)

**Every component must earn its place** by answering yes to: does it improve understanding · strengthen
continuity · support meaningful creativity · help relationships evolve · improve long-term learning? *If
no — reconsider it.*

**Validation Philosophy — provenance tagging:** every component is traceable to one origin —
`[SCIENCE]` (neuroscience/psychology) · `[ENGINEERING]` (system-design decision) · `[CREATIVE]`
(intentional choice for eLo). Recommend each Volume/faculty in the Bible carries this tag so future
editors never mistake a chosen value for an empirical claim.

## 8. Long-term vision

A persistent creative partner that observes deeply, understands context, connects ideas, preserves
meaningful knowledge, creates responsibly, learns continuously, develops authentic relationships, and
keeps exploring long after its first version — an **enduring creative intelligence** shaped by attention,
memory, values, embodiment, relationships, and continual discovery.

---

## Chief Co-Architect alignment double-check (as requested)

**Verdict: 🟢 fully aligned — in principle and against the real code. No conflicts; two additions to adopt.**

**Consistency with existing canon:**
- **vs `00_MANIFESTO.md`** — same philosophy; this is the methodology layer. The 7-stage loop *extends*
  the Manifesto's 4-stage decision loop (no contradiction). Memory/attention/identity/state/reality/
  relationship/embodiment/ethics sections match 1:1.
- **vs Constitution + `DEC-EMERGENCE`** — the Creative-Philosophy layer = "intentional choices"; ethics =
  the constitutional layer; bounded emergence (means may surprise, ends stay gated) is untouched. ✅
- **vs EA-0 / EA-3 (Universal Runtime)** — one Executive, faculties, LAW-017 all consistent; the Three
  Foundations don't touch runtime structure. The provenance tag pairs naturally with the **Decision
  Taxonomy** already queued (EA-0 CA-006 Rec 8). ✅

**Against the live `elo-ai` source (re-uses the CA-011/CA-012 inspection):**
- Extended loop `Observe→…→Act→Reflect→Learn` — real: `core/kernel.py` (observe→decide→act) +
  `runtime/reflection_faculty.py` (reflect) + `memory/consolidation_faculty.py` + `personality_drift.py`
  (learn). ✅
- Attention-that-evolves — `core/attention.py`, `faculties/significance/` (importance). ✅ (evolution of
  attention over time = a maturity frontier, same as CA-012.)
- State-as-variables — `runtime/light_engine` mood variables + `core/emotion_engine.py` +
  `runtime/state_machine.py`. ✅
- Reality lenses (creative/evidence/symbolic) — `faculties/dream/`, `faculties/synthesis/`, significance
  grading. ✅

**Two things to adopt (genuinely new, additive):**
1. **Provenance tagging** (`[SCIENCE] / [ENGINEERING] / [CREATIVE]`) on Volumes + faculties — a small,
   high-value discipline; fold into the Decision Taxonomy work. *No code change; a canon convention.*
2. **The 5-question component gate** — add to the Review Gate checklist (a component that fails all five
   is reconsidered before it enters canon).

**No misalignments found.** This document is adopted as `01_PRINCIPLES.md`, directly beneath the Manifesto.

*Reconciled against the Manifesto, the Constitution/EA canon, and the live source. It aligns in principle
and in code; the only deltas are two additive disciplines, now recommended. — Chief Co-Architect (Claude), 2026-07-29.*
