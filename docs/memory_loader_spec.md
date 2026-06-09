# eLo AI OS — Memory Loader Design Specification

**Version**: 1.0
**Status**: Design — no implementation yet
**Purpose**: Read Obsidian markdown files and build session context for eLo AI OS

---

## Problem Statement

eLo needs persistent memory across sessions without a cloud database.
Memory lives in an Obsidian vault as markdown files.
At session start, a Python loader reads those files and builds a context block
that gets injected into the system prompt.

**Constraints:**
- No cloud AI
- No external database
- Works offline
- Markdown files are the source of truth
- Adding a memory note = adding a `.md` file to the vault

---

## Folder Structure

```
core/
└── memory/
    ├── __init__.py
    ├── loader.py            ← main entry point
    ├── parser.py            ← frontmatter + body extraction
    ├── scanner.py           ← vault file discovery
    ├── matcher.py           ← topic matching for priority-2 loading
    ├── formatter.py         ← builds context block string
    ├── summariser.py        ← creates compact note summaries
    └── models.py            ← data classes (MemoryNote, MemoryContext)

memory/                      ← the vault (populated by user in Obsidian)
├── long_term/
├── character/
├── project/
├── world/
├── technical/
└── personal/
```

---

## Module Responsibilities

### `models.py`

Defines the data structures. No logic.

```
MemoryNote
    path:          str         file path on disk
    memory_type:   str         long_term | project | character | world | technical | personal
    title:         str         from frontmatter or filename
    tags:          list[str]   from frontmatter tags list
    backlinks:     list[str]   from frontmatter linked_to list
    category:      str         subcategory within the memory type
    load_priority: int         1 = always, 2 = topic match, 3 = on request
    active:        bool        false = archived, not loaded
    confidence:    str         high | medium | low | unknown
    body:          str         full markdown body text
    created:       str         ISO date string
    updated:       str         ISO date string
    version:       int         how many times this note has been revised

MemoryContext
    notes:         list[MemoryNote]   all loaded notes for this session
    context_text:  str                formatted string for system prompt injection
    total_chars:   int                length of context_text
    load_time_ms:  int                how long the scan took
```

---

### `parser.py`

Extracts data from a single markdown file. Handles YAML frontmatter.

**Inputs:**
- Raw file content (string)
- File path (for fallback title)

**Outputs:**
- `dict` of metadata fields from frontmatter
- `str` body text (everything after the frontmatter block)

**Behaviour:**
- Handles missing frontmatter gracefully (returns empty dict)
- Handles malformed YAML lines gracefully (skips them)
- Parses: string, int, bool, list values
- Does not crash on any input — always returns a result

**Does NOT:**
- Render markdown
- Follow links
- Make any system calls

---

### `scanner.py`

Discovers all memory note files in the vault.

**Inputs:**
- `vault_path: str` — root directory of the vault's memory folder

**Outputs:**
- `list[MemoryNote]` — all valid, active memory notes found

**Behaviour:**
- Recursively walks `vault_path`
- Skips files that do not end in `.md`
- Skips files with no `memory_type` frontmatter field
- Skips files with `active: false`
- Calls `parser.py` on each file
- Returns list of `MemoryNote` objects

**Edge cases:**
- Vault path does not exist → returns empty list
- File cannot be read → skip silently
- Frontmatter is malformed → skip the file

---

### `matcher.py`

Decides which priority-2 notes are relevant to the current user input.

**Inputs:**
- `user_input: str` — the current user message
- `notes: list[MemoryNote]` — all scanned notes

**Outputs:**
- `list[MemoryNote]` — the subset of priority-2 notes that match

**Matching strategy:**
1. Extract meaningful words from user_input (remove stopwords, short words)
2. For each priority-2 note, check if any extracted word appears in:
   - The note's `tags`
   - The note's `category`
   - The note's `title`
3. Return notes where at least one word matches

**Does NOT:**
- Use embeddings
- Use fuzzy matching
- Make external calls
- Change note content

---

### `summariser.py`

Creates compact summaries of individual notes for the context block.

**Inputs:**
- `note: MemoryNote`
- `max_chars: int` (default 400)
- `mode: str` — "summary" | "full"

**Outputs:**
- `str` — a compact text representation of the note

**Summary format:**
```
**[Title]**: [First meaningful paragraph or sentence]
```

**Full format:**
Returns up to `max_chars` of the body text.

**Behaviour:**
- Strips markdown headers from the summary
- Ignores blank lines
- Does not truncate mid-word

---

### `formatter.py`

Assembles the final context block from a set of loaded notes.

**Inputs:**
- `notes: list[MemoryNote]`
- `max_total_chars: int` (default 3000)
- `full_body: bool` (default False)

**Outputs:**
- `str` — the formatted context block

**Output format:**
```
[MEMORY: Long Term]
**[Title]**: [Summary]
**[Title]**: [Summary]

[MEMORY: Character]
**[Title]**: [Summary]

[MEMORY: Project]
**[Title]**: [Summary]
```

**Behaviour:**
- Groups notes by `memory_type`
- Orders groups: long_term → character → personal → project → world → technical
- Truncates to `max_total_chars` at a section boundary, not mid-note
- Adds section headers for each memory type present
- Returns empty string if no notes

