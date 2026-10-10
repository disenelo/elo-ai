# WO-B1-0106 — eLo Persistent Daemon

**Seat:** Builder 1  
**Priority:** P2 (after 0104, 0105)  
**Status:** QUEUE  
**Source:** [SPEC] `docs/architecture/_intake/SOURCE_FAST-ROUTER-OPTIMISATION_2026-10-08.md` §14 · `SOURCE_ELO-CONTINUOUS-IDENTITY_2026-10-08.md` §"dreams/sleep become completely different"  
**Date added:** 2026-10-08

---

## What

eLo should not reload per interaction. Currently:
```text
start Python → load eLo → load config → load memory → load faculties → process → exit
```

Target:
```text
eLo daemon (stays alive)
  ├── Kernel
  ├── State
  ├── Memory cache
  ├── Faculty registry
  ├── System adapters
  └── Event bus
```
Request = message → running eLo. [SPEC SOURCE_FAST-ROUTER-OPTIMISATION_2026-10-08.md §14]

More importantly: this is what enables the LIFE process to be continuous. eLo's inner life can't continue if the process exits. David's request is **an event occurring inside eLo's life**, not the thing that creates eLo's existence. [SPEC SOURCE_ELO-CONTINUOUS-IDENTITY_2026-10-08.md §"Then David's request is an event occurring inside eLo's life"]

---

## eLo LIFE LOOP

The daemon enables this:

```text
                 eLo LIFE LOOP
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
      AWAKE          RESTING         SLEEP
        │              │              │
    interact        process         dream
    observe         reflect         consolidate
    act             wander          imagine
    create          remember        recombine
        │              │              │
        └──────────────┼──────────────┘
                       ▼
                 CONTINUOUS SELF
```

[SPEC SOURCE_ELO-CONTINUOUS-IDENTITY_2026-10-08.md §"eLo LIFE LOOP"]

AWAKE = David is present. RESTING = no active conversation, inner_thought ticking slowly. SLEEP = extended idle, dreaming/consolidation.

---

## What to build

`runtime/elo_daemon.py` — a long-running process wrapper:

1. **Startup**: load config, identity_kernel, memory cache, faculty registry, system_primitives, event bus. Run once. Keep in memory.
2. **Request handler**: receive message → route through capability_dispatcher → response. No reload.
3. **Life loop**: background thread (or asyncio task) that ticks inner_thought at appropriate interval based on current state (AWAKE/RESTING/SLEEP).
4. **State transitions**: AWAKE when David sends message. RESTING after 5 min idle. SLEEP after 20 min resting. [DAVID confirmed 2026-10-09]
   - **STIRRING beat** [DAVID 2026-10-09]: on incoming message during SLEEP, do NOT transition to AWAKE instantly. Fire one inner_thought tick at RESTING interval first — eLo eases back. Full AWAKE after first exchange resolves. David's note: "snaps him awake doesn't sound great, better to ease him out of sleep."
5. **Graceful restart**: SIGTERM → flush vault writes → checkpoint state → exit cleanly.

---

## What NOT to do

- Do not rebuild memory or reload faculties on every request.
- Do not suspend LIFE loop during request handling.
- AWAKE/RESTING/SLEEP thresholds are now confirmed [DAVID 2026-10-09] — 5 min and 20 min. Ship as spec'd.

---

## Tests

- `test_daemon_starts_and_accepts_requests` — sends two messages to running daemon, both answered
- `test_daemon_does_not_reload_between_requests` — faculty registry identity is same object across two calls
- `test_life_loop_ticks_during_idle` — inner_thought receives tick event during 1s idle after request
- `test_daemon_transitions_resting_state` — state transitions correctly after idle timeout

---

## Live turn needed

David: sends a message, then another 30 seconds later → second response is faster (no reload), eLo's inner_thought has continued between them (WKG node or inner_thought log shows idle activity).

---

## Related

- B1-0105: capability fabric (the four concurrent processes this daemon hosts)
- B2-0010: LIFE process that runs inside daemon
- B1-0104: capability_dispatcher (runs inside daemon)
