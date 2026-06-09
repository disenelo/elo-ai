# eLo — Knowledge Graph Architecture

**Version**: 1.0
**Scope**: Dual-purpose graph supporting storytelling and AI memory

---

## Design Principle

One graph. Two lenses.

The same node can be a **narrative entity** (character, location, concept)
and a **cognitive tool** (thinking framework, AI behaviour modifier, system anchor).

Sugarcore is a villain in the story AND a state name in the AI routing system.
The graph holds both truths simultaneously.

---

## Node Types

### 1. Entity Node

A being, object, or system with identity and behaviour.

| Field | Type | Description |
|---|---|---|
| `id` | string | slug — e.g. `entity-elo` |
| `name` | string | display name |
| `type` | enum | `entity` |
| `subtype` | enum | `character` \| `system` \| `device` \| `force` |
| `role_story` | string | narrative role |
| `role_ai` | string | function in AI OS |
| `role_robot` | string | physical/hardware role |
| `tags` | list | for retrieval and filtering |

**eLo Universe entity nodes:**

```
entity-elo          character + AI identity + robot body
entity-chunk        character + AI reasoning tool + game mechanic
entity-k7           character + emotional signal layer + robot intent
entity-sugarcore    force/antagonist + AI state name + game enemy class
entity-core         object + AI navigation layer + robot hardware
```

---

### 2. System Node

A technical or architectural system within eLo AI OS, Unity, or the robot.

| Field | Type | Description |
|---|---|---|
| `id` | string | slug — e.g. `system-kernel` |
| `name` | string | display name |
| `type` | enum | `system` |
| `subtype` | enum | `ai_module` \| `game_system` \| `hardware_layer` \| `backend` |
| `status` | enum | `frozen` \| `active` \| `planned` \| `deprecated` |
| `version` | string | semver |
| `tags` | list | |

**System nodes:**

```
system-kernel             cognitive routing kernel (frozen)
system-personality-engine mode profiles + expression rules
system-memory-engine      persistent memory + influence signals
system-backend-router     failover + switching layer
system-state-engine       6-state conversational machine
system-unity-bridge       Python → Unity signal channel
system-robot-bridge       signal → motor command chain
```

---

### 3. World Node

A location, region, or space within the eLo Universe.

| Field | Type | Description |
|---|---|---|
| `id` | string | slug — e.g. `world-elo-planet` |
| `name` | string | display name |
| `type` | enum | `world` |
| `subtype` | enum | `location` \| `realm` \| `memory-space` |
| `narrative_role` | string | what happens here |
| `game_function` | string | how it works in eLo Planet |
| `memory_analog` | string | what this represents in AI memory |

**World nodes:**

```
world-elo-planet          the game world (also maps to memory graph visual)
world-sugarcore-zone      distortion regions (enemy territories)
world-core-space          navigation layer — where Core Orb operates
world-memory-islands      visual memory world (concept clusters as islands)
world-chunk-field         reconstruction zones — fragments remade here
```

---

### 4. Concept Node

An abstract idea that exists in both the narrative and the AI system.

| Field | Type | Description |
|---|---|---|
| `id` | string | slug |
| `name` | string | display name |
| `type` | enum | `concept` |
| `narrative_meaning` | string | what it means in the story |
| `ai_meaning` | string | what it means in the AI system |
| `activation_trigger` | string | when this concept becomes relevant |

**Concept nodes:**

```
concept-reconstruction    Chunk logic — fragments become new shapes
concept-distortion        Sugarcore state — overload and signal noise
concept-navigation        Core function — finding the thread when lost
concept-expression        K-7 signal — what behaviour reveals vs words
concept-exploration       eLo mode — curiosity outrunning certainty
concept-calm-as-action    core narrative principle — peace is the move
concept-overcharged       enemy philosophy — not evil, just overloaded
```

---

### 5. Project Node

An active real-world project in the eLo ecosystem.

| Field | Type | Description |
|---|---|---|
| `id` | string | slug |
| `name` | string | display name |
| `type` | enum | `project` |
| `status` | enum | `active` \| `paused` \| `complete` \| `planned` |
| `platform` | string | Python \| Unity \| Blender \| Physical |
| `linked_entities` | list | entity nodes this project realises |

