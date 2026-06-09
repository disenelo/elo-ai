# eLo AI OS — Local Intelligence Architecture

**Version**: 1.0
**Status**: Design document — kernel unchanged

---

## Principle

The cognitive kernel decides. The intelligence layer generates.

These two responsibilities are strictly separated.
Swapping the intelligence source never touches the kernel.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER INPUT                                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              COGNITIVE KERNEL  (frozen — never modified)         │
│                                                                  │
│  classify_input()  →  route()  →  loop_filter()                 │
│                                                                  │
│  Output: mode + meta (DIRECT | CREATIVE | GENTLE_GROUNDED ...)  │
└──────────────────────────┬──────────────────────────────────────┘
                           │  mode + context (StateBus)
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              BACKEND ROUTER   (backend_router.py)                │
│                                                                  │
│  Mode: auto | claude | local | deterministic                     │
│                                                                  │
│  1. Try primary backend                                          │
│  2. On failure → try fallback                                    │
│  3. On fallback failure → safe string                            │
│                                                                  │
│  NEVER raises. NEVER leaks errors to user.                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┬───────────────┐
           │               │               │               │
           ▼               ▼               ▼               ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ DETERMINISTIC│  │  LOCAL LLM   │  │  CLAUDE API  │  │    FUTURE    │
│   BACKEND    │  │   BACKEND    │  │   BACKEND    │  │   BACKEND    │
│              │  │              │  │              │  │              │
│ • always on  │  │ Ollama       │  │ Anthropic    │  │ (stub)       │
│ • no network │  │ LM Studio    │  │ claude-      │  │              │
│ • rule-based │  │ llama.cpp    │  │ sonnet-4-6   │  │              │
│ • mock pools │  │              │  │              │  │              │
└──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘
           │               │               │
           └───────────────┴───────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│          PERSONALITY ENGINE   (elo_personality_engine/)          │
│                                                                  │
│  build_elo_prompt(mode, memory, state)                           │
│  Injects: mode profile + expression rules + memory context       │
│                                                                  │
│  Output: system prompt string sent to backend                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │  response_text
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    USER OUTPUT                                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Backend Interfaces

All backends implement `BaseBackend` from `backends/base_backend.py`.

### Required interface

```python
class BaseBackend(ABC):

    NAME:         str   # unique identifier
    VERSION:      str   # semver
    DESCRIPTION:  str   # one-line description
    REQUIRES_KEY: bool  # True if external key or server needed

    @abstractmethod
    def generate_response(
        self,
        user_input: str,     # raw user text
        mode:       str,     # kernel routing mode
        context:    dict,    # StateBus.to_context()
        memory:     dict,    # memory influence signals
        state:      dict,    # state snapshot
        identity:   dict,    # identity snapshot
    ) -> BackendResponse:    # {"response_text": str}

    def is_available(self) -> bool:   # key/server check
    def on_load(self):                # setup hook
    def on_unload(self):              # teardown hook
```

### Backend specifications

#### 1. Deterministic Backend (`backends/offline_backend.py`)

```
Purpose:      Always-on baseline. Works without any model.
Availability: Always True — no dependencies
Mechanism:    Rule-based response pools keyed by input pattern and mode
Output:       Deterministic — same input always returns same output
Latency:      <1ms
Use case:     Testing, development, API unavailability, default fallback
```

#### 2. Local LLM Backend (`backends/local_llm_adapter.py`)

```
Purpose:      Open-source model via local inference server
Availability: Server running at ELO_LOCAL_MODEL_URL
Mechanism:    OpenAI-compatible chat completions API (HTTP POST)
Models:       Ollama (llama3, mistral), LM Studio, llama.cpp server
Latency:      500ms–10s depending on model and hardware
Use case:     Privacy-first, offline-capable, no API cost
Config:
    ELO_LOCAL_MODEL_URL   default: http://localhost:11434/v1/chat/completions
    ELO_LOCAL_MODEL_NAME  default: llama3
```

#### 3. Claude Backend (`backends/claude_backend.py`)

```
Purpose:      Primary high-quality language generation
Availability: ANTHROPIC_API_KEY environment variable set
Mechanism:    Anthropic SDK, claude-sonnet-4-6 by default
Latency:      800ms–3s
Use case:     Best response quality, production use
Config:
    ANTHROPIC_API_KEY  required
    ELO_MODEL          default: claude-sonnet-4-6
```

#### 4. Future Backend (stub)

```
Purpose:      Placeholder for integrations not yet implemented
Examples:     OpenAI, Gemini, Cohere, custom fine-tuned model
Mechanism:    Extend BaseBackend, register in BackendRegistry
Latency:      Unknown
Use case:     Future extensibility
```

---

## Switching Strategy

### Manual switching (CLI)

```
/backend auto          # default: try Claude → local → deterministic
/backend claude        # force Claude API
/backend local         # force local LLM
/backend deterministic # force offline deterministic
```

### Programmatic switching (Python)

```python
from backends.backend_router import set_backend_mode

set_backend_mode("auto")          # auto-failover chain
set_backend_mode("claude")        # force Claude
set_backend_mode("local")         # force local LLM
set_backend_mode("deterministic") # force offline
```

