# eLo Cognitive Journal — Capture Workflow

## Entry Type Taxonomy

Each entry belongs to exactly one primary type. Secondary types may be appended as tags.

| Type | Name | When to use |
|------|------|-------------|
| `CONV` | Conversation log | A multi-turn exchange with an AI or human that produced a decision, insight, or unresolved question — or is about to be lost |
| `OBS` | Observation | Something noticed in a running system, Unity scene, or physical test that is not yet a formal bug ticket |
| `INSIGHT` | Insight | A shift in understanding, a root cause identified, or a connection made between two previously separate problems |
| `DECISION` | Decision | A choice made from among alternatives, including constraints accepted and direction changes |
| `THEME` | Recurring theme | A pattern that has surfaced three or more times — promoted from repeated entries |
| `QUESTION` | Open question | An unresolved question that needs follow-up before a decision or action can proceed |
| `MILESTONE` | Project milestone | A milestone reached, missed, or redefined |

---

## Capture Triggers

### Conversation triggers
- A multi-turn exchange with Claude, GPT, or a local LLM produces a decision, insight, or unresolved question
- A conversation is closed or context is about to be lost

### Observation triggers
- A behaviour is noticed in Unity (unexpected, confirmed, or broken) that is not yet a bug ticket
- A physical build result is logged (robot servo test, material test, print result)
- A pattern recurs across two or more sessions (same root cause hit twice, same question asked twice)

### Decision triggers
- A design direction is chosen from among alternatives
- A previous decision is reversed or superseded
- A constraint is accepted (e.g. CharacterController-only, no Rigidbody)

### Insight triggers
- A root cause is identified
- A mental model shifts (e.g. "world vs local space is the recurring root cause")
- A connection is made between two previously separate problems

### Theme triggers
- Three or more entries share a tag or subject within 14 days — promote to a recurring theme entry
- A theme is resolved or closed

### Project-event triggers
- A milestone is reached or missed
- A tracker is updated with a status change
- An external dependency is unblocked or newly blocked

---

## Step-by-Step Capture Process

### Step 1 — Choose an entry type

Identify which trigger fired and select the corresponding type from the taxonomy above.

### Step 2 — Generate the filename

```
YYYY-MM-DD_<TYPE>_<slug>.md
```

- `slug` is lowercase, hyphen-separated, max 6 words
- `date` is the date of the event, not necessarily today
- If two entries share a date and slug, append `-2`, `-3`

**Examples:**

```
2026-06-06_DECISION_no-rigidbody-constraint.md
2026-06-06_INSIGHT_world-vs-local-space.md
2026-06-06_CONV_arm-animation-fk-chain.md
2026-06-06_OBS_particle-system-world-space.md
2026-06-06_QUESTION_chunk-vehicle-attachment-method.md
2026-06-06_THEME_world-vs-local-recurring-root-cause.md
2026-06-06_MILESTONE_core-systems-complete.md
```

### Step 3 — Write the front matter

All entries use YAML front matter. Required fields are marked R; conditional fields marked C.

```yaml
---
id: <TYPE>-YYYYMMDD-<slug>           # R — stable unique identifier
date: YYYY-MM-DD                      # R — event date
created: YYYY-MM-DDTHH:MM:SS         # R — file creation timestamp
type: <TYPE>                          # R — one of the taxonomy values above
project:                              # R — list, at least one
  - <project-tag>
status: open | closed | superseded   # R
supersedes: <id or null>             # C — if this replaces an earlier entry
superseded_by: <id or null>          # C — filled in when a newer entry replaces this one
tags: []                             # R — namespace/term tags
summary: <one sentence>             # R — written by author, not generated
source: human | ai-assisted | ai-generated   # R
ai_tool: <tool name or null>         # C — if source is ai-assisted or ai-generated
---
```

### Step 4 — Write the body

Each type has a required body structure. Use only the structure for the type chosen in Step 1.

**CONV**
```markdown
## Context
<What was being worked on. What question was posed.>

## Exchange Summary
<Condensed record of what was discussed. Key back-and-forth preserved verbatim where load-bearing.>

## Outcomes
- Decisions made: <list or "none">
- Questions opened: [[QUESTION-...]] or "none"
- Insights surfaced: [[INSIGHT-...]] or "none"

## Raw Transcript
<Optional. Paste full transcript under a collapsible block if long.>
```

**OBS**
```markdown
## What was observed
<Exact behaviour, including file, component, context.>

## Conditions
<Unity version, scene, platform, input state — whatever is relevant.>

## Interpretation
<What this suggests. Leave blank if unknown — do not invent.>

## Follow-up
- [ ] <action or question>
```

**INSIGHT**
```markdown
## The insight
<One clear statement of the new understanding.>

## What led to it
<The chain of observations or conversations that produced this.>

## Implications
<What this changes in approach, code, or design.>

## Related entries
<[[links]] to the entries this insight resolves or connects.>
```

