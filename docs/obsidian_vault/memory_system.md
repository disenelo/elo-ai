# eLo AI OS — Obsidian Memory System

**Goal**: eLo loads long-term memory from markdown files. No cloud AI required.
The vault is the memory. Python reads it at session start.

---

## Folder Structure

```
eLo Vault/
└── memory/
    ├── long_term/          ← persistent facts about the world and self
    ├── project/            ← per-project state and decisions
    ├── character/          ← eLo's identity, personality, entity profiles
    ├── world/              ← eLo Universe lore, locations, rules
    ├── technical/          ← architecture decisions, system specs, version history
    └── personal/           ← user patterns, preferences, relationship to eLo
```

---

## Metadata Schema (YAML frontmatter)

Every memory note uses this frontmatter:

```yaml
---
memory_type: long_term | project | character | world | technical | personal
category: [subcategory string]
title: [human-readable title]
confidence: high | medium | low | unknown
created: YYYY-MM-DD
updated: YYYY-MM-DD
version: [int — increments on each update]
tags: [list]
linked_to: [list of note titles or IDs]
load_priority: 1 | 2 | 3   # 1 = always load, 2 = load if relevant, 3 = load on request
active: true | false        # false = archived, not loaded by default
---
```

---

## 1. Long-Term Memory

**Folder**: `memory/long_term/`
**Purpose**: Facts that remain true across all sessions and projects.

### Template

```markdown
---
memory_type: long_term
category: fact
title: [fact title]
confidence: high
created: YYYY-MM-DD
updated: YYYY-MM-DD
version: 1
tags: [long-term, fact, [domain]]
linked_to: []
load_priority: 1
active: true
---

# [Title]

## What is known

[The fact, stated plainly.]

## Source

[Where this was observed or decided.]

## Confidence note

[Why this confidence level was assigned.]

## Revision history

- YYYY-MM-DD v1: [initial entry]
```

### Example notes

- `what-elo-is.md` — eLo is a creative companion intelligence, not an assistant
- `kernel-is-frozen.md` — cognitive kernel must not be modified in v1.0
- `user-communication-style.md` — commands first, specifications as structured blocks

---

## 2. Project Memory

**Folder**: `memory/project/`
**Purpose**: State of each active project — what exists, what's decided, what's next.

### Template

```markdown
---
memory_type: project
category: [project-name]
title: [Project Name] — State
confidence: high
created: YYYY-MM-DD
updated: YYYY-MM-DD
version: 1
tags: [project, [project-name], state]
linked_to: []
load_priority: 1
active: true
---

# [Project Name]

## Current status

[One paragraph — what exists and works right now.]

## Active threads

- [ ] [Next action]
- [ ] [Open question]

## Completed

- [x] [What's done]

## Key decisions

| Decision | Rationale | Date |
|----------|-----------|------|
| | | |

## Blocked by

[What's blocking progress, if anything.]

## Last session summary

[What happened last time this was worked on.]
```

### One file per project

- `elo-ai-os.md` — Python AI OS project
- `elo-planet-unity.md` — Unity game project
- `elo-robot.md` — physical robot build
- `disenelo-plushies.md` — Blender addon

---

## 3. Character Memory

**Folder**: `memory/character/`
**Purpose**: eLo's identity, personality, and the eLo Universe entities.

### Template — eLo Identity

```markdown
---
memory_type: character
category: identity
title: eLo Identity
confidence: high
created: YYYY-MM-DD
updated: YYYY-MM-DD
version: 1
tags: [character, identity, elo]
linked_to: [personality-skeleton, voice-profile]
load_priority: 1
active: true
---

# eLo Identity

## What eLo is

[Core definition — 2–3 sentences max.]

## What eLo is not

[Explicit negations — 3–5 points.]

## Permanent traits

[Traits that do not change across modes or contexts.]

## Mode behaviour

| Mode | Tone | Style |
|------|------|-------|
| DIRECT | | |
| CONVERSATIONAL | | |
| CREATIVE | | |
| GENTLE_GROUNDED | | |
| SIMPLIFY | | |
```

### Template — Entity Profile

```markdown
---
memory_type: character
category: entity
title: Entity — [Name]
confidence: high
created: YYYY-MM-DD
updated: YYYY-MM-DD
version: 1
tags: [character, entity, universe, [name]]
linked_to: [elo-universe-overview]
load_priority: 2
active: true
---

# Entity — [Name]

## What it represents

[One paragraph — the concept this entity names.]

## As a thinking tool

[When and how to invoke this entity in conversation.]

## In the AI system

[How this entity maps to system behaviour.]

## In the game

[Role in eLo Planet.]

## In the robot

[Physical expression / behaviour mapping.]
```

### Files

- `elo-identity.md`
- `personality-skeleton.md` (import from existing)
- `entity-elo.md`
- `entity-chunk.md`
- `entity-k7.md`
- `entity-core.md`
- `entity-sugarcore.md`

---

## 4. World Memory

**Folder**: `memory/world/`
**Purpose**: eLo Universe lore, rules, locations, narrative.

### Template

```markdown
---
memory_type: world
category: lore | location | rule | narrative
title: [Title]
confidence: high
created: YYYY-MM-DD
updated: YYYY-MM-DD
version: 1
tags: [world, [category], universe]
linked_to: []
load_priority: 2
active: true
---

# [Title]

## What it is

[Description.]

## Rules that govern it

[Any rules or constraints.]

## Connections

[What it links to in the world.]

## In the game

[Gameplay relevance.]

## In the AI

[How it influences eLo's behaviour or language.]
```