**Project nodes:**

```
project-elo-ai-os         Python AI OS (this repository)
project-elo-planet        Unity game project
project-elo-robot         Physical robot build
project-disenelo-plushies Blender addon
```

---

## Relationship Types

### Story relationships

| Relationship | From → To | Meaning |
|---|---|---|
| `IS_IDENTITY_OF` | entity-elo → concept-exploration | eLo embodies exploration |
| `REPRESENTS` | entity-chunk → concept-reconstruction | Chunk represents this concept |
| `CAUSES` | concept-distortion → entity-sugarcore | distortion manifests as Sugarcore |
| `INHABITS` | entity-elo → world-elo-planet | eLo lives in eLo Planet |
| `OPPOSES` | entity-elo → entity-sugarcore | narrative tension |
| `COMPANION_OF` | entity-k7 → entity-elo | K-7 accompanies eLo |
| `GUARDS` | entity-core → world-core-space | Core holds the navigation space |
| `CORRUPTS` | entity-sugarcore → world-elo-planet | Sugarcore corrupts the world |

### AI system relationships

| Relationship | From → To | Meaning |
|---|---|---|
| `IMPLEMENTS` | system-backend-router → concept-exploration | router enables exploration-mode behaviour |
| `READS_FROM` | system-personality-engine → entity-elo | engine expresses eLo identity |
| `TRIGGERS` | concept-distortion → system-kernel | Sugarcore state → GENTLE_GROUNDED mode |
| `PROVIDES` | system-memory-engine → entity-elo | memory grounds eLo's identity |
| `MAPS_TO` | entity-chunk → concept-reconstruction | Chunk = reconstruction in AI reasoning |
| `FROZEN_AS` | system-kernel → concept-navigation | kernel routes = navigation function |

### Cross-domain relationships (story ↔ system)

| Relationship | From → To | Meaning |
|---|---|---|
| `STORY_IS` | entity-sugarcore → system-kernel.GENTLE_GROUNDED | Sugarcore narratively IS the GENTLE_GROUNDED state |
| `REALISES` | project-elo-ai-os → entity-elo | the AI OS makes eLo real |
| `VISUALISES` | world-memory-islands → system-memory-engine | memory islands = visual memory system |
| `INHABITS_SYSTEM` | entity-elo → system-kernel | eLo's cognition lives in the kernel |

### Project relationships

| Relationship | From → To | Meaning |
|---|---|---|
| `BUILDS` | project-elo-ai-os → entity-elo | OS builds the AI layer |
| `DEPICTS` | project-elo-planet → world-elo-planet | Unity depicts this world |
| `EMBODIES` | project-elo-robot → entity-elo | robot is eLo's physical form |
| `CONNECTS` | system-unity-bridge → project-elo-planet | bridge links AI to Unity |

---

## Backlink Conventions

### In Obsidian markdown

Every note that references a graph node uses the standard wikilink:

```markdown
[[entity-elo]]        ← links to the eLo entity node note
[[concept-distortion]] ← links to the distortion concept
[[system-kernel]]     ← links to the kernel system note
```

### Backlink naming rules

| Node type | Convention | Example |
|---|---|---|
| Entity | `entity-[name]` | `[[entity-chunk]]` |
| System | `system-[name]` | `[[system-memory-engine]]` |
| World | `world-[name]` | `[[world-elo-planet]]` |
| Concept | `concept-[name]` | `[[concept-reconstruction]]` |
| Project | `project-[name]` | `[[project-elo-ai-os]]` |

### Relationship backlinks

When a note describes a relationship, it declares it in frontmatter:

```yaml
---
related_to:
  - entity: entity-sugarcore
    relationship: OPPOSES
  - concept: concept-distortion
    relationship: CAUSES
---
```

### Cross-lens link marker

When a note links the story to the AI system, mark it:

```markdown
> [STORY ↔ SYSTEM] [[entity-sugarcore]] is the narrative form of [[system-kernel.GENTLE_GROUNDED]]
```

---

## Visual Graph Strategy

### Obsidian graph groups (colour coding)

