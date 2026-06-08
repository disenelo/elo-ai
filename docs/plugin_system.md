# eLo AI OS — Plugin System Specification

**Version**: 1.0
**Status**: Active

---

## Principle

Plugins extend output layers only.
They may never modify kernel logic, routing decisions, or cognitive behaviour.

```
ALLOWED:   core/ → plugin (plugins read kernel output)
FORBIDDEN: plugin → core/ (plugins cannot write to kernel state)
```

---

## Plugin interface

Every plugin must subclass `plugins.base.PluginBase` and declare:

```python
class MyPlugin(PluginBase):
    # ── identity ──
    NAME:         str  = "my_plugin"     # unique, lowercase_underscore
    VERSION:      str  = "1.0.0"         # semver
    CAPABILITIES: list = ["output_type"] # see capability vocabulary

    # ── safety declarations (required, enforced at registration) ──
    LAYER:        str  = "output"        # "output" | "input" | "observability"
    KERNEL_SAFE:  bool = True            # MUST be True — no exceptions

    # ── required methods ──
    def generate_response(self, user_input: str, context: dict) -> str: ...
    def is_available(self) -> bool: ...
```

### Capability vocabulary

| Capability | Layer | Description |
|---|---|---|
| `text_generation` | output | Generates text responses (API, local LLM) |
| `voice_output` | output | Speaks responses (TTS) |
| `hardware_output` | output | Drives physical devices (Orb, robot) |
| `voice_input` | input | Captures audio (STT) |
| `vision` | input | Processes images |
| `observability` | observability | Reads events for monitoring (no side effects) |

---

## Layer rules

### output

- Receives `(user_input, context)` after kernel has made all decisions
- May generate or transform responses
- May deliver output (TTS, hardware, file write)
- May NOT read from or write to any `core/` module
- May NOT call `core/kernel.decide_response()`
- May NOT modify routing mode

### input

- Captures raw input and returns a string
- May NOT call `core/kernel.py`
- May NOT modify routing mode
- Output is text only — all decisions belong to the kernel

### observability

- Reads system events (from dashboard/event_bus or snapshot files)
- Pure read-only — no writes, no state mutations
- May NOT modify any core/ module

---

## Lifecycle

```
register(plugin)
    → validate()          safety constraints checked; refused if violated
    → plugin stored in registry

activate(name)
    → is_available()      checked; falls back to offline if False
    → on_load()           called once; safe to open connections, load models
    → plugin becomes active

[per turn]
    → generate_response() called with (user_input, context)
    → deliver_output()    called if plugin has output capability

[periodic]
    → on_health_check()   called by registry to verify still operational

deactivate(name)
    → on_unload()         called once; release connections, free resources
    → plugin deactivated
```

---

## Safety constraints

Enforced at `registry.register()` time. A plugin that violates ANY constraint is refused registration.

| Constraint | Rule | Enforced by |
|---|---|---|
| `KERNEL_SAFE=True` | Plugin must declare it does not modify kernel state | `validate()` |
| `LAYER` valid | Must be one of: output, input, observability | `validate()` |
| `NAME` unique | Must not be empty or "base" | `validate()` |
| No kernel imports | Plugin must not import `core/kernel.py` directly | Convention + audit |
| No routing calls | Plugin must not call `route()`, `decide_response()` | Convention + audit |
| No engine writes | Plugin must not write to `_loop_state`, `_detector`, etc. | Convention + audit |

A plugin that passes `validate()` but violates the convention-level rules is considered a **safety violation** and must be removed. If discovered post-release, it triggers a MAJOR version increment.

---

## Example plugins

### Unity output plugin (skeleton)

```python
class UnityOutputPlugin(PluginBase):
    NAME         = "unity_output"
    VERSION      = "1.0.0"
    CAPABILITIES = ["hardware_output"]
    LAYER        = "output"
    KERNEL_SAFE  = True

    def is_available(self) -> bool:
        return os.path.exists(self.signal_file_path)

    def generate_response(self, user_input: str, context: dict) -> str:
        # delegate to offline — Unity plugin handles delivery, not generation
        from core.behavior_engine import generate_offline_response
        return generate_offline_response(user_input, context, context.get("mode","companion"))

    def deliver_output(self, response: str, context: dict):
        signal = to_unity_signal(mode=context.get("mode",""), ...)
        write_signal_file(signal, self.signal_file_path)
```

### Voice output plugin (skeleton)

```python
class VoiceOutputPlugin(PluginBase):
    NAME         = "voice_output"
    VERSION      = "1.0.0"
    CAPABILITIES = ["voice_output"]
    LAYER        = "output"
    KERNEL_SAFE  = True

    def is_available(self) -> bool:
        try: import pyttsx3; return True
        except ImportError: return False

    def generate_response(self, user_input: str, context: dict) -> str:
        from core.behavior_engine import generate_offline_response
        return generate_offline_response(user_input, context, context.get("mode","companion"))

    def deliver_output(self, response: str, context: dict):
        from plugins.voice.tts_output import speak
        speak(response, emotion_snapshot=context.get("emotion"))
```

### Memory visualiser plugin (skeleton)

```python
class MemoryVisualiserPlugin(PluginBase):
    NAME         = "memory_visualiser"
    VERSION      = "1.0.0"
    CAPABILITIES = ["observability"]
    LAYER        = "observability"
    KERNEL_SAFE  = True

    def is_available(self) -> bool: return True

    def generate_response(self, user_input: str, context: dict) -> str:
        # observability plugins don't generate responses
        from core.behavior_engine import generate_offline_response
        return generate_offline_response(user_input, context, context.get("mode","companion"))

    def deliver_output(self, response: str, context: dict):
        from world.world_state import build_world_state, save_world_state
        state = build_world_state(project=context.get("project"))
        save_world_state(state)   # write to disk for external renderer
```

### Robot control plugin (skeleton)

```python
class RobotControlPlugin(PluginBase):
    NAME         = "robot_control"
    VERSION      = "0.1.0"
    CAPABILITIES = ["hardware_output"]
    LAYER        = "output"
    KERNEL_SAFE  = True

    def is_available(self) -> bool:
        try: import RPi.GPIO; return True
        except ImportError: return False

    def generate_response(self, user_input: str, context: dict) -> str:
        from core.behavior_engine import generate_offline_response
        return generate_offline_response(user_input, context, context.get("mode","companion"))

    def deliver_output(self, response: str, context: dict):
        # HARDWARE HOOK — map emotion/state to servo/light commands
        emotion = (context.get("emotion") or {}).get("emotion", "neutral")
        energy  = (context.get("state")   or {}).get("weight", 0.5)
        # _set_robot_state(emotion, energy)
```

---

## Registering a plugin

```python
from plugins.registry import registry

# register (safety checked automatically)
registry.register(MyPlugin())

# activate
registry.activate("my_plugin")

# use — same call regardless of which plugin is active
response = registry.generate_response(user_input, context)
```

---

## Forbidden patterns

Any plugin that does any of the following is **immediately invalid**:

```python
# FORBIDDEN — importing kernel
import core.kernel as kernel
from core.kernel import route, decide_response, _loop_state

# FORBIDDEN — calling routing
mode = route(classification, assembled)
response, meta = decide_response(user_input, context)

# FORBIDDEN — writing to engine state
from core.kernel import _detector
_detector.arm_reflection_cooldown(5)   # NO

# FORBIDDEN — modifying memory retrieval
from core.memory_engine import _score_record
_score_record.__code__ = ...           # NO

# FORBIDDEN — setting KERNEL_SAFE = False
KERNEL_SAFE = False                    # Refused at registration
```
