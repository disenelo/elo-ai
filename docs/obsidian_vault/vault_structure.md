# eLo OS — Obsidian Knowledge Vault

**Version**: 1.0
**Designed for**: 10+ year AI / robotics / worldbuilding project

---

## Folder Structure

```
eLo Vault/
│
├── 00 - Inbox/
│   └── (daily capture — unsorted notes, quick thoughts, links)
│
├── 01 - eLo Core/
│   ├── Identity/
│   │   ├── eLo Identity Specification.md
│   │   ├── Personality Skeleton.md
│   │   ├── Voice Profile.md
│   │   └── Behaviour Invariants.md
│   ├── Philosophy/
│   │   ├── eLo Design Principles.md
│   │   ├── Sugarcore Arc.md
│   │   └── Chunk Logic.md
│   └── Universe/
│       ├── eLo Universe Overview.md
│       ├── Entity — eLo.md
│       ├── Entity — Chunk.md
│       ├── Entity — K-7.md
│       ├── Entity — Core.md
│       └── Entity — Sugarcore.md
│
├── 02 - AI System/
│   ├── Architecture/
│   │   ├── System Overview.md
│   │   ├── Kernel Architecture.md
│   │   ├── Backend Interface Contract.md
│   │   └── Invariants.md
│   ├── Memory/
│   │   ├── Memory Engine Design.md
│   │   ├── Memory Categories.md
│   │   └── Drift Control.md
│   ├── Personality Engine/
│   │   ├── Mode Profiles.md
│   │   ├── Expression Rules.md
│   │   ├── Philosophical Control.md
│   │   └── Prompt Pipeline.md
│   ├── Backends/
│   │   ├── Claude Backend.md
│   │   ├── Mock Backend.md
│   │   ├── Local LLM Backend.md
│   │   └── Backend Router.md
│   └── Versions/
│       ├── v0.1 — Prototype.md
│       ├── v0.2 — Stable Kernel.md
│       ├── v0.3 — Unity + API.md
│       ├── v0.4 — Voice + Persistence.md
│       └── v1.0 — Stable Release.md
│
├── 03 - Robotics/
│   ├── Hardware/
│   │   ├── Orb Device Spec.md
│   │   ├── Raspberry Pi Setup.md
│   │   └── Servo + Motor Plan.md
│   ├── Software/
│   │   ├── Robot Signal Protocol.md
│   │   ├── Motor Abstraction Layer.md
│   │   ├── Safety Controller.md
│   │   └── Telemetry System.md
│   └── Phases/
│       ├── Phase 1 — Static Glowing eLo.md
│       ├── Phase 2 — Voice Reactive.md
│       └── Phase 3 — Mobile Robot.md
│
├── 04 - Unity + Game/
│   ├── Avatar/
│   │   ├── eLo Character Design.md
│   │   ├── Animation System.md
│   │   ├── Signal Receiver (C#).md
│   │   └── Motion Mapping.md
│   ├── eLo Planet/
│   │   ├── World Design.md
│   │   ├── Memory World System.md
│   │   ├── Project Islands.md
│   │   └── Level Design Notes.md
│   └── Game Design/
│       ├── Game Overview.md
│       ├── Mechanics.md
│       ├── Enemy Design.md
│       └── Narrative Structure.md
│
├── 05 - Worldbuilding/
│   ├── Narrative/
│   │   ├── Four Act Structure.md
│   │   ├── eLo Character Arc.md
│   │   └── Enemy Philosophy.md
│   ├── Lore/
│   │   ├── Sugarcore Lore.md
│   │   ├── Core Orb History.md
│   │   └── Chunk Mythology.md
│   └── Visual/
│       ├── Aesthetic Direction.md
│       ├── Colour Language.md
│       └── Motion Language.md
│
├── 06 - Voice/
│   ├── Voice Profile.md
│   ├── TTS Engine Notes.md
│   ├── Emotional Cadence.md
│   └── Recording Sessions/
│       └── (future voice session notes)
│
├── 07 - Research/
│   ├── AI Papers/
│   ├── Robotics Research/
│   ├── Game Design References/
│   └── Inspirations/
│       ├── Disney Animatronics.md
│       ├── Companion AI Examples.md
│       └── eLo Influences.md
│
├── 08 - Personal/
│   ├── Learning/
│   │   ├── Animatronics Learning Path.md
│   │   ├── Unity Learning Path.md
│   │   └── AI Development Log.md
│   ├── Decisions/
│   │   └── (major decision records)
│   └── Reflections/
│       └── (personal development notes)
│
├── 09 - Projects/
│   ├── eLo AI OS/
│   │   ├── Project Overview.md
│   │   ├── TRACKER.md (mirrored)
│   │   └── Release Log.md
│   ├── eLo Planet (Unity)/
│   │   ├── Project Overview.md
│   │   └── Session Notes/
│   └── eLo Robot/
│       ├── Project Overview.md
│       ├── BOM (Bill of Materials).md
│       └── Build Log/
│
├── 10 - Templates/
│   ├── Note Templates/
│   │   ├── T — Session Note.md
│   │   ├── T — Research Note.md
│   │   ├── T — Decision Log.md
│   │   ├── T — Entity Profile.md
│   │   ├── T — Feature Spec.md
│   │   └── T — Weekly Review.md
│   └── Dashboards/
│       ├── Home Dashboard.md
│       ├── AI System Dashboard.md
│       ├── Robot Dashboard.md
│       └── Game Dashboard.md
│
└── 99 - Archive/
    └── (retired notes — never deleted, just moved here)
```

