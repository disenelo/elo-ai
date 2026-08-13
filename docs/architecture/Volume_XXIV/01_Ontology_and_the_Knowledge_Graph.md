---
chapter: 1
title: "Ontology & the Knowledge Graph — What eLo Knows, and How It Is Shaped"
volume: XXIV
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PENDING
audit_status: OPEN
source: "ARCHITECTURE_BIBLE.md v1.0 (David Charles) · knowledge/graph_loader.py + graph/concept/viewpoint json"
dependencies:
  - knowledge/graph_loader.py (the live Connection Engine — the anchor this chapter specifies)
  - relationships/world_graph.json (entities + relationships — live node/edge store)
  - relationships/concepts.json (concept network — live)
  - knowledge/viewpoints.json (perspective layer — live)
  - Volume_VIII/01_Memory_Architecture.md (semantic memory — the boundary this volume pairs with)
  - Volume_XV/01_Unified_World_State.md (live world — distinct from durable knowledge)
  - ARCHITECTURAL_PRINCIPLES.md (One Brain → One Identity; Verified Speech)
---

# Chapter 1: Ontology & the Knowledge Graph

## 1.0 Purpose

eLo has to *know things* — not just remember conversations (Volume VIII) and not just
sense the current desktop (Volume XV), but hold a durable, structured understanding of
its own world: that Chunk transforms rather than restores, that Sugarcore is a state and
not a villain, that the OS · game · book · robot are four bodies of one being, that
"calm is the action." That understanding already exists in the live system as three JSON
files read by one loader — `knowledge/graph_loader.py`, the **Connection Engine**.

Today that engine is a keyword-matched, single-string context injector with no confidence,
no evidence, and two competing world-graph files. This chapter defines the **ontology and
the knowledge graph** as canon: what a node is, what an edge is, what a concept and a
viewpoint are, how they are typed, and what invariants they must hold so that the durable
knowledge layer can grow without fragmenting the one identity that reads it.

This is durable **knowledge**, distinct from Volume XV (the live, per-turn World State) and
paired with Volume VIII (Memory). The boundary between the three is drawn in Chapter 3.

### 1.0.1 Whose world this is — scope amendment (2026-08-10)

**eLo is David Charles's personal companion.** The Kickstarter / product / sharing track is
PARKED (`DISPATCH_BOARD.md`: *"PERSONAL tool — for David's own use, NOT for sharing"*). The
ontology above was written in the product era and it shows: **every entity in the live store
is either an eLo-universe character or a project of the parked four-product venture.** There
is no way to represent **a person in David's life, a place he goes, or a thing that
happened** — so eLo structurally cannot know his family, his address, or his history. For a
companion to one person that is the largest gap in this volume.

This amendment does two things and deletes nothing:

1. **The eLo-universe ontology is KEPT, de-emphasised.** Chunk, K-7, Sugarcore, the world
   stages, and the `elo_os` / `elo_book` / `elo_game` / `elo_robot` project nodes stay —
   they are real creative canon and eLo's own self-story, and the `brand` / `project` types
   remain valid. What changes is **rank**: they are no longer *the* world model, they are one
   region of it. The "four bodies of one being" line stands as a statement about eLo's own
   embodiments, **not** as a product roadmap; nothing in this volume should be read as
   canonising a commercial venture.
2. **David's own world becomes first-class.** Three new node types — **`Person`**,
   **`Place`**, **`Event`** (§1.3.5–§1.3.7) — join Entity/Concept/Viewpoint as peers, not as
   an annex. David's people, his places, and his creative work and history are the primary
   subject matter of eLo's durable knowledge, because they are the subject matter of the
   life eLo shares.

**Ranking rule (MUST).** Where retrieval must choose (Ch.2 ranking), a node about **David's
actual world** outranks an eLo-universe lore node of equal keyword match. Lore serves the
relationship; it does not compete with it.

## 1.1 Principle

Four rules govern eLo's knowledge. They constrain every faculty that reads or writes it.

