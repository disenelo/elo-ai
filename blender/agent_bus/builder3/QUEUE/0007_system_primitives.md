# WO-B3-0007 — System Primitives module

**Seat:** Builder 3  
**Priority:** P1  
**Status:** QUEUE  
**Source:** [SPEC] `docs/architecture/_intake/SOURCE_SYSTEM-FACULTY-FAST-LANE_2026-10-08.md` §Part 1 + §Part 2 + `SOURCE_ELO-COMMAND-LAYER_2026-10-08.md`  
**Date added:** 2026-10-08

---

## What

Create `tools/system_primitives.py` — a stable, deterministic API over macOS system utilities.

This is **not a cognitive tool**. It provides facts. No LLM. No confirmation required. It is the instrument panel the kernel calls directly for Tier-0 requests.

---

## Why

Currently the only Tier-0 direct path is the CLOCK handler in `server.py`. Everything else — math, date arithmetic, disk/battery/system state, file search — routes through the LLM or a confirmation-based cognitive tool. The spec says: **don't make the AI calculate or invent things that macOS can deterministically provide.** [SPEC SOURCE_SYSTEM-FACULTY-FAST-LANE_2026-10-08.md §"For eLo specifically"]

---

## Spec

Build `tools/system_primitives.py` with the following stable API surface. Thin wrappers over macOS shell commands — **no imports beyond subprocess/shlex/datetime**.

### `SystemPrimitives` class (or module-level functions)

```python
# TIME
system.time.now()           # → "13:25:42"       (date +%H:%M:%S)
system.time.utc_now()       # → ISO UTC string   (date -u +%Y-%m-%dT%H:%M:%SZ)
system.time.timestamp()     # → unix int         (date +%s)
system.time.timezone()      # → "BST" / "UTC"

# CALENDAR
system.calendar.today()     # → "Thursday 8 October 2026"
system.calendar.tomorrow()  # → date string      (date -v+1d)
system.calendar.yesterday() # → date string      (date -v-1d)
system.calendar.date_offset(days=7)   # → date string (date -v+Nd)
system.calendar.day_of_week()         # → "Thursday"

# MATH
system.math.calculate(expression: str) → str   # echo "expr" | bc (scale=4 by default)
# e.g. calculate("25 * 17") → "425"
# e.g. calculate("10 / 3")  → "3.3333"
# For complex: python3 -c "print(expr)" fallback

# COMPUTER
system.computer.hostname()    # → string  (hostname)
system.computer.os_version()  # → string  (sw_vers -productVersion)
system.computer.uptime()      # → string  (uptime)
system.computer.battery()     # → dict {percent, charging}  (pmset -g batt)
system.computer.disk()        # → dict {total, free, used}  (df -h /)
system.computer.cpu_info()    # → string  (sysctl -n machdep.cpu.brand_string)

# FILES
system.files.list(path: str)               # → list of filenames (ls)
system.files.search(query: str, scope: str = "~")  # → list of paths (mdfind)
system.files.exists(path: str)             # → bool
system.files.open(path: str)               # → None  (open command)

# MACOS
system.macos.speak(text: str, voice: str = None)  # → None  (say -v voice text)
system.macos.notify(title: str, message: str)      # → None  (osascript display notification)
system.macos.open_app(name: str)                   # → None  (open -a)
system.macos.open_url(url: str)                    # → None  (open url)

# PROCESS
system.process.list_running()    # → list of {name, pid}  (ps -ax)
system.process.is_running(name: str)  # → bool

# ENVIRONMENT
system.env.whoami()     # → string
system.env.current_dir() # → string  (pwd)
```

### Capability declarations (for kernel dispatcher)

Each function must have metadata the kernel can query:

