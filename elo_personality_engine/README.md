# eLo Personality Engine v1.0

**Cross-platform personality and expression system for eLo AI OS.**

---

## Purpose

The eLo Personality Engine defines HOW eLo AI OS sounds and moves across all output systems.
It does not affect cognition, routing, or decision-making — those live in the kernel.

```
What the kernel does:        What this engine does:
─────────────────────        ──────────────────────
Classify input               Define tone per mode
Select routing mode          Define speech style per mode
Detect loops                 Enforce expression rules
Manage memory                Map modes to motion/avatar states
Assign state                 Build the final prompt string
```

---

## Separation from kernel

```
User input
    │
    ▼
kernel/decide_response()     ← COGNITIVE KERNEL (frozen, not touched)
    │
    ▼ mode, routing meta
    │
    ▼
eLo Personality Engine       ← THIS SYSTEM
    ├── build_elo_prompt()   builds consistent system prompt
    ├── mode_profiles.json   defines tone and speech per mode
    ├── expression_rules.json enforces global behaviour rules
    └── motion_mapping.json  maps mode → Unity / robot motion
    │
    ▼ final prompt string
    │
    ▼
Backend (Claude / offline)   ← generates response text
```

---

## Files

| File | Purpose |
|---|---|
| `version.json` | Engine version and stability |
| `personality_core.md` | Core identity — what eLo is and isn't |
| `mode_profiles.json` | Tone, speech style, question rate per mode |
| `expression_rules.json` | Global behaviour rules (forbidden patterns, etc.) |
| `motion_mapping.json` | Mode → Unity avatar + robot motion intent |
| `prompt_pipeline.py` | `build_elo_prompt()` — single prompt assembly function |
| `README.md` | This file |

---

## Cross-platform consistency

All eLo AI OS output systems read from this engine:

| System | How it uses the engine |
|---|---|
| **Claude backend** | `build_elo_prompt()` → system prompt sent to API |
| **Offline backend** | `build_elo_prompt()` → reference for framing |
| **Unity avatar** | `motion_mapping.json` → animation trigger per mode |
| **Robot system** | `motion_mapping.json` → intent + motion state per mode |

Same mode → same tone → same motion → everywhere.

---

## Key rule: CONVERSATIONAL mode

Before this engine, CONVERSATIONAL mode defaulted to philosophical recursion.

After:
- Answers the literal question first
- Does not default to "what's underneath that?"
- Asks at most one follow-up question, only if needed
- `question_rate: 0.3` (not every response needs a question)

---

## Usage

```python
from elo_personality_engine.prompt_pipeline import build_elo_prompt, get_motion_mapping

# build a system prompt
prompt = build_elo_prompt(
    mode       = "CONVERSATIONAL",
    user_input = "How are you doing today?",
    memory     = {"tone_signal": "neutral"},
    state      = {"name": "exploring"},
)

# get motion mapping for Unity
motion = get_motion_mapping("CREATIVE")
# → {"motion_state": "gentle_bounce", "posture": "lean_forward", ...}
```

---

## Editing personality

To change tone or behaviour for a mode:

1. Edit `mode_profiles.json` — change `tone`, `speech`, or `question_rate`
2. Edit `expression_rules.json` — add or remove forbidden patterns
3. Edit `personality_core.md` — update the core identity description

No code changes required. No kernel changes. No restart needed (cache clears on reload).

---

## What this is NOT

- Not an intelligence upgrade
- Not a routing change
- Not a memory modification
- Not a kernel refactor

It is a personality consistency layer. The kernel decides. The engine expresses.
