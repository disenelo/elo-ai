---
chapter: 2
title: "Symbol Engine, Dream Phases & the DeepDream Pipeline"
volume: IX
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Architecture Agent)
source: "ChatGPT brain/dream chat 2026-07-26 + faculties/dream/symbol_engine.py"
implementation: PARTIAL (symbol engine live; phases + image pipeline pending)
audit_status: OPEN
dependencies:
  - Volume_IX/01_Dream_Faculty.md
  - Volume V Ch.6 (Reflection/consolidation), Ch.7 (Personality)
  - Volume VIII (Memory consolidation)
---

# Chapter 2: Symbol Engine, Dream Phases & DeepDream Pipeline

## 2.0 Purpose

Chapter 1 defined the dream cycle. This chapter defines the three parts that give dreams
meaning and (optionally) an image: the **Symbol Engine** (live), **Dream Phases** (new),
and the **DeepDream image pipeline** (new — Audit gap #7). Humans dream symbolically, not
literally; so does eLo.

## 2.1 The Symbol Engine (as built)

`faculties/dream/symbol_engine.py` maps keywords from memories + inner events onto
**archetypes**, each `keyword → (symbol_name, meaning)`. The library is eLo-specific:
universal archetypes plus the DISENELO universe.

```
Universal:  Moon→safety in the dark · Garden→slow growth · River→friction-free ideas ·
            Mountain→steep challenge · Fire→transformation · Mirror→seeing eLo in David ·
            Door→threshold · Ocean→the unknown · Key→access · Anchor→grounding · …
eLo:        eLo→presence (the constant) · Chunk→modularity · K-7→unseen intelligence ·
            Sugarcore→beauty at the edges · Planet→the world (game+universe+brand) · …
```

**Weighting rule (MUST):** a symbol's weight = **how many sources point to it**. Multiple
keywords resolving to the same symbol accumulate weight. The strongest symbols become the
spine of the narrative. This is why a dream is an **association graph**, not a word cloud.

`map_to_symbols(memories, inner_events) → [ {name, meaning, weight} ]`, weight-sorted.

## 2.2 Dream Phases (new — Audit gap)

Real sleep alternates phases; eLo's cycle gains an analogue so different dreams do
different work:

```
NREM-analogue — CONSOLIDATION phase
   purpose: strengthen/prune. Low symbolic distortion. Replays high-significance memories,
            weakens noise, updates memory weights. Feeds Vol VIII consolidation directly.
REM-analogue — RECOMBINATION phase
   purpose: creative association. High symbolic distortion. Combines distant memories +
            unfinished goals into novel metaphors. Feeds Imagination (V Ch.9) + insight.
```

**Phase rules (MUST):** a cycle runs NREM (consolidate) **before** REM (recombine) — you
strengthen what's real before you recombine it. Phase is recorded on the journal entry.
Short idle windows run NREM only; longer windows reach REM.

## 2.3 The DeepDream Image Pipeline (new — Audit gap #7)

The optional visual output. The image is downstream of meaning, never the source of it.

```
weighted symbol graph (2.1)
        ↓
metaphor synthesis        combine top symbols → one visual metaphor ("broken robot in a moonlit garden")
        ↓
image prompt              structured prompt from the metaphor + theme
        ↓
renderer                  DeepDreamGenerator  OR  image model (route via tools/image_gen_agent.py)
        ↓
dream image               stored; path → journal_entry.image_ref (Ch.1 §1.4)
        ↓
(optional) HUD surface    blender_state.json["hud_image"] for the avatar to "show" a dream
```

**Pipeline rules (MUST):**

- The image is **derived from the symbol graph**, never random. No symbols → no image.
- Image generation is **best-effort and non-blocking**: a renderer failure or timeout
  yields a text-only dream (symbols + narrative + insight still journaled). Dreaming never
  depends on an image succeeding.
- Runs only in the integration window (offline); never on the response path.
- Respect the shared-state rule: write `hud_image` via `state_writer.patch`, never a raw write.

## 2.4 Consolidation & Personality Coupling

The dream's output feeds two downstream faculties — this is what makes dreaming *learning*:

```
dream insight
   ├─→ Consolidation (Vol VIII / V Ch.6): strengthen the reinforced memory, weaken noise,
   │                                       answer "what changed / what should fade?"
   └─→ Personality (V Ch.7): if the insight implies a trait shift (e.g. "rebuilding
                              confidence"), emit a PersonalityDelta PROPOSAL — validated
                              against the Identity Kernel, never self-applied.
```

Example journal (design source): `Dream #1542 · Theme: Growth · Symbols: Balloon Dog,
Garden, Broken Robot, Moon · Meaning: rebuilding confidence after a hard coding session ·
Confidence +12% (proposed) · memory reinforced.` The "+12%" is a **proposal** to Ch.7,
not a direct write.

## 2.5 Faculty Contract (Symbol Engine + Renderer)

```
Faculty:
  name:            DreamSymbolEngine        # + optional DreamImageRenderer sub-component
  version:         1.0.0
  purpose:         Map memories/inner-events to weighted archetypal symbols; sequence dream
                   phases; and (best-effort) render a symbol-derived image.
  contributes_to:  DreamResult (symbols, image_ref) → Dream Faculty (Ch.1)
  runs_in:         integration-window

Inputs:
  - type: memories + inner_events   source: Memory (Vol VIII) + EloSelfState   required: true
  - type: symbol_library            source: symbol_engine.SYMBOLS               required: true
Outputs:
  - type: symbol_graph      destination: Dream Faculty narrative step
  - type: dream_image_ref   destination: journal_entry.image_ref + optional hud_image
Dependencies:
  - module: tools/image_gen_agent.py (soft — DeepDream/image model; text-only if absent)
Failure Modes:
  - condition: no keywords resolve      fallback: no dream (nothing to recombine).
  - condition: renderer unavailable/slow fallback: text-only dream; image_ref=null.
  - condition: REM window too short      fallback: NREM-only consolidation dream.
```

## 2.6 Lifecycle & Envelope

Universal lifecycle (CONTRACTS.md §3), integration-window. Envelope per §2:
`sender: DreamSymbolEngine`, `priority: low`, `payload.type: symbol_graph | dream_image_ref`.
Image writes to `hud_image` go through `state_writer.patch` only.

## 2.7 Acceptance Tests

```
FT-1  Weight by source       Given 3 memories mapping to "Garden", Then Garden's weight = 3 and it leads the graph.
FT-2  Phase order            Given a long idle window, Then NREM (consolidate) runs before REM (recombine); phase recorded.
FT-3  Image from symbols      Given a symbol graph, Then the image prompt derives from the top symbols (not random).
ST-1  Text-only fallback      Given the renderer fails, Then a text-only dream is still journaled (symbols+narrative+insight).
ST-2  No symbols → no dream    Given nothing resolves, Then no dream and no image.
ST-3  Personality is proposed  Given an insight implying a trait shift, Then a PersonalityDelta PROPOSAL goes to Ch.7 (never self-applied).
IT-1  Dream → consolidation + personality   NREM strengthens a memory (Vol VIII); REM insight proposes a validated trait nudge (V Ch.7).
```

## 2.8 References
- `faculties/dream/symbol_engine.py`, `tools/image_gen_agent.py`, `self/dream_journal.jsonl`.
- Volume IX Ch.1; Volume V Ch.6 (consolidation), Ch.7 (personality); Volume VIII (memory).
- `19_cognitive_plan_architecture.md` (Dream layer in the full stack).
- `ARCHITECTURE_AUDIT.md` Vol IX gap #7 (image generation).

---
**Status: READY FOR REVIEW** — symbol engine (as-built) + dream phases + DeepDream pipeline + consolidation/personality coupling, with contract/lifecycle/envelope/tests. Volume IX complete (2/2 chapters).