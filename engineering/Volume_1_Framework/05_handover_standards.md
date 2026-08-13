# Volume 1 — Handover Standards

A handover document is written for a future Claude instance — or a human contributor — who has never seen this phase and needs to understand it cold in under 10 minutes.

---

## What Every Handover Must Contain

### 1. What This Phase Built

A functional description, not a code listing. What capability does eLo now have that it didn't have before? What cognitive function is now active?

Example (Phase 2): "eLo's Attention Faculty now observes registered cognitive streams (conversation, vision, memory, system), finds concept resonance, and produces a structured AttentionSnapshot that the Executive reads as context."

Not: "We added AttentionSnapshot, StreamDefinition, and ring buffer classes to connection_surface.py."

### 2. Files Added or Modified

A table:

| File | Status | What Changed |
|---|---|---|
| `tools/connection_surface.py` | Modified | Phase 2 complete rewrite — AttentionSnapshot, StreamDefinition, ring buffer |
| `config/concept_clusters.json` | New | 83 keyword→cluster mappings, 6 clusters |

### 3. Runtime Interfaces

Every interface the next phase will consume. Written as contracts, not descriptions.

```python
# What the next phase can call:
from tools.connection_surface import get_observation, register_stream, AttentionSnapshot

# get_observation() → AttentionSnapshot | None
# Returns None if cooldown hasn't elapsed, confidence is below threshold,
# or no resonance found.

# register_stream(name, fn, **kwargs) → None
# Adds a new cognitive stream to the registry.
# fn() → set[str] (tokens to observe)
```

### 4. What the Next Phase Must Not Break

Specific behaviours that the next phase must preserve:

- "The `__str__` output of AttentionSnapshot must remain `[ATTENTION: ...]` — server.py injects it via str()"
- "The Executive must not be modified"
- "The hybrid cooldown must remain the gating mechanism"

### 5. Known Issues

Things that are not fixed in this phase, documented honestly:

| Issue | Severity | Planned Fix |
|---|---|---|
| Vision stream vocabulary thin (app name only) | Low | Phase 3 Semantic World Model adds richer tokenisation |

### 6. What the Next Phase Should Watch Out For

Gotchas. Non-obvious constraints. Things that cost hours if not known.

---

## Handover Tone

Write as a briefing, not a specification. The reader should be able to start working within 10 minutes. If a section requires more than 2 minutes to read and understand, it's too long.

If the reader needs to know the internals, they can read the code. The handover tells them what matters without making them read everything.

---

## Handover Timing

The handover draft is written before the freeze decision. This forces the engineer to articulate what was built clearly — if they can't write a clear handover, the phase isn't ready to freeze.

After the freeze decision, the handover is updated with:
- The final freeze decision and date
- Any CONDITIONAL exceptions and which phase resolves them
