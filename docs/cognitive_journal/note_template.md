---
# --- Identity ---
id: {{YYYY-MM-DD-NNN}}
title: "{{One sentence title, no trailing period}}"
created: {{YYYY-MM-DDTHH:MM}}
author: "{{eLo | David | Claude | Session}}"

# --- Classification ---
type: {{conversation | observation | insight | theme | decision | dream | question}}
status: open

# --- Linking ---
projects:
  - "[[{{ProjectName}}]]"
characters:
  - "[[{{CharacterName}}]]"
related_notes:
  - "[[{{YYYY-MM-DD-NNN}}]]"
session_id: "{{optional external session or conversation ID}}"

# --- Discovery ---
tags:
  - journal
  - "{{project-slug}}"
  - "{{type}}"
themes:
  - "{{named-theme-from-controlled-vocab}}"
mood: "{{energised | focused | stuck | neutral | frustrated | breakthrough}}"
confidence: "{{low | medium | high | speculative}}"

# --- Lifecycle ---
superseded_by: ""
archived: false
---

## Context

{{One to three sentences. Why does this entry exist today? What triggered it?
Include the date and time inline for scanability even though it is in frontmatter.
Example: 2026-06-06, early afternoon. [Triggering event or observation.]}}

---

## Content

{{Main body. Follow the rules for your entry type:}}

{{--- CONVERSATION ---
Paste or paraphrase the exchange. Prefix each line with the speaker:
> **eLo:** ...
> **Claude:** ...
Keep the shape of the exchange intact. Never smooth over confusion — it is data.}}

{{--- OBSERVATION ---
Describe what was seen, heard, or felt. Be specific.
Include file paths, line numbers, or scene object names when relevant.}}

{{--- INSIGHT ---
State the insight in one sentence first (bold it), then explain the reasoning
that led there. End with how it changes the approach going forward.}}

{{--- THEME ---
Name the theme in a heading, list every prior instance with wikilinks,
then describe the pattern abstractly.}}

{{--- DECISION ---
State the decision as an imperative sentence (bold it). List the forces that
drove it. End with what is now explicitly off the table.}}

{{--- DREAM ---
Free-form. No rules. Capture without filtering.}}

{{--- QUESTION ---
State the question exactly as it formed. List what is already known.
List what would need to be true for each possible answer.}}

---

## Connections

{{Explicit prose links to other notes, systems, or characters.
Use wikilinks. One sentence per link explaining the relationship.}}

- [[{{YYYY-MM-DD-NNN}}]] — {{why this prior entry is relevant}}
- [[{{TrackerOrSystemName}}]] — {{what this entry affects in that system}}
- [[{{CharacterName}}]] — {{why this character is implicated}}

---

## Open Threads

{{Bullet list of unresolved questions or follow-up actions this entry generates.
Each item is either:
  - a question (ends with ?)
  - an action (starts with a verb)
Do not delete items. If resolved, append — resolved YYYY-MM-DD: <summary> inline.}}

- {{Open question or action?}}
- {{Open question or action?}}

---

## Change Log

{{Append-only. One line per edit after initial creation.}}

- {{YYYY-MM-DDTHH:MM}} — initial entry
