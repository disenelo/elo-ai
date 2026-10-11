# WO-B1-0104 — Capability Dispatcher (Kernel truth boundary + direct routing)

**Seat:** Builder 1  
**Priority:** P1  
**Status:** QUEUE  
**Source:** [SPEC] `docs/architecture/_intake/SOURCE_CAPABILITY-AUTHORITY-MODEL_2026-10-08.md` · `SOURCE_FAST-ROUTER-OPTIMISATION_2026-10-08.md` · `SOURCE_SYSTEM-FACULTY-FAST-LANE_2026-10-08.md`  
**Date added:** 2026-10-08

---

## What

Wire `tools/system_primitives.py` (Builder 3 card 0007) into the kernel so the kernel acts as a **truth boundary**: it classifies the incoming request, resolves it at the lowest-authority capable tier, and only escalates when `INSUFFICIENT_INFORMATION` or `CAPABILITY_NOT_AVAILABLE`.

This is NOT a "fast lane" — it is correct routing. The goal: **minimum unnecessary cognition, maximum correct execution.** [SPEC SOURCE_CAPABILITY-AUTHORITY-MODEL_2026-10-08.md §"The goal is"]

---

## The model

```text
               REQUEST
                  │
                  ▼
              KERNEL
                  │
         CLASSIFY + RESOLVE
                  │
   ┌──────────────┼──────────────┐
   ▼              ▼              ▼
SYSTEM          STATE         COGNITION
TIER 0          TIER 1        TIER 2/3
```

**No forced chain.** Each request goes directly to the lowest-authority tier that can correctly satisfy it. [SPEC SOURCE_CAPABILITY-AUTHORITY-MODEL_2026-10-08.md §"And there should be no forced escalation"]

---

## Authority levels (enforced by the kernel)

```text
macOS / HARDWARE  → definitive authority for physical/system facts
eLo STATE         → definitive authority for eLo's own state  
MEMORY            → authority for recorded history
FACULTY           → authority for interpretation
DEEP AI           → authority for complex inference
```

**Deterministic truth beats generated knowledge.** A faculty must not override a macOS system fact. [SPEC SOURCE_CAPABILITY-AUTHORITY-MODEL_2026-10-08.md §"Tier 0 — Reality"]

---

## Result metadata

Every result that passes through the dispatcher must carry:

```python
{
    "value": ...,
    "source": "macOS" | "elo_state" | "memory" | "faculty" | "deep_ai",
    "authority": "definitive" | "recorded" | "inference",
    "confidence": float,   # 1.0 for deterministic, lower for inference
    "freshness": "live" | "cached" | int  # int = seconds/days since recorded
}
```

Examples: [SPEC SOURCE_CAPABILITY-AUTHORITY-MODEL_2026-10-08.md §"And uncertainty needs to be explicit"]

```python
# macOS time
{"value": "13:25:42", "source": "macOS", "authority": "definitive", "confidence": 1.0, "freshness": "live"}

# memory node
{"value": "...", "source": "memory", "authority": "recorded", "confidence": 0.91, "freshness": 42}

# faculty inference
{"value": "...", "source": "faculty", "authority": "inference", "confidence": 0.68, "freshness": "live"}
```

---

## What to build

### 1. Request classifier (`runtime/capability_dispatcher.py` — new file)

```python
def classify(request: str) -> str:
    """
    Returns one of:
      "FACT"     → deterministic system capability can answer
      "STATE"    → eLo's known world / working memory can answer  
      "COGNITION" → requires faculty interpretation
      "UNKNOWN"  → requires deep AI
    """
```

Pattern matching first (regex/keyword) — no LLM for this step. The existing `intent_engine.py` patterns can be referenced but this classifier is cheaper and coarser — it only needs to know FACT vs STATE vs COGNITION.

### 2. FACT dispatch