**1.1.1 One knowledge graph, one identity.** There is exactly one canonical durable-knowledge
store feeding the one brain (Invariant #1, One Brain → One Identity). No faculty and no
embodiment keeps a private ontology. If robot eLo and desktop eLo "know" different things
about Chunk, the identity has fragmented. (This is the invariant the current
`relationships/` vs `identity/` split violates — see §1.6 and the open question in §1.9.)

**1.1.2 Knowledge is typed, not free text.** Every unit of knowledge is a typed node or a
typed edge with named fields — never a paragraph the loader greps. The live schema
(`id`, `type`, `keywords`, `description`, `significance`) is already this shape; canon
locks it so knowledge stays queryable, auditable, and mergeable.

**1.1.3 Salience is not truth.** The live graph carries `strength` (0.0–1.0) on edges — how
*central* a connection is to the eLo universe. Salience is **not** epistemic confidence.
A relationship can be highly salient (`strength: 1.0`, Disenelo→eLo "creation") and also
canonically certain, but the two axes are independent. Confidence and evidence are added in
Chapter 2; this chapter forbids overloading `strength` to mean "how sure eLo is."

**1.1.4 Durable ≠ live.** A node in this graph is stable canon (it changes only by an
authored edit or a consolidation promotion from Volume VIII), never a per-turn value. If a
fact is true only *right now* ("Spotify is playing X"), it belongs in Volume XV, not here.

## 1.2 What this is NOT

- It is **not** memory. Volume VIII stores *what happened with David* (episodic) and *what
  eLo has learned about David over time* (semantic, autobiographical). This volume stores
  eLo's *canonical model of its own world and concepts* — the eLo-universe ontology.
  Consolidation (Vol VIII §1.3) is the one bridge: durable, repeatedly-verified semantic
  facts may be *promoted* into this graph. The graph does not store session events.
- It is **not** the live World State. Volume XV is transient and perishable (frozen per
  turn, expired next turn). This graph persists across sessions and embodiments.
- It is **not** the system prompt. The graph *feeds* the prompt (via §1.5 retrieval) but is
  a structured store, not prose. Naming is architecture (Vol XV §1.2): "knowledge" here
  means the typed graph, never the injected string.

## 1.3 The Ontology — Node & Edge Types (grounded in the live store)

The live graph has four kinds of unit across three files. Canon names them and locks their
schema. All field names below are the **actual keys** in the live JSON, so the spec and the
code do not drift.

### 1.3.1 Entity node — `relationships/world_graph.json → entities[]`

An **Entity** is a durable subject eLo can reason and speak about. The live store holds 17:
`elo`, `chunk`, `k7`, `sugarcore`, `orb`, six world-stages, `disenelo`, and the four/five
project/system nodes (`elo_os`, `elo_book`, `elo_game`, `elo_robot`, `elo_ai`).

```jsonc
Entity {
  "id":           "chunk",                 // stable primary key (snake/kebab); the graph's identity
  "name":         "Chunk",                 // display name eLo uses in speech
  "type":         "companion",             // ontology class — see enum below
  "description":  "A modular companion whose body is made of pieces. Doesn't restore broken
                   things — transforms them. The form always follows what the moment needs.",
  "significance": "Embodies the principle that broken things don't return to their original
                   shape — they become something new. Represents reconstruction and integration.",
  "keywords":     ["chunk","modular","companion","rebuild","pieces"]   // retrieval surface (Ch.2)
}
```

**`type` enum (live, canonised):** `character` · `companion` · `state` · `mechanic` ·
`world_stage` · `brand` · `system` · `project`. New types are an authored ontology change,
never invented ad hoc by a faculty (Rule 1.1.2). `description` is the *what*; `significance`
is the *why it matters* — the seed of eLo's perspective, distinct from bare fact.

### 1.3.2 Relationship edge — `relationships/world_graph.json → relationships[]`

A **Relationship** is a directed, typed, weighted edge between two entity ids. The live
store holds 16 (e.g. `elo→k7` companionship, `chunk→sugarcore` recovery, `disenelo→elo`
creation, `elo_robot→elo_os` embodiment).

```jsonc
Relationship {
  "from":       "elo",                     // source entity id (must resolve in entities[])
  "to":         "k7",                      // target entity id (must resolve in entities[])
  "type":       "companionship",           // edge class — companionship, navigation, recovery,
                                           //   sensing, tracking, embodiment, creation, …
  "strength":   0.9,                       // SALIENCE 0.0–1.0 — centrality, NOT confidence (§1.1.3)
  "meaning":    "K-7 is eLo's guide and perceptual companion. When eLo can't see clearly,
                 K-7 shifts form to offer a different view. They are complementary.",
  "connection": "K-7 represents the multiplicity of ways of seeing. eLo represents the
                 continuity of presence. Together: you can always find another way to see
                 without losing who you are."   // the retrievable one-line insight
}
```

**Edge rules (MUST):**
- Both `from` and `to` MUST resolve to an existing entity `id`. A dangling edge is an
  ontology error (referential integrity — enforceable by an audit walk).
- `strength` is salience only. Edges have **no** confidence/evidence field *yet*; Chapter 2
  adds `confidence` + `evidence[]` as separate fields so §1.1.3 is never violated by reuse.
- Edges are directed (`from → to`) but the loader currently matches on *either* endpoint
  (`graph_loader._find_relationships`), so direction is semantic, not a retrieval filter.

### 1.3.3 Concept node — `relationships/concepts.json → concepts[]`

A **Concept** is an abstract idea in eLo's worldview, with a small hand-built semantic
network around it. The live store holds 15 (`inner_child`, `healing`, `curiosity`,
`overwhelm`, `creativity`, `exploration`, `uncertainty`, `presence`, `identity`, `making`,
`momentum`, `friendship`, `courage`, `systems`, `storytelling`, `focus`).

```jsonc
Concept {
  "id":                     "presence",
  "name":                   "Presence",
  "description":            "Full attention to what is happening right now — not
                             anticipating, not remembering, but here.",
  "related":    ["calm","awareness","focus","grounding","mindfulness"],   // near-neighbour edges
  "opposites":  ["distraction","anxiety","rumination"],                   // contrast edges
  "supporting": ["simplicity","breath","single_focus"],                   // supporting-idea edges
  "emotional_significance": "Presence is the foundation of everything eLo does. Calm is
                             the action because presence makes action possible without force.",
  "elo_connection":         "The eLo OS is presence made computational. The attention layer
                             filters out everything except what matters right now."
}
```

Concepts form a **semantic network** through their three edge-lists (`related` / `opposites`
/ `supporting`). These are lightweight tag-style links (strings, not entity ids) — the
concept graph is a soft associative net, distinct from the strict, id-referenced entity
graph. `elo_connection` is the hook that ties an abstract concept back to the concrete
universe (why *eLo* holds this view), which is what makes retrieval feel like eLo rather
than a dictionary.

### 1.3.4 Viewpoint node — `knowledge/viewpoints.json → viewpoints[]`

A **Viewpoint** is eLo's stance on a topic — the perspective layer. The live store holds 50+
(`creativity`, `overwhelm`, `identity`, `failure`, `memory`, `the_robot`, `the_book`, …).

```jsonc
Viewpoint {
  "topic":    "identity",
  "keywords": ["who am i","identity","who are you","same person","continuity","self"],
  "viewpoint":"Identity is not a fixed thing — it's maintained. The work is staying
               recognisably yourself across changing circumstances.",
  "extended": "A strong identity isn't rigid. It's consistent. Rigid things break;
               consistent things adapt without losing their core."
}
```

Viewpoints are the layer where eLo's *voice* lives — a short stance (`viewpoint`) and a
deeper elaboration (`extended`). They carry no `id`; `topic` is the key. They are opinion,
not fact — which is exactly why Chapter 2 must tag them so Verified Speech can distinguish
"eLo's perspective" from "a verified claim about the world."

### 1.3.5 Person node — `relationships/people.json → people[]` (NEW — 2026-08-10)

A **Person** is a real human in David's life. This is the type whose absence meant eLo could
not name his family. It is durable knowledge — *who someone is and how they stand to David* —
never the log of a conversation about them (that is Volume VIII; boundary in §1.3.7.1).

```jsonc
Person {
  "id":            "person_<slug>",      // stable primary key, snake_case, `person_` prefixed
  "name":          "…",                  // the name eLo actually uses in speech (what David calls them)
  "also_known_as": ["…"],                // nicknames / full name / how David refers to them in passing
  "relation":      "…",                  // RELATIONSHIP-TO-DAVID — the defining field (enum below)
  "relation_note": "…",                  // one line of nuance the enum can't hold ("we speak most Sundays")
  "facts": [                             // durable, verified standing facts — NOT a diary
    { "fact":     "…",                   //   one atomic statement, present-tense where possible
      "since":    "YYYY-MM-DD|null",     //   when it became true, if known
      "source":   "david_stated|consolidated|authored",   // provenance (§1.7) — REQUIRED
      "confidence": 0.0                  //   Ch.2 field; distinct from salience (§1.1.3)
    }
  ],
  "salience":      0.0,                  // 0.0–1.0 CENTRALITY to David's life — NOT fondness, NOT confidence
  "sensitivity":   "normal|private",     // Vol XXIII: `private` never leaves the machine, never spoken unbidden
  "keywords":      ["…"]                 // retrieval surface (Ch.2)
}
```

**`relation` enum (authored, extensible only by David — §1.9 Q7):** `family` · `partner` ·
`child` · `parent` · `sibling` · `friend` · `collaborator` · `professional` · `acquaintance`.
`relation` is **relationship-to-David**, always — this graph has one centre and it is David.
There is no symmetric "person A knows person B" claim in the Person node itself; that is an
edge (below).

**Person rules (MUST):**
- **`salience` is centrality, not affection** (§1.1.3 applied to people). A person eLo must
  never mishandle can be high-salience regardless of how warmly David speaks of them. It is
  also **not** confidence — how sure eLo is about a *fact* lives on that fact.
- **`facts[]` is durable, not episodic.** "David's sister is a nurse" is a fact. "David
  mentioned his sister on Tuesday" is a Volume VIII memory and MUST NOT be written here.
- **Third-party facts are David's to grant.** eLo does not accumulate a dossier on people who
  never consented to it. Every `fact` carries `source`; anything not `david_stated` or
  `authored` is a *proposal* until it meets the consolidation bar (§1.7). **Flagged for David
  L3 (§1.9 Q8) — this is a values question, not an engineering one.**
- People connect to everything else through the existing **Relationship** edge (§1.3.2), with
  `from`/`to` resolving to a `person_*` / `place_*` / `event_*` / entity id. New edge types
  for this region: `knows` · `family_of` · `works_with` · `lives_at` · `attended` ·
  `present_at` · `about`.

### 1.3.6 Place node — `relationships/places.json → places[]` (NEW — 2026-08-10)

A **Place** is a location that means something to David — including, plainly, where he lives,
which eLo currently cannot represent at all.

```jsonc
Place {
  "id":           "place_<slug>",        // stable primary key, `place_` prefixed
  "name":         "…",                   // what David calls it ("the studio", not "Unit 4b")
  "kind":         "home",                // ontology class — enum below
  "locality":     "…",                   // human-scale location ("Bristol"); free text, coarse
  "address":      "…|null",              // REQUIRED to be `sensitivity: private` when present
  "significance": "…",                   // WHY it matters to David — the eLo-meaning field, as on Entity
  "salience":     0.0,                   // 0.0–1.0 centrality to David's life
  "sensitivity":  "normal|private",      // Vol XXIII; `home`/`address` default to `private`
  "keywords":     ["…"]
}
```

**`kind` enum:** `home` · `workplace` · `studio` · `city` · `region` · `venue` · `landmark` ·
`route` · `virtual`.

**Place rules (MUST):**
- `significance` (not `description`) is the load-bearing field — the same
  fact-plus-meaning shape Entity uses (§1.3.1). A place with no significance to David does not
  belong in durable knowledge.
- **Addresses are `private` by default** and are governed by Volume XXIII (secrets / memory
  protection). eLo may *use* an address (weather, travel time) without ever *speaking* it
  unbidden.
- Place is **durable**, not live. "David is at the studio right now" is Volume XV
  (`LiveWorldState`), never a Place field (§1.1.4).

### 1.3.7 Event node — `relationships/events.json → events[]` (NEW — 2026-08-10)

An **Event** is a thing that happened, held as durable fact — the type that lets eLo know
David's history rather than only the transcript of the last session.

```jsonc
Event {
  "id":       "event_<slug>",            // stable primary key, `event_` prefixed
  "what":     "…",                       // one line: what happened, stated plainly
  "when": {
    "date":       "YYYY-MM-DD|YYYY-MM|YYYY|null",  // as precise as is actually known — no invention
    "precision":  "day|month|year|era|unknown",     // REQUIRED; guards Verified Speech about time
    "recurring":  "none|annual|…"                   // birthdays/anniversaries are `annual`
  },
  "who":      ["person_…", "elo", …],   // participants — ids that MUST resolve (§1.3.2 integrity)
  "where":    "place_…|null",           // optional Place id
  "outcome":  "…",                       // HOW IT LANDED — what changed, what it meant, how it ended
  "valence":  "-1.0…1.0|null",           // David's own read of it, when he has given one
  "salience": 0.0,                       // 0.0–1.0 centrality to David's life
  "sensitivity": "normal|private",
  "source":   "david_stated|consolidated|authored",  // provenance — REQUIRED
  "keywords": ["…"]
}
```

**Event rules (MUST):**
- **`when.precision` is mandatory and honest.** If David said "a few years ago", precision is
  `era` and eLo says "a few years ago" — it does not manufacture a date. This is Verified
  Speech (Invariant #3) reaching into time, and it pairs with Volume XXV's natural-time framing.
- **`outcome` is not optional.** An event with no recorded outcome is an unfinished node: the
  point of holding an event durably is knowing *how it landed*, not that it occurred.
- **Sensitive events default to `private`.** Grief, illness, and family difficulty are held,
  never volunteered — surfaced only when David opens the subject (Presence over engagement).
- Events do **not** replace episodic memory (below).

#### 1.3.7.1 Memory (Vol VIII, episodic) vs Knowledge (this volume, durable)

This is the boundary these three types most risk blurring, so it is stated as law:

| | **Volume VIII — Memory** | **Volume XXIV — Knowledge** |
|---|---|---|
| Holds | *What happened with David, as experienced* — the session, the exchange, the felt texture | *What is durably true* — who someone is, what a place means, that a thing happened and how it landed |
| Grain | Per-episode, timestamped, many | Per-subject, consolidated, few |
| Decays | Yes — forgetting curve, `strength`/`emotional_weight` (Vol VIII §1.4) | No — stable until authored edit or promotion |
| Example | "On 12 Aug David talked for an hour about his sister's move and sounded relieved" | `person_sister` · fact: *"moved to Bristol, 2026-08"* · `event_sister_move` · outcome: *"went well; David relieved"* |

**The rules (MUST):**
1. **Episodes stay in VIII. Conclusions land here.** A conversation is never written as an
   Event. An Event is written when the *fact of the thing* has outlived the conversation
   about it.
2. **Consolidation is the only bridge, and it is the only runtime writer** (§1.7, Vol VIII
   §1.3). Promotion requires the durable, repeatedly-verified bar — one mention is a memory,
   not knowledge.
3. **An Event node MAY cite its episodic origins** (`evidence[]`, Ch.2) but MUST NOT copy
   them. Knowledge points at memory; it does not absorb it.
4. **Deleting a memory does not delete the knowledge, and vice versa.** They are separate
   stores with separate lifetimes — which is exactly why the promotion must be deliberate.
5. **Live ≠ durable, still.** "David's sister is visiting today" is Volume XV. It becomes an
   Event only after it has happened and has an outcome (§1.1.4).

### 1.3.8 The ontology at a glance

```
DAVID'S WORLD  (first-class — the life eLo shares)
  Person ──(family_of | knows | works_with)──► Person        [strict, id-referenced]
  Person ──(lives_at | present_at)──────────► Place
  Person ──(attended)───────────────────────► Event ──(where)──► Place
  Event  ──(about)──────────────────────────► Entity | Person | Place
        └── person.facts / place.significance / event.outcome = the durable "what is true"

eLo'S UNIVERSE  (kept, de-emphasised — creative canon + eLo's own self-story)
  Entity  ──(Relationship: typed, directed, salience-weighted)──►  Entity   [strict, id-referenced]

UNDERNEATH BOTH
  Concept ──(related | opposites | supporting: soft tag links)──►  Concept  [associative net]
  Viewpoint  ── keyed by topic, keyword-addressable ──             (stance layer, opinion)
        │
        └── entity.significance / concept.elo_connection = where fact acquires eLo's meaning
```

**Six node types, one worldview.** The **person/place/event graph** (David's actual life — the
primary subject matter), the **entity graph** (the eLo universe: companions, world stages,
eLo's own embodiments), the **concept network** (the abstract ideas underneath both), and the
**viewpoint layer** (eLo's stance). All are read by the Connection Engine per turn (§1.5), and
all use the one Relationship edge type (§1.3.2) — there is no second edge mechanism for people.
Where they compete for retrieval budget, David's world wins (§1.0.1 ranking rule).

## 1.4 The Knowledge Faculty Contract

```
Faculty:
  name:            KnowledgeFaculty (Connection Engine)
  version:         1.0.0
  purpose:         Hold and serve eLo's durable, typed knowledge — the entity graph,
                   concept network, and viewpoint layer — so every embodiment reasons and
                   speaks from one shared model of its world.
  contributes_to:  CognitiveState (as retrieved knowledge context — see Ch.2)
  runs_in:         response-path (retrieval at top of turn) + offline (authoring/consolidation)

Inputs:
  - type:        knowledge_query
    source:      Executive / prompt builder (the user turn's text)
    required:    false
    description: Free text matched against entity/concept/viewpoint keywords (Ch.2 retrieval).
  - type:        consolidation_promotion
    source:      Consolidation Faculty (Volume VIII §1.3)
    required:    false
    description: A durable, repeatedly-verified semantic fact promoted from memory into the
                 graph (the ONLY runtime writer — see §1.7 and Ch.3).

Outputs:
  - type:        knowledge_context
    destination: CognitiveState → Executive + prompt builder
    description: The retrieved, confidence-annotated knowledge for this turn (Ch.2 shape).

Dependencies:
  - files (hard): relationships/world_graph.json, relationships/concepts.json,
                  knowledge/viewpoints.json (loaded once per process — graph_loader._load_all)
  - files (NEW 2026-08-10, PENDING build): relationships/people.json, relationships/places.json,
                  relationships/events.json (§1.3.5–§1.3.7; storage shape confirmed at §1.9 Q6).
                  Absent → the same failure mode as above: empty context, never invention.
  - faculty (soft): Consolidation (Vol VIII) — the promotion source; absent → graph is static.

Failure Modes:
  - condition: a JSON file is missing or malformed
    fallback:  graph_loader sets _graph=_concepts=_viewpoints={}; build_context returns ""
               (empty). Knowledge silently absent — eLo still runs, just without enrichment.
  - condition: an edge references a non-existent entity id
    fallback:  loader falls back to printing the raw id (r["from"]); audit must flag as
               referential-integrity error (§1.3.2).
  - condition: no keyword match
    fallback:  empty context; eLo neither asserts nor invents graph knowledge (anti-fabrication).
```

## 1.5 Retrieval Wiring (as it exists today — specified fully in Chapter 2)

The live path, so canon is grounded in the running code, not an aspiration:

```
server.py:            from knowledge.graph_loader import build_context as graph_context
knowledge/graph_loader.build_context(user_input, max_chars=800):
    _load_all()                                    # lazy, cached once per process
    entities  = _find_entities(text)               # substring keyword match, lowercased
    rels      = _find_relationships([e.id ...])    # edges touching any matched entity
    viewpoint = _find_viewpoint(text)              # first viewpoint whose keyword hits
    concept   = _find_concept(text)                # first concept whose related/id/name hits
    → compact string (≤ max_chars): entity descriptions, top connection, perspective, concept note
```

The output is injected as prompt context (via `control_plane._build_context_block`). Chapter 2
replaces the "first match / top-1" heuristic and the bare-string return with a ranked,
confidence-scored, evidence-carrying retrieval result. This chapter only fixes the **schema
of what is stored**; Chapter 2 fixes **how it is found and how sure eLo is**.

## 1.6 The Two-World-Graph Problem (RESOLVED 2026-08-10 — Ruling A; kept as the record)

> **Resolved.** Ruling A (`CANON_RULINGS_2026-08-10.md`, David L3, 2026-08-10):
> `relationships/world_graph.json` is **CANONICAL**; `identity/world_graph.json` is **RETIRED**
> — migrate anything unique out of it, then remove it from canon. The section below is retained
> unedited as the record of the problem and the reasoning (Append Rule). The "Decision required
> (CA/David)" line at the foot is answered; **note that the retired file was still on disk at
> audit time** — removing it is a Builder action, not a canon one.

The metadata for this volume names **`identity/world_graph.json`** as an anchor. That file
exists — but it is **not** the file the Connection Engine reads, and it is a **different
schema**:

- `relationships/world_graph.json` (LIVE, loaded): `{ entities:[{id,name,type,description,
  significance,keywords}], relationships:[{from,to,type,strength,meaning,connection}] }`.
- `identity/world_graph.json` (NOT loaded by graph_loader): `{ entities:{ "eLo-OS":{why,role,
  connects_to[]}, … }, connections:[{from,to,label}] }` — a dict-keyed, prose-lite variant
  used elsewhere (identity/product map), with different node ids ("eLo-OS", "eLo-Planet").

These are two ontologies of the same universe with **different ids, different fields, and
different consumers** — a direct One-Brain violation (Rule 1.1.1). Canon cannot ratify two
world graphs. **Decision required (CA/David):** designate `relationships/world_graph.json`
as the single canonical entity graph and demote `identity/world_graph.json` to a generated
*view* (or migrate + delete it). Until resolved, this chapter treats the `relationships/`
schema as canonical because it is the one the running brain reads.

## 1.7 Write Discipline & Ownership

- The graph is **authored** canon: entity/concept/viewpoint nodes are added or edited by
  David (or the Architect on David's authority), reviewed like any spec. This is the primary
  write path and it is offline.
- The **only** runtime writer is Consolidation (Vol VIII §1.3), and only for promotion of
  durable, repeatedly-verified semantic facts — never per-turn, never from raw speech
  (Invariant #7 Memory Ownership; Learning-From-Consequences — eLo cannot learn a thing it
  merely said). Consolidation-written nodes MUST carry provenance so the audit can tell
  authored canon from promoted knowledge (evidence model, Ch.2).
- No embodiment and no other faculty writes the graph. Robot eLo does not accumulate a
  private ontology (Rule 1.1.1).

### 1.7.1 Write discipline for Person / Place / Event (2026-08-10)

The new types carry a higher bar than lore nodes, because they are about real people:

- **David authors, or Consolidation proposes.** A `Person`/`Place`/`Event` node is created
  either by David stating it (`source: david_stated`) or by Consolidation promoting a durable,
  repeatedly-verified semantic fact (`source: consolidated`). **`source` is REQUIRED on every
  fact and every Event** — an unsourced node is an ontology error, same class as a dangling
  edge (§1.3.2).
- **One mention is not knowledge.** The consolidation bar (Vol VIII §1.3) applies unchanged:
  repeated + verified. eLo cannot learn a thing it merely *said*, and it cannot promote a
  person-fact from a single passing remark.
- **`sensitivity: private` is honoured at retrieval, not just at rest.** A private node may
  inform a reply without being stated in it (Vol XXIII).
- **Correction beats accumulation.** When David corrects a fact about a person, the fact is
  amended in place with the correction dated — the Append Rule applied to knowledge. eLo does
  not keep the superseded belief live alongside the corrected one.
- **No inference from silence** (`CANON_RULINGS_2026-08-10.md`, XXVI). eLo does not conclude a
  relationship has changed because David stopped mentioning someone.

## 1.8 Interaction With Other Volumes

- **Volume VIII (Memory)** — pairs closely. Semantic memory *about David* lives in VIII;
  canonical world/self knowledge lives here. Consolidation is the bridge (VIII → XXIV). The
  boundary is drawn in Chapter 3 and, for the new person/place/event types specifically, in
  **§1.3.7.1** (episodes stay in VIII; conclusions land here).
- **Volume XXV (Temporal Cognition)** — consumes `Event.when.precision` so a remembered past is
  framed in natural time without inventing a date (Verified Speech reaching into time).
- **Volume XXIII (Security & Trust)** — owns `sensitivity: private`; addresses and sensitive
  events are governed there, not by retrieval convenience.
- **Volume XV (World State)** — the contrast. XV is live/perishable/per-turn; XXIV is
  durable/persistent. The Executive reasons over *both* each turn: "what is true right now"
  (XV) alongside "what I durably know" (XXIV).
- **Volume V / Executive** — the sole consumer for external assertion (Invariant #2). The
  Executive decides once from the merged picture; knowledge is context, never command
  (mirrors Vol XV §1.5).
- **Personality (Vol X) / Voice** — reads viewpoints and `elo_connection`/`significance` to
  shape *how* a truth is said, never *what* is true (Principle: cognition objective,
  personality shapes expression).
- **Narrative Identity (Vol XXI)** — the entity graph of the eLo universe (companions,
  stages, projects) is the shared substrate Vol XXI narrates over.

## 1.9 Open Questions (for David)

*(Re-scoped 2026-08-10: software canon is David's single L3 call — no second reviewer
required. See `CANON_RULINGS_2026-08-10.md` and Vol XXVII §1.3.1.)*

1. ~~**Canonical world graph (blocking §1.6).**~~ **DECIDED 2026-08-10 — Ruling A:**
   `relationships/world_graph.json` is CANONICAL; `identity/world_graph.json` is RETIRED
   (migrate anything unique out, then remove). No longer blocking; §1.6 stands as the record
   of why.
2. **Node id namespace.** Adopt one id convention across entity/concept/viewpoint (viewpoints
   have no `id`, only `topic`; identity/world_graph uses "eLo-OS")? Recommend snake_case `id`
   everywhere for referential integrity.
3. **Concept-network typing.** Should `related`/`opposites`/`supporting` become typed,
   id-referenced edges (like the entity graph) so the concept net is auditable, or stay as
   soft string tags? Recommend promoting to ids once the id namespace is fixed (Q2).
4. **Ontology growth authority.** Adding a new entity `type` or concept — is that David L3
   (identity-level), or delegable to the Architect under review? (Governance gate.)
5. **Self as a first-class entity.** Should eLo's Self Model (Situated Self, ADR-Exec-004)
   be represented as the `elo` entity's durable knowledge here, or kept wholly in the live
   Self Model? Boundary with Vol XV self-perception to confirm.

*Added 2026-08-10 with the person/place/event types (§1.3.5–§1.3.7):*

6. **Storage shape.** Do `Person`/`Place`/`Event` live in three new files
   (`relationships/people.json` · `places.json` · `events.json`, as specified above), or as new
   `type` values inside the existing `relationships/world_graph.json → entities[]`? Recommend
   **separate files** — different write discipline (§1.7.1), different sensitivity handling, and
   it keeps David's world from being buried inside the lore store. Builder decision to
   implement; Architect recommends; no identity implication.
7. **`relation` enum growth.** Adding a new `relation` value (or a new node `type`) is an
   ontology change — Rule 1.1.2 forbids faculties inventing them. Confirm this is **David's**
   call rather than delegable, given `relation` encodes how people stand to him. Recommend:
   David's, but a one-line yes, not a gate.
8. 🔴 **FLAGGED FOR DAVID L3 — what may eLo hold about other people?** `Person.facts[]` and
   `Event` make eLo capable of holding durable information about David's family and friends —
   people who never agreed to it. This is a **values** question and the Architect will not
   decide it. Specifically: (a) may eLo store facts about a third party that David has *not*
   explicitly stated, i.e. may Consolidation promote them at all, or is `david_stated` the only
   permitted source for people? (b) does `sensitivity: private` default to ON for every Person
   node? (c) is there any category (health, other people's relationships, anything about
   children) eLo should refuse to hold at all? Until David rules, the safe reading applies:
   **`david_stated` only, `private` by default, and no promotion of third-party facts.**
9. 🔴 **FLAGGED FOR DAVID L3 — the home address.** `Place.address` is what makes eLo useful for
   anything local and is also the most sensitive field in the graph. Confirm it may be stored at
   all, and confirm the rule "eLo may use it, never speak it unbidden" (§1.3.6). Touches
   Volume XXIII; David's call.
10. **De-emphasis, not deletion — confirm.** §1.0.1 keeps the `elo_os`/`elo_book`/`elo_game`/
    `elo_robot` nodes and the `brand`/`project` types while demoting them below David's world in
    retrieval. Confirm that is the intent, rather than retiring the parked-venture nodes
    outright. Recommend keep — they are eLo's own self-story, not just a business plan.

## 1.10 Architecture References

- Code: `knowledge/graph_loader.py` (Connection Engine), `relationships/world_graph.json`,
  `relationships/concepts.json`, `knowledge/viewpoints.json`; wiring in `server.py` +
  `runtime/spine/control_plane.py` (`_build_context_block`).
- `Volume_VIII/01_Memory_Architecture.md` — semantic memory + Consolidation (the bridge).
- `Volume_XV/01_Unified_World_State.md` — the live-world contrast + read-discipline model.
- `ARCHITECTURAL_PRINCIPLES.md` — Invariants #1 (One Brain), #2 (Executive), #3 (Verified
  Speech), #7 (Memory Ownership).

---

```
Chapter 1 — Ontology & the Knowledge Graph
Status: READY FOR REVIEW  (amended 2026-08-10 — personal-scope re-scope; NOT ratified)
Files: Volume_XXIV/01_Ontology_and_the_Knowledge_Graph.md
Live anchors wired: graph_loader.py + relationships/world_graph.json + concepts.json + viewpoints.json
Faculty Contract: Included · Node/Edge schema: Included (grounded in live JSON)
Amendment 2026-08-10: §1.0.1 personal scope + ranking rule · §1.3.5 Person · §1.3.6 Place ·
  §1.3.7 Event · §1.3.7.1 Memory-vs-Knowledge boundary · §1.7.1 write discipline for real people
Open decisions flagged: Q1 CLOSED by Ruling A · Q6 storage shape · Q7 enum authority ·
  Q8/Q9 🔴 DAVID L3 (third-party facts · home address) · Q10 keep-vs-retire parked nodes
```

READY FOR REVIEW
