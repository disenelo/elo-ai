# WO-B2-0010 — LIFE Process + Short-term Working Memory

**Seat:** Builder 2  
**Priority:** P1  
**Status:** QUEUE  
**Source:** [SPEC] `docs/architecture/_intake/SOURCE_ELO-CONTINUOUS-IDENTITY_2026-10-08.md` §LIFE + §eLo LIFE LOOP · `SOURCE_FAST-ROUTER-OPTIMISATION_2026-10-08.md` §9 · `SOURCE_CAPABILITY-AUTHORITY-MODEL_2026-10-08.md` §"Tier 1 — eLo's known world"  
**Date added:** 2026-10-08

---

## What

Two linked deliverables:

**A. Short-term Working Memory** — last 10–30 relevant events in memory, alongside long-term vault.  
**B. LIFE Process continuity** — eLo's inner life (thinking/dreaming/reflecting/sleeping) continues whether or not David is talking to eLo.

These are the STATE tier of the capability fabric. When the kernel asks "what do I need?", working memory and the LIFE process state are checked before any faculty is invoked. [SPEC SOURCE_ELO-CONTINUOUS-IDENTITY_2026-10-08.md §"SELF + LIFE"]

---

## A. Working Memory

### Why
"What am I working on?" is currently answered by LLM generation. It should be answered by state lookup.
```text
CurrentProject / CurrentTask / CurrentSession / RecentEvents / WorkingMemory
```
The kernel doesn't need to ask a model to reinterpret something eLo already knows. [SPEC SOURCE_CAPABILITY-AUTHORITY-MODEL_2026-10-08.md §"Tier 1 — eLo's known world"]

### What to build
`faculties/inner_thought/working_memory.py` — a ring buffer of the last 10–30 events:

```python
class WorkingMemory:
    MAX_EVENTS = 30
    
    def add_event(self, event: dict):
        """
        event = {
            "timestamp": ...,
            "type": "USER_MESSAGE" | "APP_OPENED" | "APP_CLOSED" | "TASK_CHANGED" | "FILE_OPENED" | ...,
            "content": ...,
            "source": "macOS" | "user" | "unity" | "elo",
            "authority": "definitive" | "recorded" | "inference",
        }
        """
    
    def query(self, query: str) -> list[dict]:
        """Simple keyword/type filter over the last N events."""
    
    def current_project(self) -> dict | None:
        """Returns most recent TASK_CHANGED or PROJECT_SET event."""
    
    def recent_events(self, n: int = 10) -> list[dict]:
        """Last N events, newest first."""
    
    def as_context(self) -> str:
        """Formatted string the kernel can inject into a faculty packet's STATE field."""
```

Example content:
```text
09:31 opened Blender
09:34 imported eLo model
09:37 started render
09:38 switched to Photoshop
```
[SPEC SOURCE_FAST-ROUTER-OPTIMISATION_2026-10-08.md §9]

Working memory events have authority `"recorded"`, freshness = seconds since timestamp. They are not LLM inference.

### Integration
- Builder 1 reads `working_memory.as_context()` in the STATE tier of capability_dispatcher (card 0104).
- Events are added by: user messages, app-open/close events from Presence (if Designer wires event bus), task state changes.
- Builder 2 fires `working_memory.add_event()` from inner_thought on significant events.

---

## B. LIFE Process

### Why
Currently eLo's inner process only runs when David sends a message. The spec says:

> "eLo's inner life is continuous and is not suspended merely because a capability is being invoked."
> "David's request is an event occurring inside eLo's life, not the thing that creates eLo's existence."

[SPEC SOURCE_ELO-CONTINUOUS-IDENTITY_2026-10-08.md]

### What to build
Extend `faculties/inner_thought/` to support continuous lifecycle:

**LIFE loop states:**
```text
AWAKE   → David is present / active interaction
RESTING → No active conversation, ticking slowly  
SLEEP   → Extended idle, dreaming/consolidation
```

**In each state, inner_thought runs at different tick rates:**
- AWAKE: tick on every message + short idle ticks
- RESTING: slow tick (e.g. every 60s) — reflect, wander, process recent events
- SLEEP: very slow tick (e.g. every 10min) — consolidate WKG, dream (recombine memory), imagine

**The LIFE loop itself lives in Builder 1's daemon (card 0106).** Builder 2 provides the tick function:

```python
def life_tick(state: str) -> dict:
    """
    Called by daemon at appropriate interval.
    state = "AWAKE" | "RESTING" | "SLEEP"
    Returns inner_thought output (may include WKG write, SPG update, etc.)
    """
```

**RESTING tick does:**
- Process recent working_memory events
- Light reflection on last interaction
- Update emotional/curiosity state

**SLEEP tick does:**
- Consolidate significant events into WKG nodes (vault_write)
- Dream: recombine memory — surface unexpected connections
- Imagination: generate new thoughts eLo hasn't been asked about

