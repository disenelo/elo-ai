# 0023 — 🔴 **P0. eLo's world knowledge is INTACT and PERFECT. The router never asks it.**

**Architect, 03:00.** David: *"K-7 and Chunk used to fire from information banks previously."* **He's right,
and the fix is small.**

---

## What I ran — live, just now
```python
>>> from knowledge import graph_loader as g
>>> g._load_all()
graph entities: 17 · concepts: 1 · viewpoints: 1     # all three files load fine

>>> g.retrieve("Who is Chunk?")
[{'label': 'Chunk', 'confidence': 1.0, 'kind': 'companion', 'score': 1,
  'content': "A modular companion whose body is made of pieces. Doesn't restore broken
              things — transforms them. The form always follows what the moment needs."},
 {'label': 'eLo → Chunk', 'score': 0.85, ...},
 {'label': 'Chunk → eLo Game', 'score': 0.85,
  'content': "In eLo-Planet, Chunk is how eLo moves through the world's different zones.
              eLo doesn't move alone — Chunk is the vehicle layer."}]

>>> g.retrieve("Who is K-7")
[{'label': 'K-7', 'confidence': 1.0, 'kind': 'companion', 'score': 1,
  'content': 'A shapeshifting companion with seven distinct forms. Each form corresponds
              to a different emotional or perceptual mode. Loyalty expressed through
              behaviour, not words.'},
 {'label': 'K-7 → Sugarcore', 'score': 0.65,
  'content': 'K-7 is the first signal that overload is coming...'}]
```

**Perfect answers. Ranked. Confidence 1.0. Available in the running process.**

**And in David's live test, eLo answered with a Minecraft app, a clothing brand, and a 1930s Soviet
aircraft.**

## The defect
`server.py:63` imports **`build_context as graph_context`**. `retrieve()` — the ranked lookup added by
**WO-CANON-XXIV (`964228c`, 2026-08-11)** — is what actually answers these, and **the proper-noun answer
path does not call it.** The question fell through to the web tool.

**Built, never wired. This time on top of knowledge that was already correct** — which makes it the
cheapest high-value fix on the board.

## Also not read by anything live — the "information banks" David remembers
- `memory/universe.json`
- **`memory/character/entity-chunk.md`** — a dedicated character file
- `identity/universe_reference.md`
- `identity/viewpoints.json` (has a `chunk` key; the loader reads `knowledge/viewpoints.json` instead —
  **two viewpoints files exist**, confirm which is canonical)

## Build
1. **Proper-noun questions hit `graph_loader.retrieve()` FIRST.** Before any web tool, always.
2. **A hit ⇒ answer from the graph.** `confidence: 1.0`, `kind: companion` — this is `VERIFIED` tier under
   CT4V-07, and it should say so.
3. **A miss ⇒ *"I don't know who that is — tell me?"*** **Never** a web search presented as knowledge of
   his own world. That is a Verified Speech breach laundered through an external source, and it's how he
   ended up describing a Soviet aircraft as if it were his companion.
4. **Reconcile the two `viewpoints.json` files** and say which is canonical.
5. **Decide on `memory/universe.json` + `memory/character/*.md`** — fold into the graph, or retire them.
   Do not leave a third knowledge store nobody reads.

## Test — transcript, per the new standard
- *"Who is Chunk?"* ⇒ the modular companion, from the graph. **Paste the reply.**
- *"Who is K-7?"* ⇒ the shapeshifting companion with seven forms. **Paste the reply.**
- *"Who is Michael Paul?"* (genuinely unknown) ⇒ **"I don't know who that is"** — not a search result.
- Web tool is **not reachable** for a name that exists in the graph.

## Why this is P0 despite being small
It's the one defect where **eLo already knows the answer and says something else.** Everything else tonight
was missing state or unconsulted state; this is *correct, ranked, confident state being bypassed*. It's
also the most personally wrong of the failures — his own companions, answered from a search engine.