---

## Core Note Templates

### T — Session Note

```markdown
---
tags: [session, {{domain}}]
date: {{date}}
project: {{project}}
---

# Session — {{title}}

**Date**: {{date}}
**Project**: {{project}}
**Duration**: 

## What I worked on

## What I learned

## What broke / went wrong

## Decisions made

## Next session

## Links
- [[]]
```

---

### T — Decision Log

```markdown
---
tags: [decision, {{domain}}]
date: {{date}}
status: decided
---

# Decision — {{title}}

**Date**: {{date}}
**Context**: 

## The decision

## Why this over alternatives

## Alternatives considered

| Option | Pros | Cons |
|--------|------|------|
| | | |

## Expected consequences

## Review date (if applicable)

## Links
- [[]]
```

---

### T — Feature Spec

```markdown
---
tags: [spec, {{system}}, {{status}}]
date: {{date}}
status: draft
---

# Spec — {{feature name}}

**System**: {{system}}
**Status**: draft → review → stable

## Purpose

## Requirements

### Must
-

### Must NOT
-

## Interface / API

## Acceptance criteria
- [ ]
- [ ]

## Links
- [[]]
```

---

### T — Entity Profile (eLo Universe)

```markdown
---
tags: [entity, universe, lore]
entity: {{name}}
---

# Entity — {{name}}

## What it is

## What it represents

## When to use it (as a thinking tool)

## In the AI system

## In the game

## In the robot

## Relationships
- [[Entity — eLo]]
- [[Entity — Core]]

## Evolution log
- {{date}}: first defined
```

---

### T — Research Note

```markdown
---
tags: [research, {{topic}}]
date: {{date}}
source: 
---

# Research — {{title}}

**Source**:
**Date read**:

## Key points

## Relevance to eLo

## Questions this raises

## Links
- [[]]
```

---

### T — Weekly Review

```markdown
---
tags: [review, weekly]
date: {{week-start}}
---

# Week of {{week-start}}

## What moved forward

## What stalled

## What I'm thinking about

## State of the system

## Next week priority

## Energy level this week
(1–10)
```

---

## Linking Strategy

### Core links to always make

Every note links to its **parent system note**:
- AI notes link to `[[Kernel Architecture]]` or `[[System Overview]]`
- Robot notes link to `[[Robot Signal Protocol]]` or relevant hardware note
- Game notes link to `[[Game Overview]]` or `[[World Design]]`
- Universe notes link to `[[eLo Universe Overview]]`

### Cross-domain links

