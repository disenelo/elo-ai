# 03d_WO-102 — eLo cannot represent David's family, home, or anything that happened

**WO:** WO-102 (closes the code half of WO-CANON-XXIV) · **Seat:** builder · **Priority:** P1
**Gate?** none. **Spec:** `docs/architecture/Volume_XXIV/01_Ontology_and_the_Knowledge_Graph.md`
— §1.3.5 Person (`:219`) · §1.3.6 Place (`:266`) · §1.3.7 Event (`:298`), rationale `:44-50, :61-63`.

## The gap
[VERIFIED] The volume specifies **Person · Place · Event** with full schemas and MUST rules. **The code has
none of it.**
- `relationships/world_graph.py:85` — `type: str`, free-form; only `project` and `brand` are seeded
  (`:30, :38, :46, :54, :62`).
- `relationships/world_graph.json` — keys are `["entities", "relationships"]` only.
- `knowledge/graph_loader.py:26-27, :41-42` — loads world_graph + concepts + viewpoints. Nothing else.
- The stores the volume names — `relationships/people.json`, `relationships/places.json`,
  `relationships/events.json` — **do not exist on disk**, and no loader references them.

**So eLo cannot hold the fact that David has a family, or where he lives, or that something happened to
him.** For a companion whose entire purpose is one person, that is the most consequential gap in the audit.
It has nothing to do with the parked product work — it is the personal-companion scope.

## Build
1. Create the three stores per the volume's schemas. **Follow Ruling A** — `relationships/` is the
   canonical graph; `identity/world_graph.json` is retired. Do not create a fourth home.
2. `knowledge/graph_loader.py` loads them into the one graph.
3. Entity `type` becomes a **closed set** (`project · brand · person · place · event`, extendable in one
   named place) — not a free-form string. Free-form is why two ontologies drifted in the first place.
4. Retrieval reaches them, so a question about a person/place/event resolves from the graph.
5. **Verified Speech holds:** eLo states these facts only from the graph — never inferred, never guessed.
   An empty store means he says he doesn't know. **Do not seed placeholder people.**

## 🔴 Do NOT invent David's data
Create the **structure**, empty. Who is in it is David's to say. If you find yourself typing a family
member's name, stop — that is fabrication about a real person and it violates Verified Speech at the worst
possible point.

## Test (without David)
- The three stores load; a seeded test person/place/event is retrievable through the normal path.
- An unknown person ⇒ eLo says he doesn't know. **No inference, no confabulation.**
- Type validation rejects an out-of-set type loudly (Rule 1 alarm).
- Ruling A holds: exactly one graph is read; `identity/world_graph.json` is not resurrected.

## Done when
Green, committed, hash to outbox. Then tell me it's ready and **I'll ask David what he wants eLo to know
about him** — that question is worth asking once, properly, not as a build blocker.
