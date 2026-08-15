# Memory Engine Authority Analysis — card 0025

**Builder, 2026-08-15.** Per card 0027: produce the authority analysis first. David chooses RETIRE / ABSORB / SPLIT. No fix is made here.

---

## What `core/memory_engine.py` does

1,146 lines. Owns `memory/interactions.json` — a 895-record list of raw conversational turns.

**Per-record schema** (`{timestamp, project_tag, mode, user, response, concepts}`):
- `user` — raw input string
- `response` — eLo's response string
- `concepts` — list of matched concept-group tags (creation/narrative/identity/emotion/imagination/technical)
- `project_tag` — resolved from project_registry.json
- `mode` — CAL action at write time

**Five category system** (vs Vol VIII's four biological types):
Identity · Project · Creative · World · User ← not mapped to episodic/semantic/procedural/emotional

**Public API:**
| Function | What it does | Caller count |
|---|---|---|
| `store_interaction()` | Write one turn record to `interactions.json` | 2 live callers |
| `retrieve(query, top_k)` | Keyword-score interactions.json → top-k matches | 1 live caller |
| `retrieve_by_project(project_tag)` | Filter interactions.json by project tag | 1 live caller |
| `retrieve_structured(query, project_hint)` | Returns 4-block dict (identity/project/creative/world) | legacy path |
| `build_memory_influence(query, project_hint)` | Full influence dict for behavior/identity/avatar | 3 live callers |
| `load_registry()` | Load project_registry.json (project name → tag) | 1 live caller |
| `resolve_project(text, registry)` | Tag a turn's project from registry patterns | 1 live caller |
| `export_memory()` | Markdown export of top threads, entities, arcs | not called at runtime |
| `_load_store()` | Read interactions.json (private — accessed externally by visual_memory.py:145) | |

---

## Who calls it (non-test, live path only)

### Writes
- **`server.py:3574-3578`** — `store_interaction(raw, response, action, project_tag)` every turn, response path.
- **`core/core_engine.py:254`** — same call on the CLI path (legacy chat loop).

### Reads
- **`server.py:3378-3388`** — `retrieve()` + `retrieve_by_project()` — contextual recall before the turn response is generated.
- **`core/core_engine.py:190`** — `build_memory_influence()` — memory signals injected into system prompt.
- **`core/behavior_engine.py:183-184`** — expects `build_memory_influence()` output format.
- **`core/identity_engine.py:336`** — consumes `build_memory_influence()` output.
- **`core/avatar_bridge.py:36`** — uses memory dict for energy modifiers.
- **`core/visual_memory.py:145`** — accesses private `_load_store()` directly.

### Shims
- **`memory_engine.py` (root)** — `from core.memory_engine import *` — legacy re-export.

---

## What `interactions.json` contains

- **895 records** (as of 2026-08-15)
- Raw conversational turns — user text + eLo response — not curated summaries
- Concept tags (keyword-matched at write time)
- No weight, no decay, no significance gate, no consolidation
- Appended every turn; grows without bound

**This is NOT the same as the vault.** The vault holds:
- Curated summaries with weight 1-9 + decay
- Submitted via `MemoryFaculty.submit()` → `vault_layer.write_memory()`
- One record per *significant* event or session synthesis

`interactions.json` holds the full raw turn log. The vault holds selected, weighted durable memory. They serve different purposes.

---

## What disappears if `core/memory_engine.py` is retired

| System | Loss |
|---|---|
| `server.py` contextual recall (`retrieve()`) | eLo loses per-turn retrieval of past conversations |
| `build_memory_influence()` | behavior_engine, identity_engine, avatar_bridge lose memory-shaped prompt signals |
| project tagging (`load_registry`, `resolve_project`) | Project context not injected into turns |
| 895 historical interaction records | Full conversation history lost unless migrated |
| `core_engine.py` CLI path | Broken (legacy path calls both store and retrieve) |

If retired without migration: **eLo loses contextual recall and memory-shaped responses entirely** until equivalent paths through vault_layer are built.

---

## What is genuinely distinct vs what overlaps Vol VIII

**Overlaps (Vol VIII already does this):**
- Durable memory → vault_layer (already handles this via significance + weight)
- Episodic retrieval → `vault_layer.recall_context()` (already exists)
- Reinforcement on recall → `consolidation_faculty.reinforce()` (exists but misplaced — card 0025 P0-3)

**Genuinely distinct (not in vault):**
- **Raw conversational turn log** — the vault only receives *significant* moments; `interactions.json` records every turn. This is a different beast: an episodic scratchpad, not a curated store.
- **Keyword concept retrieval** — fast, no embeddings. Vault uses spot-code lookup. Memory engine uses keyword scoring against the raw turn text.
- **Project tag system** — `project_registry.json` → project tags per turn. No equivalent in vault.
- **build_memory_influence()** — synthesises the raw interaction log into a 4-block influence dict (identity, project, creative, world context). No equivalent in vault.

---

## The three options — honest framing

### (a) RETIRE — migrate everything into vault

`interactions.json` becomes episodic vault entries submitted via `MemoryFaculty.submit()`. `retrieve()` becomes `vault_layer.recall_context()`. `build_memory_influence()` is rebuilt against vault lookups.

**True cost:**
- All 895 records need to be migrated (or discarded) — not trivial
- Vault retrieval uses spot-codes and weight decay; keyword retrieval is qualitatively different
- `build_memory_influence()` synthesises across 4 thematic blocks — vault lookup is per-spot
- The project tagging system (`project_registry.json`) has no vault equivalent
- `behavior_engine`, `identity_engine`, `avatar_bridge` all expect `build_memory_influence()` dict format — callers change
- **Estimation: this is a 2-3 day rebuild, not a swap**

**Benefit:** one durable-memory writer. Runtime Invariant 7 satisfied. Vol VIII honest.

### (b) ABSORB — name it in Vol VIII with an explicit boundary

Vol VIII §4 is amended to say: eLo has two memory surfaces.

1. **Turn log** — `core/memory_engine.py` / `interactions.json`. Raw episodic scratchpad. Writes every turn. Concept-tagged. Not consolidated. Not weight-gated. Owned by `core/`.
2. **Durable vault** — `memory/vault_layer.py` / obsidian_vault. Curated, weighted, decaying. Significance-gated. Consolidation-scheduled. Owned by `memory/`.

Boundary rule: the vault is the **permanence layer** (survives restarts, shapes identity). The turn log is the **context layer** (shapes current turn, replaced over time by vault summaries).

AT-8 is amended: `core/memory_engine.py` is no longer listed as a "known violator" — it's a **named second surface with a documented boundary**.

**True cost:**
- Zero migration
- Vol VIII doc update (Architect lane)
- AT-8 updated to reflect the two-surface model (Builder lane — small)
- `server.py` and `core/core_engine.py` are no longer violations — they're wired correctly to their respective surfaces

**Benefit:** honest, low risk, matches what the code already does. No rebuild.

### (c) SPLIT — two explicit owners

Both surfaces exist with separate canon governance. Not recommended by the Architect; same reason as Ruling A (duplicate world-graphs — the boundary erodes).

---

## Builder's observed recommendation (for David's consideration)

**(b) ABSORB** is lowest risk and most honest. `interactions.json` is a raw episodic turn log — every turn gets a record. The vault is curated durable memory. These are genuinely different purposes, different retrieval models, different lifecycles. Calling one a "violation" of the other presupposes they should be one thing, which Vol VIII §4.113 does say — but Vol VIII wrote its invariant before the turn-log pattern was established.

The test AT-8 was structured to "FAIL until David rules" — which is correct. The failure is a deliberate flag, not a bug. Once David rules (a), (b), or (c), AT-8 is updated to match the new boundary.

---

## Builder actions taken on this card (before David's ruling)

- **AT-8 whole-repo durable-write scan**: already in `tests/test_canon_viii_memory.py`. Flags `core/core_engine.py` and `server.py` as violations (both call `store_interaction()`). Test correctly fails and stays failing until the L3 ruling. ✅
- **This analysis document**: authority map complete. David can rule. ✅
- **P0-3 (reinforce out of hot loop)**: separate from P0-1. Can be fixed without the L3 ruling. See next section.

## P0-3 — reinforce() in hot loop (separate from P0-1, fixable now)

`vault_layer.py:344` calls `reinforce()` inside `lookup()`, which runs on the response path. Vol VIII forbids durable writes in the hot loop. This is independent of the memory_engine L3 decision.

**Fix**: move `reinforce()` call behind a queue or integration-window call — fire it after the Executive has consumed the retrieved memory, not at retrieval time. See card 0025 order: `P0-1 AT-8` (done) → `P0-3 reinforce lane` (next) → `P0-2 Ruling B` (David's).