When a concept appears in multiple domains, link explicitly:
- `[[Entity — Chunk]]` appears in: AI system, robot intent, game mechanics, lore
- `[[Sugarcore Arc]]` appears in: narrative, AI mode design, enemy design

### Link to decisions

Any note that results from a decision links to the decision:
```
This approach was chosen in [[Decision — CharacterController over Rigidbody]]
```

### Version links

Feature notes link to the version they shipped in:
```
First stable in [[v0.2 — Stable Kernel]]
```

---

## Tagging Strategy

### Tag hierarchy

Use nested tags (Obsidian supports `tag/subtag`):

```
#ai/kernel
#ai/memory
#ai/backend
#ai/personality

#robot/hardware
#robot/software
#robot/phase

#game/design
#game/narrative
#game/unity

#universe/entity
#universe/lore
#universe/visual

#status/active
#status/draft
#status/stable
#status/archived

#type/session
#type/decision
#type/spec
#type/research
#type/review

#domain/ai
#domain/robotics
#domain/game
#domain/worldbuilding
#domain/personal
```

### Tags to always include

Every note gets:
1. A `#type/` tag
2. A `#domain/` tag
3. A `#status/` tag if it's a spec or decision

---

## Graph Organisation Strategy

### Cluster anchors (high-connectivity hub notes)

These notes should become the central nodes of each cluster:

| Hub Note | What connects to it |
|---|---|
| `eLo Universe Overview` | All entities, all lore, game + robot + AI |
| `System Overview` | All AI system notes |
| `Robot Signal Protocol` | All robot hardware and software |
| `World Design` | All game and eLo Planet notes |
| `Personality Skeleton` | Identity, voice, expression engine |

### Colour coding (Obsidian graph groups)

Configure these in Obsidian → Graph View → Groups:

| Pattern | Colour | Meaning |
|---|---|---|
| `tag:#domain/ai` | Blue | AI system |
| `tag:#domain/robotics` | Orange | Robot |
| `tag:#domain/game` | Purple | Game/Unity |
| `tag:#domain/worldbuilding` | Green | Lore/Universe |
| `tag:#type/decision` | Red | Decisions |
| `tag:#status/archived` | Grey | Archive |

### Graph filters

For focused views, create these saved filters:

**AI Only**: show `path:02 - AI System/`
**Robot Only**: show `path:03 - Robotics/`
**Cross-domain**: show notes with 5+ links
**Active Work**: show `tag:#status/active`

---

## Scale Strategy (10+ years)

### Annual archive

At the end of each year:
1. Move completed/settled notes from active folders to `99 - Archive/{{year}}/`
2. Create a new `Session Notes/{{year}}/` subfolder
3. Write a Year Review note in `08 - Personal/Reflections/`
4. Update version notes in `02 - AI System/Versions/`

### Note hygiene

- **Inbox clears weekly** — every note in `00 - Inbox/` gets filed or deleted each Sunday
- **Orphan review quarterly** — run Orphan Notes plugin, link or archive anything unlinked for 3+ months
- **Decision review annually** — revisit all `#type/decision` notes, update status

### What never gets deleted

- Decision logs
- Entity profiles
- Version release notes
- Session notes older than 6 months

These go to `99 - Archive/` — the reasoning matters even when the outcome is superseded.

---

## Recommended Plugins

| Plugin | Purpose |
|---|---|
| Dataview | Query notes as database (project status tables, etc.) |
| Templater | Use the templates above with variable substitution |
| Calendar | Visual session note navigation |
| Graph Analysis | Find disconnected notes |
| Obsidian Git | Auto-backup vault to GitHub |
| Kanban | Project task boards inside the vault |
| Excalidraw | In-vault diagrams (system architecture, etc.) |

---

## Starting Point

Create these first — they become the foundation everything else links to:

1. `Home Dashboard.md`
2. `eLo Universe Overview.md`
3. `System Overview.md`
4. `eLo Identity Specification.md`
5. `Game Overview.md`
6. `Robot Signal Protocol.md`

Then start logging sessions daily in `00 - Inbox/` and file them weekly.
