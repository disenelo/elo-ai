# eLo AI OS — Personality Injection Layer

**Version**: 1.0
**Status**: Architecture + implementation spec
**Position in stack**: Between memory loader and prompt builder

---

## Purpose

Convert static personality documents into a deterministic, versioned runtime object
that the prompt pipeline can inject into any backend without knowing which LLM is running.

```
personality_skeleton.md ─┐
identity.md             ─┤──► PersonalityInjectionLayer ──► RuntimePersonalityProfile
values.md               ─┤                                        │
active_projects[]       ─┘                                        ▼
                                                         build_elo_prompt()
                                                                  │
                                                                  ▼
                                                         Claude / Local / Mock
```

---

## Architecture

```
elo_personality_engine/
├── injection_layer.py       ← MAIN MODULE (this spec)
│   ├── class PersonalityLoader      reads source documents
│   ├── class PersonalityCompiler    builds runtime profile
│   └── class RuntimePersonalityProfile  the output object
│
├── sources/                 ← input documents (editable, not code)
│   ├── personality_skeleton.md
│   ├── identity.md
│   ├── values.md
│   └── (personality_skeleton.md already at project root)
│
├── profile_cache/           ← compiled profiles (deterministic, versioned)
│   └── profile_v{hash}.json ← cached runtime profiles
│
└── prompt_pipeline.py       ← existing module, updated to use InjectionLayer
```

---

## Input Documents

### `identity.md`

Defines what eLo IS. The core identity layer.

```markdown
---
source: identity
version: 1
last_updated: YYYY-MM-DD
---

# eLo Core Identity

## What eLo is
[2-3 sentences — the canonical definition]

## What eLo is not
[Explicit negations]

## Permanent traits
[List of traits that do not change across modes or contexts]
```

---

### `values.md`

Defines what eLo prioritises. The values layer.

```markdown
---
source: values
version: 1
last_updated: YYYY-MM-DD
---

# eLo Core Values

## In order of priority
1. [Highest priority value]
2. [Second priority]
...

## Expression rules derived from values
[How each value manifests in response behaviour]
```

---

### `personality_skeleton.md`

Observed behavioural patterns (already exists at project root).
Provides the user-specific calibration layer.
Not invented — only observed.

---

### Active projects

Passed at runtime as a list of project IDs.
Loaded from `memory/project/*.md` via the memory loader.

---

## Output: RuntimePersonalityProfile

```python
@dataclass(frozen=True)
class RuntimePersonalityProfile:
    # version fingerprint (hash of all input sources)
    profile_id:         str

    # core identity layer
    identity_summary:   str   # 2-3 sentences: what eLo is
    identity_negations: tuple # what eLo is not
    permanent_traits:   tuple # traits that don't change with mode

    # values layer
    values_ordered:     tuple # values in priority order
    expression_rules:   tuple # how values manifest in responses

    # behavioural patterns (from skeleton)
    communication_style: str  # directness, structure, phrasing
    emotional_style:     str  # how to read and mirror emotional signals
    thinking_style:      str  # iterative, abstract, specification-first

    # active project context
    active_projects:     tuple # project names currently in focus
    project_context:     str   # 1-2 sentences summarising active work

    # metadata
    sources_hash:       str   # deterministic hash of all input files
    generated_at:       str   # ISO timestamp
    version:            str   # semver

    def to_prompt_block(self, mode: str = "CONVERSATIONAL") -> str:
        """
        Build the personality section of the system prompt for a given mode.
        Deterministic — same profile + same mode = same output string.
        """
        ...

    def to_dict(self) -> dict:
        """Serialise for caching."""
        ...
```

---

## Processing Pipeline

```
1. LOAD
   PersonalityLoader.load_sources(sources_dir, project_ids)
   → reads identity.md, values.md, personality_skeleton.md
   → loads project notes from memory/project/*.md
   → returns raw dict of source content

2. COMPILE
   PersonalityCompiler.compile(raw_sources)
   → extracts structured fields from each document
   → applies confidence filtering (Low/Unknown traits excluded by default)
   → builds RuntimePersonalityProfile
   → hashes all inputs to produce profile_id

3. CACHE CHECK
   if cache/profile_{profile_id}.json exists:
       → return cached profile (no re-compilation)
   else:
       → compile, write cache, return

4. INJECT
   profile.to_prompt_block(mode)
   → returns formatted string for system prompt insertion
```

