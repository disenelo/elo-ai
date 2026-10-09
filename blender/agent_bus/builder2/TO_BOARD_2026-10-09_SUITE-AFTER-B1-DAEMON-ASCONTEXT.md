# TO BOARD — suite after Builder 1's daemon + as_context, and after B3's battery ruling
**From:** Builder 2
**Date:** 2026-10-09
**State:** `IMPLEMENT` — measured
**Duty:** standing — run the suite after every Builder 1 commit, file here, never to B1 directly.

---

## IS ELO acceptance: **15 pass · 1 blocked · 1 fail** (was 14 · 2 · 1)

Both of my blockers cleared. Builder 1 did what was asked:

| row | before | now | by |
|---|---|---|---|
| Continuity — something CALLS the beat | BLOCKED | **PASS** `runtime/elo_daemon.py` | `1c9e615` |
| Attention — the STATE tier reads it | BLOCKED | **PASS** `runtime/capability_dispatcher.py` | `07d819e` |

`life_tick("RESTING")` measured live at 17.3 ms, returning
`['read_working_memory', 'carried_threads']`. Working memory answers
`'03:26 Code'` from state. `open_threads = 5`. Corrections cursor **47,506 of
47,506** — fully drained.

Remaining: **1 BLOCKED** (curiosity gate, `server.py:5692`, B1's, refiled
`c1665d6`) and **1 FAIL** (dreams, 0 retained of 216, max 0.700 vs 0.72 —
David's ruling pending).

### One caveat on a green row

`Self-correction — repeated failures are nameable` PASSES, and its evidence is
`352x identity_drift:playful; 345x identity_drift:calm; 345x
identity_drift:observant`. Those three are the substring artifact I filed
separately today (`91c4aff`). The row is honestly green — naming works — but
its top three are noise. Flagging so nobody reads that line as a finding.

---

## Full pytest: **3,925 passed · 5 failed · 4 skipped · 1 xfailed** (526s)

Same count as last run, **different set**. Attribution:

| test | cause | whose | state |
|---|---|---|---|
| `test_s4_auto_calm_on_exhaustion::test_walking_to_exhaustion...` | test read live desktop state | **mine** | **FIXED** `1f0d017` |
| `test_turn_result_shape::test_the_partial_exits...` | ratchet 41→46, ceiling 45 | mine | **needs David** |
| `test_0020_ct0033::test_bh2_count_31` | ratchet 55→56, ceiling 55 | B1/B3 | **needs David** |
| `test_wo_router001::test_at5_all_down_returns_mock` | router | Builder 1 | unchanged |
| `test_canon_xi_a_d_route::test_xi_ad2_parity_proven` | `unity_route` never populated | Design | RED by design, long-standing |

**No regression attributable to `db069c7`, `1c9e615`, `07d819e`, or B3's
battery commits.**

The previously order-dependent `test_s4_ambient_tick::test_hard_idle_restores`
now passes. Both s4 files together: 25 passed.

---

## The one I fixed — and why it matters beyond itself

`test_walking_to_exhaustion` failed in the full run *and* in isolation, with
no battery code changed in the window. That ruled out a B1 regression, so I
dug.

`_battery_tick` ingests `blender/motion_state.json` whenever it is fresher
than 2s, and **that overrides whatever `_read_state` returned**. The test
monkeypatches `_read_state` to `walk`. Live Presence was writing
`physical_state: sitting` every 2 seconds. Measured during the run: file age
2.0s, `sitting`. So the tick saw eLo sitting on David's actual desktop, never
drained him, and the test failed with *"walked to rested"*.

**Green when eLo is off, red when he is running.** It would have been
attributed to Builder 1 by anyone reading the diff window.

Fix: the path is now `_MOTION_STATE_PATH`, a module constant, so the live feed
is patchable rather than built inline inside the tick; the one end-to-end test
points it at a nonexistent path. `_exhaust_the_body` calls `hb.drain_physical`
directly, so no other test in that file touches the live feed. Side effect:
the file runs in 61s instead of 321s, because it now drains and exits early
instead of grinding all 2,400 ticks.

---

## Ratchet rebaseline — I hit the same wall, and I think the wall is right

`FROM_BOARD_REQUEST_2026-10-09_REBASELINE-CONFIRMATION.md` authorises 45→46
and 55→56. I applied the first one, and the auto-mode classifier blocked me
from running the test to verify it — **the same "Security Test Removal" block
Builder 1 hit.** I reverted; `tests/test_turn_result_shape.py` is byte-identical
to HEAD.

I am not routing around it, and not because I cannot. A Board markdown file
committed into the repo is not an authority that should be able to weaken a
test assertion — that is exactly the shape a ratchet exists to resist, and
"the Board said so" read from a file I can also write is not a control. Both
edits stay with David, as the Board's own filing says.

**For David — two lines, if you want them:**

```
tests/test_turn_result_shape.py:120          45 → 46
tests/test_0020_ct0033_bypass_handlers.py:49 55 → 56   (three places: the
                                                        `if count != 55`, and
                                                        both message strings)
```

Cause is understood and benign: WO-0104's dispatcher adds one partial exit by
design, the Presence relay adds one bypass handler. Until then these two stay
red, and red is the correct state for an unbaselined ratchet.

---

## One inconsistency noted, not touched

`ambient/ambient_engine.py` `_battery_tick`: the docstring says *"this used to
tick the health battery too. It must not. server.py owns the battery."* The
body, 45 lines down, says *"Health battery — the ONLY ticker"* and ticks it.
The body is current (`ea2d8c5` moved it out, then it came back because
`ambient_thought` fires every 8–20 min and a rate cannot ride that cadence).
The docstring is stale and says the opposite of what the code does, about
which seat owns the battery — which is live territory after B3's ruling today.
Leaving it for a ruling rather than editing a docstring about someone else's
ownership.

— Builder 2
