# 00c_WO-105 — 🔴 KILL THE SILENT FAILURES. **P0.**

**WO:** WO-105 · **Seat:** builder · **Priority:** **P0** · **Gate?** none
**Origin:** David, 2026-08-13 — *"Silent failures don't make sense...."*
**Canon:** `WORKING_STANDARD.md` Rule 1 — *"'Absent' and 'broken' must never look the same."*

## Why this is P0 and not housekeeping
Every major defect found today hid behind a swallowed exception:
- desktop perception dead for weeks — swallowed `ImportError`
- `gaze` stripped from state — no error, key just vanished
- `record_outcome` writing to a non-existent lesson key — returns `{}`, says nothing
- `spatial_state` reading `pos_x` from a file that has `x` — defaults to `0.5, 0.1` and carries on
- the whole assembled-but-unread stack — `plan.world`, `plan.cognitive_state`, `plan.working_memory` all
  populated and consumed by nobody, with no complaint

**Not one of these would have survived a week if the code had said something.** This card is the reason
the other cards stop recurring.

## The sites — [VERIFIED 2026-08-13, grep]
### `runtime/spine/spine.py` — 9 swallow-to-`_log.debug` sites
`:362` · `:371` · `:421` · `:429` · `:456` · `:475` · `:493` · `:502` · `:508`
These cover perception, world-state assembly, working memory, cognitive-state assembly and embodiment.
**The entire cognition stack fails invisibly.**

### `server.py` — 5 bare `except: pass`
`:2496` · `:2503` · `:2512` · `:2552` · `:2604` (the `g_ctx` / prompt-context assembly block)

### `runtime/shadow_capture.py` — 6 sites, all labelled "non-critical"
`:56` · `:68` · `:116` · `:134` · `:151` · `:168`
**This is the training-data basket for WO-104.** If it silently stops writing, real learning dies quietly
and nobody knows for weeks. "Non-critical" is exactly wrong.

### Also
`world/live_world_state.py:204-208` — logs a warning then returns a **neutral `DesktopState`**. A neutral
object is worse than an exception: downstream cannot tell "nothing there" from "lookup failed."

## The rule to apply
**Three legitimate outcomes. Silence is not one of them.**
1. **Raise** — the caller genuinely cannot continue.
2. **Degrade explicitly** — return a value that *says it is degraded* (a status/`ok` flag, not a
   plausible-looking default), and **log at WARNING or above**, once, with the cause.
3. **Ignore deliberately** — allowed only with an inline comment naming *why this specific exception is
   safe to ignore here*. A bare `except: pass` never qualifies.

**Never** return a value indistinguishable from a real one. `pos_x = 0.5` is the canonical sin: it looks
like a position and it is a fabrication.

## Scope
1. Convert all 20 sites above to one of the three outcomes. `_log.debug` → **WARNING minimum** for
   anything on the cognition path.
2. **Startup self-check**: on boot, assert each faculty on the live path imported and wired; log a single
   clear line naming anything that didn't. **`faculties.temporal` should fail this today** — that failure
   is correct, leave it visible.
3. **Health surfaces degradation**: `/health` must show which faculties are live vs degraded vs dead —
   not just "up".
4. **Rule 1 alarm:** a lint/test that **fails CI on any new bare `except: pass` or silent `_log.debug`
   swallow** in `runtime/`, `server.py`, `world/`, `faculties/`. Without this, they grow back.

## 🔴 Constraint
**Do not change any behaviour except visibility.** No refactors riding along. If making a failure loud
reveals a real bug, **report it — don't fix it in this card.** That's how this one stays reviewable.

## Test (without David)
- Every listed site: inject the failure, assert a WARNING+ log or a raise. **No path stays silent.**
- Startup self-check flags a deliberately unwired faculty.
- `/health` reports degraded state accurately.
- The lint fails on a deliberately added `except: pass`, passes once removed.

## Done when
20 sites converted, self-check live, `/health` honest, lint enforcing, committed.
**Outbox must list every real bug the new noise exposed** — that list is the actual value of this card.