**DECISION**
```markdown
## Decision
<State the decision in one sentence.>

## Alternatives considered
| Option | Reason rejected |
|--------|----------------|
| ...    | ...            |

## Rationale
<Why this option was chosen.>

## Constraints accepted
<Any constraints this decision locks in permanently.>

## Reversibility
<Can this be undone? Under what conditions?>
```

**THEME**
```markdown
## Theme statement
<Name the recurring pattern in one sentence.>

## First seen
<Date and [[link]] to earliest entry.>

## Instances
| Date | Entry | Notes |
|------|-------|-------|
| ...  | [[]]  | ...   |

## Status
open | resolved | accepted-constraint

## Resolution
<Fill in when status changes to resolved.>
```

**QUESTION**
```markdown
## Question
<State the question precisely.>

## Why it matters
<What decision or insight depends on this.>

## Attempts so far
- <date>: <what was tried>

## Resolution
<Fill in when answered. Set status to closed.>
```

**MILESTONE**
```markdown
## Milestone
<Name of the milestone.>

## Outcome
reached | missed | redefined

## Date planned / date actual
Planned: YYYY-MM-DD
Actual: YYYY-MM-DD or pending

## Notes
<What changed, what was learned.>
```

### Step 5 — Link forward and backward

Before saving, check for:

- Any existing open QUESTION entries this entry answers — add `superseded_by` to the question, set its status to `closed`
- Any DECISION entries this entry contradicts — add `supersedes` to this entry, add `superseded_by` to the old one
- Any THEME entries this entry is an instance of — add the entry to the theme's Instances table

### Step 6 — Append to the master index

The file `_index.md` at the journal root is append-only. Each new entry adds one line:

```
| 2026-06-06 | DECISION | no-rigidbody-constraint | [[2026-06-06_DECISION_no-rigidbody-constraint]] | eLo-Planet | open |
```

Never sort, never delete, never rewrite rows. Only append.

---

## Tag Reference

Tags follow a two-level namespace: `<domain>/<term>`. Check `_tag-registry.md` before coining a new tag.

| Namespace | Tags | Notes |
|-----------|------|-------|
| `system/` | `animation`, `weapons`, `player`, `hud`, `world-traversal`, `vfx`, `physics`, `ai-brain`, `memory` | Code systems and subsystems |
| `character/` | `elo`, `k7`, `chunk`, `enemy` | Specific named characters |
| `root-cause/` | `world-vs-local`, `stale-cache`, `timing`, `reference-null`, `layer-conflict` | Recurring technical root causes |
| `process/` | `append-only`, `versioning`, `capture-gap`, `decision-reversal` | Process and workflow concerns |
| `phase/` | `kickstarter`, `prototype`, `alpha`, `robot-phase1` | Project phase at time of entry |
| `status/` | `open`, `closed`, `superseded`, `needs-evidence` | Entry lifecycle |

When a new tag is coined, append it to `_tag-registry.md`:

```
| <namespace/term> | YYYY-MM-DD | <one-line description> | <first entry id> |
```

Never delete tags from the registry. If a tag is retired, mark it `deprecated` and note what replaced it.

---

## Project Tags

Each entry declares one or more project tags in its `project:` front-matter list.

| Tag | Covers |
|-----|--------|
| `elo-planet` | Unity game — all systems, scenes, characters, weapons, world traversal |
| `elo-robot` | Physical animatronic — servo, shell, electronics, AI brain |
| `elo-ai-os` | eLo AI OS cognitive layer — memory architecture, journal system, AI tooling |
| `disenelo-plushies` | Blender sewing-pattern addon |
| `disenelo-cross` | Decisions or insights that span multiple projects |

---

## Linking Conventions

- Link to other entries using Obsidian wiki-link syntax: `[[YYYY-MM-DD_TYPE_slug]]`
- The `id` field (e.g. `DECISION-20260606-no-rigidbody-constraint`) is the stable linking key across front matter references (`supersedes`, `superseded_by`)
- Wiki-links in body text use the filename without `.md`
- The `_index.md` is the authoritative ordered log — the only file consulted to answer "what entries exist and in what order were they created"
- Entry files are write-once after creation. The only permitted post-creation mutation is marking a file superseded (updating `superseded_by`, `status`, and appending a comment line at the end of the file)
- If a correction must be made to body content, create a new entry of the same type with `supersedes` pointing to the original — do not edit the original body

---

## Vault Layout

```
Journal/
├── _index.md                          <- append-only master index
├── _tag-registry.md                   <- all known tags with descriptions
├── 2026-06-06_DECISION_no-rigidbody-constraint.md
├── 2026-06-06_INSIGHT_world-vs-local-space.md
├── 2026-06-06_CONV_arm-animation-fk-chain.md
└── ...

Projects/
├── eLo-Planet.md
├── eLo-Robot.md
├── eLo-AI-OS.md
└── DISENELO-Plushies.md

Templates/
├── CONV.md
├── OBS.md
├── INSIGHT.md
├── DECISION.md
├── THEME.md
├── QUESTION.md
└── MILESTONE.md
```