---

### `loader.py`

The main entry point. Coordinates the other modules.

**Public functions:**

```
load_memory(
    vault_path:  str  = None,   # default: ELO_VAULT_PATH env var or memory/
    user_input:  str  = "",     # current user message
    max_chars:   int  = 3000,
    full_body:   bool = False,
) → str

load_memory_section(
    memory_type: str,            # load one specific type
    vault_path:  str  = None,
    max_chars:   int  = 1000,
) → str

scan_vault(
    vault_path:  str  = None,
) → list[MemoryNote]
```

**Flow:**

```
load_memory(vault_path, user_input, max_chars)
    │
    ├── scanner.scan_vault(vault_path)
    │       → list[MemoryNote] (all active notes)
    │
    ├── [priority 1] take all notes where load_priority == 1
    │
    ├── [priority 2] matcher.match(user_input, priority_2_notes)
    │       → list[MemoryNote] (topic-matched subset)
    │
    ├── formatter.format(priority_1 + matched_priority_2, max_chars)
    │       → str context block
    │
    └── return context_block
```

---

## Data Flow

```
Obsidian Vault (markdown files on disk)
        │
        │  read + parse frontmatter
        ▼
    scanner.py + parser.py
        │
        │  list[MemoryNote]
        ▼
    [priority 1]          [priority 2]            [priority 3]
    always load           match to user_input      on request only
        │                        │                        │
        └────────────────────────┘                        │
                     │                              load_memory_section()
                     │  list[MemoryNote] (filtered)
                     ▼
              formatter.py
                     │
                     │  context block string
                     ▼
    elo_personality_engine/prompt_pipeline.py
                     │
                     │  injected into system prompt
                     ▼
              Backend (Claude / Mock)
                     │
                     ▼
              Response to user
```

---

## Configuration

| Setting | Source | Default |
|---|---|---|
| Vault path | `ELO_VAULT_PATH` env var | `memory/` in project root |
| Max context chars | `load_memory(max_chars=...)` | 3000 |
| Full body mode | `load_memory(full_body=True)` | False (summary only) |

---

## Metadata Schema (frontmatter)

Every memory note must have at minimum:

```yaml
---
memory_type: [long_term | project | character | world | technical | personal]
load_priority: [1 | 2 | 3]
active: [true | false]
---
```

Optional but recommended:

```yaml
title: [human-readable title]
tags: [list, of, tags]
linked_to: [list, of, note, titles]
category: [subcategory]
confidence: [high | medium | low | unknown]
created: YYYY-MM-DD
updated: YYYY-MM-DD
version: 1
```

---

## Tag Extraction

Tags are read from the frontmatter `tags` list.
They are used by `matcher.py` for topic matching.

Format: `tags: [memory, project, elo-ai-os, state]`

Inline tags (`#tag` in body text) are not extracted in v1.
This may be added in v2.

---

## Backlink Extraction

Backlinks are read from the frontmatter `linked_to` list.
They represent intentional links between memory notes.

Format: `linked_to: [elo-identity, system-invariants]`

Wiki-style links (`[[Note Title]]` in body text) are not followed in v1.
This may be added in v2 for graph traversal.

---

## Memory Summary Generation

Each note is summarised by taking:
1. The `title` from frontmatter
2. The first non-blank, non-header line from the body

Result: `**Title**: First meaningful sentence.`

This keeps the context block compact while preserving the key fact.

---

## Context Block Format

The context block is designed to be clear to any language model:

```
[MEMORY: Long Term]
**eLo is not an assistant**: eLo is a creative companion intelligence — a thinking partner.
**Kernel is frozen at v1.0**: The cognitive kernel must not be modified.

[MEMORY: Character]
**eLo Identity**: eLo is grounded but curious. Conversational before philosophical.
**Entity — Chunk**: Reconstruction — fragments don't return to original shape.

[MEMORY: Personal]
**User communication style**: Commands first. Specifications as structured blocks.
```

---

## Error Handling Strategy

| Error condition | Behaviour |
|---|---|
| Vault path does not exist | Return empty string — no crash |
| File cannot be read | Skip file silently |
| Frontmatter is malformed | Skip file silently |
| Note has no `memory_type` | Skip file — not a memory note |
| note has `active: false` | Skip file |
| Context exceeds max_chars | Truncate at section boundary |

The loader must never crash the main conversation loop.
All failures produce a shorter context, not an exception.

---

## Startup Integration

At session start in `main.py`:

```python
from core.memory_loader import load_memory

vault_context = load_memory(user_input="")  # priority 1 only at start
# vault_context is injected into the system prompt via prompt_pipeline.py
```

Per-turn (optional, for topic-aware loading):

```python
vault_context = load_memory(user_input=user_input)  # priority 1 + matched priority 2
```

---

## Out of Scope (v1)

- Inline `#tag` parsing from body text
- `[[Wiki link]]` traversal
- Semantic/embedding-based matching
- Writing back to the vault
- Graph analysis
- Full-text search
- Vault sync or watching for file changes