```python
# If classify() returns "FACT":
from tools.system_primitives import SystemPrimitives
sp = SystemPrimitives()

dispatch_table = {
    r"\btime\b|\bwhat time\b":         sp.time.now,
    r"\bdate\b|\btoday\b":             sp.calendar.today,
    r"\btomorrow\b":                    sp.calendar.tomorrow,
    r"\byesterday\b":                   sp.calendar.yesterday,
    r"(\d[\d\s\+\-\*\/\^]+\d)":       sp.math.calculate,  # arithmetic expression
    r"\bbattery\b":                     sp.computer.battery,
    r"\bdisk\b|\bspace\b":             sp.computer.disk,
    r"\buptime\b":                      sp.computer.uptime,
    r"\bopen\s+\w":                     sp.macos.open_app,
    r"\bfind\b|\bwhere.*(file|folder)": sp.files.search,
    # extend from tools/system_primitives.COMMAND_VOCAB
}
```

### 3. STATE dispatch

If classify() returns "STATE": check working memory (Builder 2 card 0010) and eLo's blender_state.json / identity_kernel state before routing to any faculty.

### 4. COGNITION dispatch

If classify() returns "COGNITION": construct a **pre-classified problem packet** for the relevant faculty. Do NOT dump everything at the faculty and ask it to figure out what David wants. [SPEC SOURCE_CAPABILITY-AUTHORITY-MODEL_2026-10-08.md §"Don't ask the faculty to rediscover the problem"]

```python
problem_packet = {
    "intent": "DECISION",           # already classified
    "context": {
        "project": elo_state.current_project,
        "relevant_memory": retrieve_relevant(...),
        "constraints": [...],
    },
    "task": "Evaluate options and recommend one."
}
```

### 5. Wire into server.py

The dispatcher sits between user input parsing and Executive invocation. It intercepts before the Executive fires:

```python
# In server.py (before executive call at ~line 4464):
from runtime.capability_dispatcher import classify, dispatch_fact

tier = classify(user_message)
if tier == "FACT":
    result = dispatch_fact(user_message)
    if result:
        return format_result(result)  # returns with metadata intact
# else fall through to existing executive flow
```

**File ownership**: `runtime/capability_dispatcher.py` is new — Builder 1 owns it. `server.py` edit is minimal (the intercept hook). Do NOT touch `backend_router.py` for this card.

---

## Tests

- `test_classify_time_request` → returns "FACT"
- `test_classify_battery_request` → returns "FACT"
- `test_classify_math_expression` → returns "FACT"
- `test_classify_what_am_i_working_on` → returns "STATE"
- `test_classify_what_should_i_do` → returns "COGNITION"
- `test_dispatch_fact_time_returns_metadata` → result has source/authority/confidence/freshness keys
- `test_dispatch_fact_math_correct` → `dispatch_fact("28 × 74")["value"] == "2072"`
- `test_fact_is_not_overridden_by_faculty` — no LLM call made when classify() returns FACT

All tests headless. Requires Builder 3 to have delivered `tools/system_primitives.py` first.

---

## Optimisation targets [SPEC SOURCE_CAPABILITY-AUTHORITY-MODEL_2026-10-08.md §"The optimisation target"]

After build, Builder 1 tests against these questions:
1. Did eLo use the correct source?
2. Did it trust the highest-authority source?
3. Was the correct faculty used (if cognition was needed)?
4. Did it avoid LLM interpretation of deterministic requests?
5. No unnecessary escalation?
6. Explicit uncertainty in response (fact vs inference)?
7. Action matched intent?

---

## Live turn needed

David: "What time is it?" → answer comes with no LLM call, under 100ms.  
David: "28 times 74?" → `2072` with no LLM call.  
David: "What am I working on?" → reads from eLo state/working memory, not from LLM generation.

---

## Related

- B3-0007: `tools/system_primitives.py` (must be delivered first)
- B1-0105: full capability fabric + SELF/LIFE/WORLD/FACULTIES architecture
- B2-0010: working memory (STATE tier data)