```python
CAPABILITIES = {
    "time.now":           {"deterministic": True, "latency": "instant", "reasoning_required": False, "authority": "definitive", "freshness": "live"},
    "calendar.today":     {"deterministic": True, "latency": "instant", "reasoning_required": False, "authority": "definitive", "freshness": "live"},
    "math.calculate":     {"deterministic": True, "latency": "instant", "reasoning_required": False, "authority": "definitive", "freshness": "live"},
    "computer.battery":   {"deterministic": True, "latency": "instant", "reasoning_required": False, "authority": "definitive", "freshness": "live"},
    "files.search":       {"deterministic": True, "latency": "fast",    "reasoning_required": False, "authority": "definitive", "freshness": "live"},
    # ... etc
    # authority levels: definitive | recorded | inference
    # freshness: live | cached | aged (days since last update)
}
```
Each result returned by any function in this module must carry a metadata dict:
```python
{"value": ..., "source": "macOS", "authority": "definitive", "confidence": 1.0, "freshness": "live"}
```
[SPEC SOURCE_CAPABILITY-AUTHORITY-MODEL_2026-10-08.md §"Every result should carry something like"]

### eLo command vocabulary

Also expose a command vocabulary dict mapping natural shorthand to the underlying call — Builder 1 will wire this into the fast router:

```python
COMMAND_VOCAB = {
    "TIME":     "time.now",
    "DATE":     "calendar.today",
    "CALC":     "math.calculate",
    "BATTERY":  "computer.battery",
    "DISK":     "computer.disk",
    "FIND":     "files.search",
    "OPEN":     "macos.open_app",
    "SPEAK":    "macos.speak",
    "NOTIFY":   "macos.notify",
    "PROCESS":  "process.list_running",
    "SYSTEM":   "computer.os_version",
    "UPTIME":   "computer.uptime",
}
```

---

## What NOT to do

- Do not add LLM calls. This module is deterministic.
- Do not require AppleScript for anything in the list above (except notify + speak — those are already AppleScript/`say`).
- Do not add confirmation gates. These are safe read-only or output-only actions.
- Do not touch `server.py`, `backend_router.py`, `system_agent.py`. Builder 3 owns `tools/system_primitives.py` only.
- The file `tools/system_agent.py` already exists and handles window/app control with confirmation. Do NOT duplicate it. `system_primitives.py` is the **fast/no-confirm** layer beneath it.

---

## Tests

Write unit tests in `tests/tools/test_system_primitives.py`:
- `test_time_now_returns_string`
- `test_math_calculate_integer`
- `test_math_calculate_float`
- `test_calendar_today_returns_string`
- `test_computer_battery_returns_dict`
- `test_files_search_returns_list`
- `test_capabilities_dict_exists`
- `test_command_vocab_dict_exists`

All tests must run headless (no socket, no server, no LLM). Subprocess calls to macOS shell are fine.

---

## Live turn needed

David confirms eLo can answer "What time is it?", "What's 28 × 74?", "What's my battery?" via the new primitives path — no LLM invoked.

---

## Related

- Builder 1 card 0104: wires these into fast router in `server.py`
- Builder 1 card 0105: 3-tier architecture that routes to this module
- Source: `docs/architecture/_intake/SOURCE_SYSTEM-FACULTY-FAST-LANE_2026-10-08.md`
- Source: `docs/architecture/_intake/SOURCE_ELO-COMMAND-LAYER_2026-10-08.md`
- Source: `docs/architecture/_intake/SOURCE_FAST-ROUTER-OPTIMISATION_2026-10-08.md`

---

## Result (Builder 3, 2026-10-08)
- commit: ff07bf5
- `tools/system_primitives.py`: all 8 namespaces and every function in the spec. Each result has the metadata shape. Failures return `value: None, confidence: 0.0, error` and never raise. `CAPABILITIES` adds a `side_effect` flag (speak/notify/open), so the dispatcher can tell facts from actions. `COMMAND_VOCAB` as specced, plus `system.call("math.calculate", …)` / `system.run("CALC", …)`.
- Safety beyond the spec: `math.calculate` refuses anything that isn't arithmetic before bc or the python3 fallback runs (spoken "times / divided by / squared / what's …" are normalised first). Nothing runs through a shell. `open_url` accepts http(s) only.
- Tests: `tests/tools/test_system_primitives.py` 13/13 (headless, real macOS). Real values 2026-10-08: "Thursday 8 October 2026"; battery `{percent: None, power_source: AC, has_battery: False}` (Mac Studio); 28×74 → 2072; 10/3 → 3.3333.
- Not done: the live turn needs Builder 1 card 0104 (fast router → `system.run(...)`). Until that's wired, "What's 28 × 74?" still goes through the existing path.