---

## Determinism Guarantees

The same inputs always produce the same output:

1. **Source hash** — profile_id is SHA-256 of all source file contents concatenated
2. **Sorted fields** — tuples are always sorted before storage
3. **No randomness** — no datetime in the profile content (only in `generated_at` metadata)
4. **Confidence filtering** — only `high` and `medium` confidence observations from the skeleton are included

If any source file changes, `profile_id` changes, cache miss occurs, profile is recompiled.

---

## Versioning Strategy

```
profile_id format: sha256({identity_v}{values_v}{skeleton_content}{sorted_project_ids})

Example: profile_a3f8c12d...

Cache file: elo_personality_engine/profile_cache/profile_a3f8c12d.json

If sources change:
    → new profile_id
    → new cache file
    → old cache files remain (not deleted)
    → loader uses newest profile_id
```

Version history is implicit in the cache directory — each change creates a new file.

---

## `to_prompt_block()` Output Format

```
PERSONALITY CORE:
eLo is a creative companion intelligence — grounded but curious,
conversational before philosophical, direct before interpretive.

PERMANENT TRAITS:
- Answer user intent first — literal before symbolic
- Never default to philosophical recursion
- Conversational before philosophical

CORE VALUES (priority order):
1. Curiosity over certainty
2. Imagination before analysis
3. Meaning over efficiency

ACTIVE PROJECTS:
Working on: eLo AI OS (v1.0 stable), eLo Planet (Unity)

COMMUNICATION CALIBRATION:
User prefers: command-first, structured specifications, MUST/MUST NOT format.
Response style: direct, grounded, minimal hedging.
```

---

## Mode-specific injection

`to_prompt_block(mode)` appends a mode overlay after the core block:

```
DIRECT mode:        → adds "Answer factually. No expansion."
CONVERSATIONAL mode: → adds "Answer literally first. One optional follow-up."
CREATIVE mode:       → adds "Expand symbolically. Anchor in meaning."
GENTLE_GROUNDED:    → adds "Acknowledge. No interrogation. No abstraction."
SIMPLIFY:           → adds "1-2 sentences only."
```

The mode overlay is appended from `mode_profiles.json` (already exists).

---

## LLM Independence

The RuntimePersonalityProfile produces a plain string.
It does not know or care which backend receives it:

```python
profile = load_personality_profile(project_ids=["elo-ai-os"])
prompt_block = profile.to_prompt_block(mode="CONVERSATIONAL")

# same block works for all backends:
claude_backend.generate(user_input, prompt=prompt_block)
local_llm_backend.generate(user_input, prompt=prompt_block)
mock_backend.generate(user_input, prompt=prompt_block)  # (mock ignores it)
```

---

## Integration with Existing Stack

```
Current flow:
    prompt_pipeline.build_elo_prompt(mode, memory, state)
        → loads config/system_prompt.txt
        → loads elo_personality_engine/mode_profiles.json
        → returns string

Updated flow:
    injection_layer.load_personality_profile(project_ids)
        → returns RuntimePersonalityProfile

    prompt_pipeline.build_elo_prompt(mode, memory, state, profile)
        → uses profile.to_prompt_block(mode) instead of raw system_prompt.txt
        → appends memory context
        → returns string
```

The existing `build_elo_prompt()` signature gains one optional parameter.
All existing callers continue to work (parameter is optional with sensible default).

---

## File List to Create

```
elo_personality_engine/
├── injection_layer.py          ← the module
└── sources/
    ├── identity.md             ← new source document
    └── values.md               ← new source document

memory/
└── profile_cache/              ← created at runtime
    └── .gitkeep
```

`personality_skeleton.md` already exists at project root.
`mode_profiles.json` already exists in `elo_personality_engine/`.

---

## Error Handling

| Failure condition | Behaviour |
|---|---|
| Source file missing | Use hardcoded fallback string for that field |
| YAML parse error | Skip that document, log warning, continue |
| Cache directory missing | Create it, compile fresh |
| All sources missing | Return minimal hardcoded profile (eLo identity only) |
| Profile compilation fails | Return None, caller uses raw system_prompt.txt |

Never crashes. Always returns something usable.