Configure in Obsidian → Graph View → Groups:

| Group pattern | Colour | Represents |
|---|---|---|
| `tag:#type/entity` | Warm amber | eLo Universe characters + forces |
| `tag:#type/system` | Blue | AI OS systems and modules |
| `tag:#type/world` | Green | Locations and spaces |
| `tag:#type/concept` | Purple | Abstract ideas (dual-domain) |
| `tag:#type/project` | Orange | Real-world projects |
| `tag:#status/frozen` | Light grey | Frozen/stable nodes |
| `tag:#status/planned` | Dim grey | Future nodes |

### Node size

Node size reflects connection count (Obsidian default).
The highest-connectivity nodes should be:

```
entity-elo           ← connects to all domains
concept-distortion   ← connects story + AI + game + robot
system-kernel        ← connects to all system nodes
world-elo-planet     ← connects to story + game + memory
```

### Saved graph filters

| Filter name | Query | Purpose |
|---|---|---|
| Universe only | `tag:#type/entity OR tag:#type/concept OR tag:#type/world` | Narrative graph |
| AI system only | `tag:#type/system` | Technical graph |
| Cross-domain | notes with both `#type/entity` and `#type/system` links | Bridge nodes |
| Active work | `tag:#status/active` | Current focus |
| Frozen | `tag:#status/frozen` | What cannot change |

### Cluster layout (conceptual)

```
                        [entity-elo]
                       /      |      \
                      /       |       \
              [K-7]   [Chunk]  [Core]  [Sugarcore]
               |        |       |          |
          (emotion)  (rebuild) (nav)   (distort)
               |        |       |          |
          [system-   [system- [system-  [system-
          emotion]   memory]  kernel]   router]
               \        |       |          /
                \       |       |         /
                [project-elo-ai-os]
                        |
                [project-elo-robot]
                [project-elo-planet]
```

---

## Dual-Purpose Node Index

| Node | Story meaning | AI meaning |
|---|---|---|
| `entity-elo` | Explorer character | AI identity + personality |
| `entity-chunk` | Reconstruction being | Reasoning tool for fragmentation |
| `entity-k7` | Emotional companion | Emotional signal layer |
| `entity-sugarcore` | Overload force | GENTLE_GROUNDED routing trigger |
| `entity-core` | Navigator object | Core Orb hardware + navigation |
| `world-elo-planet` | Game world | Memory world visual (islands) |
| `world-memory-islands` | Memory geography | visual_memory.py cluster graph |
| `concept-distortion` | World corruption | AI mode condition |
| `concept-reconstruction` | Healing mechanic | Chunk logic in reasoning |
| `concept-navigation` | World traversal | Kernel routing metaphor |
| `concept-calm-as-action` | Narrative theme | Response tone principle |

---

## JSON Schema (for Python loader)

```json
{
  "nodes": [
    {
      "id": "entity-elo",
      "name": "eLo",
      "type": "entity",
      "subtype": "character",
      "role_story": "creative explorer — the protagonist",
      "role_ai": "identity layer — what the system IS",
      "role_robot": "the physical body",
      "tags": ["entity", "character", "protagonist", "identity"]
    }
  ],
  "edges": [
    {
      "from": "entity-elo",
      "to": "concept-exploration",
      "relationship": "IS_IDENTITY_OF",
      "domain": "story"
    },
    {
      "from": "entity-elo",
      "to": "system-kernel",
      "relationship": "INHABITS_SYSTEM",
      "domain": "ai"
    }
  ]
}
```

---

## Files to Create

```
memory/graph/
├── nodes/
│   ├── entity-elo.md
│   ├── entity-chunk.md
│   ├── entity-k7.md
│   ├── entity-sugarcore.md
│   ├── entity-core.md
│   ├── system-kernel.md
│   ├── system-personality-engine.md
│   ├── system-memory-engine.md
│   ├── world-elo-planet.md
│   ├── world-memory-islands.md
│   ├── concept-distortion.md
│   ├── concept-reconstruction.md
│   ├── concept-navigation.md
│   └── concept-calm-as-action.md
└── graph.json         ← machine-readable graph for Python loader
```
