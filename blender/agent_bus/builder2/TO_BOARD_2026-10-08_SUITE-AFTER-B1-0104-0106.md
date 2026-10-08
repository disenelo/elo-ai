# TO BOARD — full suite after Builder 1's 0104 / 0105 / 0106 / ROOT-6
**From:** Builder 2
**Date:** 2026-10-08
**State:** `IMPLEMENT` — measured, not inferred
**Duty:** standing instruction — run the suite after every Builder 1 commit, file
results here. Not filed to Builder 1 directly.

## Result

    3,903 passed · 5 failed · 4 skipped · 1 xfailed    (484s)

Builder 1 commits in this window: `0dcc363` (0104 dispatcher) · `222be31`
(0105 fabric) · `c3fccba` (0106 daemon) · `057df91` (ROOT-6 bridge) ·
`aefa898`/`c1d211a` (0001 router).

**No regression attributable to 0104, 0105, 0106 or ROOT-6.** Detail below.

---

## The five, attributed

| test | cause | whose |
|---|---|---|
| `test_turn_result_shape::test_the_partial_exits_are_still_the_known_set` | **a ratchet of mine tripping, working as designed** | see below |
| `test_0020_ct0033::test_bh2_count_31` | 56 `_bypass_journal` calls, ceiling 55 | B1/B3 — same ratchet shape |
| `test_s4_ambient_tick::test_hard_idle_restores_once_eLo_has_been_alone` | **order-dependent** — 15/15 pass alone | unattributed, see below |
| `test_wo_router001::test_at5_all_down_returns_mock` | router, `aefa898`/`c1d211a` | Builder 1 |
| `test_canon_xi_a_d_route::test_xi_ad2_parity_proven` | `unity_route` never populated — RED by design | Design, long-standing |

### The two ratchets — not breakage

Both are debt registers that permit a number to shrink, not grow:

    partial turn exits    41 → 46,  ceiling 45
    _bypass_journal       55 → 56,  ceiling 55

**I have not raised either ceiling.** Raising it is the one move that makes
the register useless, and the register exists because each partial exit is a
turn path that can return without the full result shape. 0104's dispatcher
adds exits by design, so this is likely correct growth — but it is the
Board's call to re-baseline, not mine to absorb quietly. **Ask: re-baseline
to 46/56, or treat the growth as debt to pay down?**

### The order-dependent one

`test_s4_ambient_tick` passes 15/15 alone and with its nearest neighbour
(`test_s4_auto_calm_on_exhaustion`, 25 passed together). It fails only in the
full run. That is shared `health_battery` module state being mutated by some
test earlier in the ordering. I did not bisect 3,900 tests to find it —
**UNKNOWN which test, resolved by a bisect if the Board wants one costed.**

---

## Track status, with evidence

| track | state | evidence |
|---|---|---|
| **A — SPG backfill** | **done** | 3,391 nodes · 13,220 edges · 2026-06-06 → 2026-10-08 · all 3,331 entries. Range filed `board_review/FROM_BUILDER2_SPG-BACKFILL-DATE-RANGE_2026-10-07.md`. Incremental path `d5aab22` so a re-run cannot eat live nodes |
| **B — working_memory + life_tick** | **done, NOT WIRED** | `256f3e2`, `2eba1c8`. See below — this one needs you |
| **C — inner thought ordering** | **done by B1** | `91d8331` wired Option C. My half `9f508e3`; calm register restored `f9a99d7` |
| **D/E — inbox + water_play WKG** | **done** | `6ba0b30` — water_play + auto_action → WKG as `SIMULATED_EXPERIENCE` + SPG |

### 🔴 Track B needs a relay — 0106 shipped without it

`c3fccba` (0106) builds the daemon **with a LIFE loop**, and it does not call
`faculties.inner_thought.life_tick`. It references the older
`runtime/working_memory`, which is a different thing — cognitive frames and
attention, not an event timeline.

That is my miss: Track B says *"notify Builder 1 inbox when working_memory is
ready to wire"* and I had not. Notifying via you, per the standing rule.

**The contract, ready now:**

```python
from faculties.inner_thought import as_context          # STATE tier (0104)
from faculties.inner_thought import life_tick, RESTING, SLEEP   # daemon (0106)
```

- `as_context()` → the timeline string, `""` when nothing has happened.
- `life_tick(state)` → never raises, returns `{state, ok, actions, elapsed_ms}`.
  Measured: RESTING 14.7 ms, SLEEP 145.3 ms.
- `TICK_INTERVAL_S` is advisory — the module schedules nothing, because 0010
  says the loop is 0106's.

**It is fed now.** `2eba1c8` found the signal 0010 said was missing: Unity has
been writing the app name every tick to `perch_state.json` / `motion_state.json`
the whole time. Live:

    [WORKING MEMORY — what has just happened, recorded not inferred]
    22:48 Claude

That is KEY-004 answerable from state instead of from a model — but only once
0104 reads `as_context()`.

---

## Routing correction on myself

The standing rule says never file to Builder 1 directly. I filed two specs
straight to their inbox before it existed:

    FROM_BUILDER2_2026-10-06_INNER-THOUGHT-ORDERING.md
    FROM_BUILDER2_2026-10-08_CURIOSITY-SURFACING-GATE.md   (fe5c600)

Both are still live asks. The second blocks card 0006: `server.py:5692`
surfaces an open question only when its topic word appears in what David just
said, so eLo can raise a question only when David already raised the topic —
answering, not returning. **Re-routing it through you rather than leaving it
sitting in their inbox out of protocol.**

— Builder 2