[SPEC SOURCE_ELO-CONTINUOUS-IDENTITY_2026-10-08.md §"LIFE" + §"eLo LIFE LOOP"]

---

## Four LIFE process components [SPEC SOURCE_ELO-CONTINUOUS-IDENTITY_2026-10-08.md §LIFE]

```text
thinking / wondering / remembering / dreaming / reflecting / learning / unlearning /
resting / sleeping / curiosity / emotion/state
```

Builder 2 already owns `faculties/inner_thought/` and `faculties/metacognition/`. This card extends those to:
1. Run as a continuous process (not only on-demand)
2. Tick at different rates based on AWAKE/RESTING/SLEEP state
3. Feed events into working_memory
4. Write consolidation WKG nodes during SLEEP

---

## Tests

- `test_working_memory_add_and_query` — add 5 events, query returns correct subset
- `test_working_memory_ring_buffer` — add 35 events, only last 30 retained
- `test_working_memory_current_project` — returns most recent TASK_CHANGED event
- `test_working_memory_as_context_returns_string` — as_context() returns non-empty string after events added
- `test_life_tick_resting_runs_without_error` — `life_tick("RESTING")` completes without exception
- `test_life_tick_sleep_writes_wkg_node` — SLEEP tick produces at least one vault_write (mock vault)
- `test_life_tick_does_not_block` — tick completes in under 2s (mock LLM)

---

## Live turn needed

David: "What was I doing?" → working_memory answers from STATE tier, no LLM.  
Between David's messages: inner_thought log shows RESTING ticks ran during idle.  
After extended idle: WKG node written from SLEEP consolidation, David can ask eLo about it.

---

## Related

- B1-0104: capability_dispatcher reads working_memory for STATE tier
- B1-0105: capability fabric — LIFE is one of the four concurrent processes
- B1-0106: daemon hosts the LIFE loop, calls life_tick() at appropriate interval
- B1 existing: vault_write / WKG (working_memory's SLEEP consolidation writes here)


---

## Result
- commit: `256f3e2`
- test: `tests/test_life_and_working_memory.py` — 19 passed (all 7 named tests present)
- notes:

**A. Working memory** — `faculties/inner_thought/working_memory.py`, exact API
from the card. Live:

    [WORKING MEMORY — what has just happened, recorded not inferred]
    15:56 opened Blender
    15:56 eLo robot shell (recorded)
    Current: eLo robot shell

- **Name collision flagged, not merged.** `runtime/working_memory.py` already
  exists and is wired into server.py — it holds cognitive FRAMES, goals and
  attention (what eLo is holding in mind during a turn). This is an event
  TIMELINE. Different things. A test asserts the two classes have not
  converged, because someone will otherwise merge them in good faith and lose
  the authority field.
- Authority defaults to `recorded`, **never** `definitive`. The other default
  would let an inference read as a fact from the OS, and avoiding exactly that
  guess is why this tier exists.
- Empty when nothing has happened — an empty string, not a sentence saying so.

**B. LIFE** — `faculties/inner_thought/life.py`, `life_tick(state)` and
nothing else. No thread, no scheduler, no timer; a test greps for them. The
card says the loop lives in your daemon (0106) and two things driving eLo's
life is the mistake already made with sits, dreams and deferral stores.

    AWAKE    does nothing — the turn path already thinks on every message
    RESTING  actions=['read_working_memory','carried_threads']   14.7ms
    SLEEP    actions=['held_threads'], dream_due reported       145.3ms

- **SLEEP does not start a dream.** Dreaming already triggers from
  ambient_engine on a spent mind battery in calm. This reports `dream_due` and
  leaves the decision there.

**FOR BUILDER 1 (cards 0104 / 0106)** — the contract is exported from
`faculties.inner_thought`:

    from faculties.inner_thought import as_context        # STATE tier, 0104
    from faculties.inner_thought import life_tick, RESTING, SLEEP   # 0106

`as_context()` returns "" when nothing has happened. `life_tick()` never
raises and returns `{state, ok, actions, elapsed_ms, ...}`. Suggested
intervals are in `TICK_INTERVAL_S` — advisory, since this module schedules
nothing.

**NOT BUILT:** events are only added by whatever calls `add_event()`. The card
lists app-open/close from Presence "if Designer wires event bus" — that bus
does not exist yet, so nothing populates the timeline automatically. The one
caller today is this module's own API. Flagged rather than faked with a
synthetic feed.

## Live turn needed
Two, and the first will fail until something feeds the timeline:

1. **"What was I doing?"** — should answer from working memory, no model.
   Needs app/task events arriving first (Designer's bus, or Builder 1 calling
   `add_event` on task changes).
2. **Between messages** — with the daemon calling `life_tick("RESTING")`,
   deferred threads stay carried while David is away. Observable as
   `EloSelfState.open_threads` staying populated during idle rather than only
   during a turn.