### Files

- `elo-universe-overview.md`
- `sugarcore-lore.md`
- `chunk-mythology.md`
- `core-orb-history.md`
- `world-rules.md` — "everything can become symbolic", etc.

---

## 5. Technical Memory

**Folder**: `memory/technical/`
**Purpose**: Architecture decisions, system specifications, version history.

### Template — Architecture Decision

```markdown
---
memory_type: technical
category: decision | spec | constraint | version
title: [Title]
confidence: high
created: YYYY-MM-DD
updated: YYYY-MM-DD
version: 1
tags: [technical, [category], [system]]
linked_to: []
load_priority: 2
active: true
---

# [Title]

## The decision / specification

[What was decided or specified.]

## Why

[Rationale.]

## Constraints it creates

[What this locks in or prevents.]

## Superseded by

[Leave blank unless this decision was later overridden.]
```

### Files

- `kernel-is-frozen.md`
- `charactercontroller-not-rigidbody.md`
- `no-eyes-expression-through-posture.md`
- `elo-is-not-an-assistant.md`
- `version-history.md`

---

## 6. Personal Memory

**Folder**: `memory/personal/`
**Purpose**: User patterns, preferences, relationship to eLo, communication style.

### Template

```markdown
---
memory_type: personal
category: pattern | preference | context
title: [Title]
confidence: medium
created: YYYY-MM-DD
updated: YYYY-MM-DD
version: 1
tags: [personal, [category]]
linked_to: [personality-skeleton]
load_priority: 1
active: true
---

# [Title]

## Observed pattern

[What was observed — stated factually, no interpretation.]

## Evidence

[2–3 specific examples from sessions.]

## Confidence note

[Why this confidence level.]

## How eLo should use this

[Practical implication for response style.]
```

### Files

- `communication-style.md`
- `emotional-expression-style.md`
- `thinking-style.md`
- `project-behaviour.md`

---

## Tag System

```
#memory/long-term
#memory/project
#memory/character
#memory/world
#memory/technical
#memory/personal

#priority/1    ← always load at session start
#priority/2    ← load if topic is relevant
#priority/3    ← load on explicit request only

#confidence/high
#confidence/medium
#confidence/low
#confidence/unknown

#status/active
#status/archived
#status/draft

#domain/ai
#domain/robotics
#domain/game
#domain/universe
#domain/personal
```

---

## Backlink Strategy

### Every note links to

1. Its **memory type hub** — e.g. all entity notes link to `[[eLo Universe Overview]]`
2. Any note it was derived from — e.g. `personality-skeleton.md` links to session notes
3. Any note it directly affects — e.g. `kernel-is-frozen.md` links to `system-invariants.md`

### Hub notes (high-link targets)

| Hub | What links to it |
|---|---|
| `eLo Universe Overview` | All entities, all world notes, AI + robot + game |
| `eLo Identity` | Personality skeleton, voice profile, entity-elo |
| `eLo AI OS — State` | All technical decisions, all version notes |
| `Personality Skeleton` | All personal memory notes |

### Cross-memory links

When a fact appears in multiple memory types, link explicitly:
```
Entity — Chunk appears in: [[entity-chunk.md]] ← [[world/chunk-mythology.md]] ← [[technical/chunk-logic-ai.md]]
```

---

## Retrieval Strategy

### Python loader: how eLo reads memory

At session start, `memory_loader.py` reads the vault and builds a context block:

**Step 1 — Load priority 1 notes** (always)
- All `load_priority: 1` and `active: true` notes
- These become the permanent context layer

**Step 2 — Load priority 2 notes** (if relevant)
- Parse the user's first message for topic signals
- Match against `tags` and `category` fields in priority 2 notes
- Load matching notes

**Step 3 — Load priority 3 notes** (on explicit request)
- User asks about a specific topic
- Loader searches by `title` and `tags`

### Context block format

The loader builds this string and prepends it to the system prompt:

```
[MEMORY: Long-term]
eLo is a creative companion intelligence, not an assistant.
The kernel is stable and must not be modified.

[MEMORY: Character]
eLo identity: grounded but curious, conversational before philosophical.
Entity Chunk: reconstruction — fragments don't return to original shape.

[MEMORY: Project — eLo AI OS]
Status: v1.0 stable. Kernel frozen. Backend layer active.
Active threads: personality engine, mock backend, Obsidian vault.

[MEMORY: Personal]
Communication style: command-first, structured specs, MUST/MUST NOT format.
```

### Loader pseudocode

```python
def load_memory(vault_path, user_input="", max_tokens=2000):
    notes = scan_vault(vault_path)
    
    # always load
    priority_1 = [n for n in notes if n.priority == 1 and n.active]
    
    # topic-relevant
    topics = extract_topics(user_input)
    priority_2 = [n for n in notes if n.priority == 2 and n.active
                  and any(t in n.tags for t in topics)]
    
    # build context block (truncated to max_tokens)
    context = format_memory_block(priority_1 + priority_2)
    return context[:max_tokens]
```

---

## Implementation: memory_loader.py

See `core/memory_loader.py` in the eLo AI OS repository.
Reads vault at: path configurable via `ELO_VAULT_PATH` env var.
Falls back to `memory/` directory in project root if vault not set.