### Startup auto-detection

`main.py` detects available backends at startup in priority order:

```
1. ANTHROPIC_API_KEY set?
   → yes: mode = "auto" (Claude primary, deterministic fallback)
   → no:  continue

2. ELO_LOCAL_MODEL_URL server reachable?
   → yes: mode = "local" (local LLM, deterministic fallback)
   → no:  continue

3. Default: mode = "deterministic"
```

### Model configuration table

| Mode | Primary | Fallback | Requires |
|---|---|---|---|
| `auto` | Claude | Deterministic | `ANTHROPIC_API_KEY` |
| `claude` | Claude | Safe string only | `ANTHROPIC_API_KEY` |
| `local` | Local LLM | Deterministic | Server running |
| `deterministic` | Deterministic | Safe string | Nothing |

---

## Fallback Strategy

### Fallback chain

```
Primary backend called
    │
    ├── Success → return response_text
    │
    └── Any failure (network, auth, timeout, empty response)
            │
            ├── mode = "auto":   try Deterministic backend
            │       │
            │       ├── Success → return response_text
            │       └── Failure → return SAFE_STRING
            │
            ├── mode = "claude":  return SAFE_STRING (no mock)
            ├── mode = "local":   try Deterministic, then SAFE_STRING
            └── mode = "deterministic": return SAFE_STRING
```

### Safe fallback strings (eLo-voiced, not technical)

```python
_SAFE_STRINGS = [
    "I'm here with you — what were you saying?",
    "I lost that for a moment. Say it again?",
    "I'm with you — continue.",
]
```

Selected deterministically by `len(user_input) % len(_SAFE_STRINGS)`.
Never exposes: API errors, 401 codes, stack traces, backend names, request IDs.

### Error handling contract

| Error type | Behaviour | User sees |
|---|---|---|
| API key missing | Skip backend silently | Fallback response |
| 401 Unauthorized | Log to debug, skip | Fallback response |
| Timeout | Caught, skip | Fallback response |
| Network error | Caught, skip | Fallback response |
| Empty response | Treat as failure, skip | Fallback response |
| Backend raises | Caught, skip | Fallback response |

All errors are caught in `_try_claude()` and `_try_local()`.
The router never propagates exceptions. The conversation never breaks.

---

## Local LLM Integration Path

### Step 1 — Install a local server

```bash
# Option A: Ollama (recommended for macOS)
brew install ollama
ollama run llama3

# Option B: LM Studio
# Download from lmstudio.ai, load a model, start local server

# Option C: llama.cpp server
# Compile and run with --server flag
```

### Step 2 — Set environment variables

```bash
export ELO_LOCAL_MODEL_URL=http://localhost:11434/v1/chat/completions
export ELO_LOCAL_MODEL_NAME=llama3
```

### Step 3 — Switch backend

```bash
python main.py
# or
/backend local
```

### Step 4 — Verify

```python
from backends.backend_router import get_backend_mode
from backends.local_llm_adapter import LocalLLMAdapter

adapter = LocalLLMAdapter()
print(f"Available: {adapter.is_available()}")
print(f"Active:    {get_backend_mode()}")
```

---

## Personality Layer Independence

The personality engine (`elo_personality_engine/`) is backend-agnostic.
The same system prompt is built regardless of which backend will receive it.

```
Personality Engine                 Backend
─────────────────                  ───────
build_elo_prompt()    →   prompt   →   Deterministic  (ignores prompt structure)
                          string   →   Local LLM      (uses as system prompt)
                                   →   Claude         (uses as system prompt)
```

The deterministic backend does not use the prompt for generation
(it uses pattern matching instead), but the prompt is still built
so the interface stays identical.

---

## Kernel Independence

The kernel routes. The backend generates. These never intersect.

```
Kernel reads:   user_input, StateBus
Kernel writes:  mode, meta (loop_detected, input_class, loop_reason)

Backend reads:  user_input, mode, context, memory, state, identity
Backend writes: response_text (string only)

No backend imports from core/kernel.py.
No kernel imports from backends/.
The StateBus carries all data. Nothing is shared by reference.
```

---

## Adding a New Backend

```python
# 1. Subclass BaseBackend
from backends.base_backend import BaseBackend, BackendResponse

class MyBackend(BaseBackend):
    NAME         = "my_backend"
    VERSION      = "1.0.0"
    DESCRIPTION  = "My custom backend"
    REQUIRES_KEY = False
    LAYER        = "output"
    KERNEL_SAFE  = True   # mandatory

    def is_available(self) -> bool:
        return True

    def generate_response(self, user_input, mode, context, memory, state, identity) -> BackendResponse:
        return {"response_text": generate(user_input, mode)}

# 2. Register in router
from backends.backend_router import _get_mock  # or add to BackendRegistry

# 3. Test
python tests/test_backends.py
```

**Invariants that must hold:**
- `KERNEL_SAFE = True` — or registry refuses registration
- No import of `core/kernel.py` at module level
- `generate_response()` always returns `BackendResponse`, never raises
- Response text never contains API errors, stack traces, or backend metadata
