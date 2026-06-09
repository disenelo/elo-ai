# eLo AI OS — Backend Interface Contract

**Step 41**
**File**: `backends/base_backend.py`
**Status**: Stable — interface is frozen alongside the kernel

---

## Principle

The kernel depends on an abstraction, not on any model.
No concrete backend may be imported by the kernel.
No backend may import kernel internals.

```
kernel / core_engine          depends on ▶   BaseBackend (abstract)
                                                    ▲
                                          implemented by
                                 ┌───────────────────────────────┐
                              Offline       Claude        LocalLLM
                              Backend       Backend       Backend
```

---

## Method signature

```python
def generate_response(
    self,
    user_input: str,                  # raw user text
    mode:       str,                  # kernel routing mode
    context:    dict,                 # StateBus.to_context() flat dict
    memory:     MemoryContext,        # memory influence signals
    state:      StateContext,         # conversational state snapshot
    identity:   IdentityContext,      # identity engine snapshot
) -> BackendResponse:                 # {"response_text": str}
```

---

## Parameters

### `user_input: str`

The raw text as typed by the user. Identical to what the kernel classified and routed. Do not modify it — it is provided for generation only.

### `mode: str`

The routing mode selected by the kernel. One of:

| Mode | Meaning |
|---|---|
| `DIRECT` | Factual query — answer directly |
| `GENTLE_GROUNDED` | Emotional input — acknowledge, no abstraction |
| `CREATIVE` | Imaginative — expand, follow symbol |
| `STRUCTURED` | Project/system — organised, step-oriented |
| `SIMPLIFY` | Short input — minimal response |
| `CONVERSATIONAL` | Default eLo voice — hold tension, one question |

The backend may use mode to adjust its system prompt or instruction framing. The backend must NOT re-route or override this value.

### `memory: MemoryContext`

Optional fields from memory_engine:

| Field | Type | Description |
|---|---|---|
| `tone_signal` | str | Dominant tone from recent history |
| `returning_theme` | str | Recurring concept phrase |
| `symbolic_echo` | str | Entity pattern phrase |
| `project` | str | Active project namespace |
| `response_style` | str | Style hint from 5-category synthesis |
| `key_association` | str | Cross-concept bridge |
| `future_idea` | str | Direction the work is pointing |

### `state: StateContext`

Optional fields from state_engine:

| Field | Type | Description |
|---|---|---|
| `name` | str | exploring / building / focused / reflecting / playful / resting |
| `tone_bias` | str | precise / open / grounded / soft / light / minimal |
| `weight` | float | 0.0 (tight) → 1.0 (expressive) |
| `pacing_bias` | str | measured / unhurried / slow / quick |

### `identity: IdentityContext`

Optional fields from identity_engine:

| Field | Type | Description |
|---|---|---|
| `values` | list | 3 most active core values this turn |
| `perspective` | str | expansion / symbolic / practical / relational / contradictory |
| `intent` | str | expand_idea / hold_space / advance_project / offer_question / ... |
| `response_bias` | str | lean_imaginative / stay_grounded / slow_down / advance / ... |
| `entities` | list | eLo universe entities mentioned |

---

## Return value

```python
BackendResponse = {"response_text": str}
```

`response_text` must be:
- A non-empty string
- The final response exactly as shown to the user
- Free of debug metadata or system tokens
- Deterministic for identical inputs (offline backend requirement)

---

## Required class attributes

```python
class MyBackend(BaseBackend):
    NAME:         str  = "my_backend"   # unique, lowercase_underscore
    VERSION:      str  = "1.0.0"         # semver
    DESCRIPTION:  str  = "One-line description"
    REQUIRES_KEY: bool = False           # True if API key needed
```

---

## Lifecycle

```
BackendRegistry.register(MyBackend())
    → stored in registry

BackendRegistry.activate("my_backend")
    → is_available() checked
    → on_load() called once

[per turn]
    → generate_response(user_input, mode, context, memory, state, identity)
    → returns BackendResponse

BackendRegistry.deactivate()
    → on_unload() called once
```

---

## Forbidden patterns

```python
# FORBIDDEN — backend importing kernel internals
from core.kernel import route, _detector, decide_response   # ✗

# FORBIDDEN — backend altering routing
def generate_response(self, ...):
    mode = "DIRECT"   # ✗ — mode is set by kernel, not backend

# FORBIDDEN — backend modifying shared state
def generate_response(self, ...):
    from core.kernel import _detector
    _detector.clear()   # ✗

# FORBIDDEN — non-deterministic output in offline backend
import random
return {"response_text": random.choice(responses)}   # ✗
```

---

## Implementing a backend

```python
from backends.base_backend import BaseBackend, BackendResponse

class MyBackend(BaseBackend):
    NAME         = "my_backend"
    VERSION      = "1.0.0"
    DESCRIPTION  = "My custom backend"
    REQUIRES_KEY = False

    def is_available(self) -> bool:
        return True

    def generate_response(
        self, user_input, mode, context, memory, state, identity
    ) -> BackendResponse:
        # build prompt from mode + memory + state + identity
        # call your model
        # return {"response_text": model_output}
        return {"response_text": f"Response to: {user_input}"}
```

---

## Error handling

Backends should raise `BackendUnavailableError` when they cannot serve.
The registry catches this and falls back to `OfflineBackend`.

```python
from backends.base_backend import BackendUnavailableError

def generate_response(self, ...):
    if not self._key:
        raise BackendUnavailableError(f"{self.NAME}: API key not set")
    ...
```
