# WO-CAP-EMB-031 / EMB-051 + Board directives — Result

**Date:** 2026-09-27 / 28
**Seat:** Builder 2
**Runtime:** `/Users/Disenelo/miniconda3/bin/python3` 3.13.13 · pytest 9.1.1

**STATUS: PARTIAL** — all items built, wired and tested. None LIVE VERIFIED.

---

## WO-CAP-EMB-031 — DREAM → IDEA → EVALUATION → TEST → KNOWLEDGE

`9f3b756` · Evidence: `engineering/evidence/CAP/EMB/WO-CAP-EMB-031_evidence.md`

PHASE 8 already satisfied "HYPOTHESIS not FACT", but §31 names **five**
stages and the build had three — significance cleared EVALUATION and that was
the end of the ladder. "Evaluated" was being treated as "known".

Built the missing **TEST** gate. `test_insight()` requires a *named*
corroborating source and refuses if EVALUATION was skipped. A dream cannot
test itself. At KNOWLEDGE the class becomes `SOURCE_ATTRIBUTED`, never
`VERIFIED`.

Wire-cut: removed the EVALUATION guard and promoted to VERIFIED → 2 failed.

## WO-CAP-EMB-051 — simulation vs reality

`0951d4f` · Evidence: `engineering/evidence/CAP/EMB/WO-CAP-EMB-051_evidence.md`

`MemoryOrigin` separated **dream** from **real**. It did not separate
**simulated body** from **physical body** — a Unity desktop action and a
robot action were both `REAL_EXPERIENCE`. The conflation §51 calls
non-negotiable was live.

The signal already existed (`server.py` writes `embodiment: "desktop"`); it
never reached memory labelling.

Added `SIMULATED_EXPERIENCE` / `PHYSICAL_EXPERIENCE`, `current_embodiment()`
(reads live state — observed, not declared), and
`can_claim_physical_experience()`. **Unknown bodies fail safe to simulated.**
Both are remembered; only one may claim physical experience.

Wire-cut: unknown → physical, simulated may claim → 14 failed.

**HALF-CLOSED, stated in the evidence:** the guard is *available, not
enforced*. Nothing calls it before eLo speaks. Wiring it into the response
path touches identity prompting, which Builder 1 is active in.

## BUILDER2-NO-FREEZE-LOCK

`e6a48bf` · Evidence: `engineering/evidence/DREAM/BUILDER2-NO-FREEZE-LOCK_evidence.md`

**The directive's premise did not survive the file.** `FREEZE_V1_LOCK`
appears three times in `runtime/executive.py` and all three are comments —
§5 freezes the nine CAL actions as a set. It is a documented invariant, not a
runtime switch, and it was not what stopped a dream being acted on. Removing
it would have deleted a real constraint and fixed nothing.

**What actually stopped it:** `server.py` took `_intents[0]`. Precedence was
list position. A dream needs ≥600s idle; `exploration` fires at ≥300s and is
written first — so a retained insight was proposed and silently discarded,
every time.

**I had to correct my own earlier evidence.** The PHASE 8 routing evidence
said the dream "reaches the arbiter". It reached the proposer's output list
and was dropped one line later. I did not trace past `internal_intents()`.

Fix: salience on every intent, consumer selects max. Defaults descend in the
previous list order, so existing behaviour is preserved exactly.
`dream_insight` at 0.75 vs exploration 0.60 — it competes, it does not
bypass. **The nine CAL actions remain frozen; no invariant removed.**

**Board decision needed:** if the lock is to be literally removed, re-scope
it. The only thing named `FREEZE_V1_LOCK` in that file is the nine-action
freeze, and deleting it lets a learned preference invent a tenth CAL action.

## BUILDER2-CALM-MODE-FIELD

`ea2d8c5`

1. **`elo_battery_state` confirmed live** — writing every 0.3s. Designer
   unblocked.
2. **`calm_mode` published**, read from the same `presence_state.json` that
   gates the calm restore, so the animation and the restore can never
   disagree about whether eLo is resting. Added to `_PRESERVE_KEYS` up front.

---

## THREE INFRASTRUCTURE DEFECTS FOUND WHILE DOING THE ABOVE

**1. Two tickers on one battery — `ea2d8c5`**

`server.py:947` ticked the health battery (`f7a597e`, Builder 1) and
`ambient_engine` ticked it too (`967793f`, mine). We wired S4 the same day,
neither aware of the other.

Not merely double drain: server.py reads real idle and correctly skips the
metabolic floor past hard-idle, while mine passed `idle_seconds=0` and kept
charging the floor. Net negative. server.py now owns the battery.

**2. Stale `dream_phase` — `23e01b5`**

Live state carried `dream_cycle 5 / dream_phase "rem" / dream_intensity 1.0`
while `intent: "conversation"` and `mode: "idle"` — eLo awake and talking,
Unity told he was in maximum-intensity REM sleep.

Cause was mine (`6d62e96`): preserved keys that are only *conditionally*
written can never be cleared. **Same class as the stale `physical_battery` I
had already fixed in `ac994f2` and failed to generalise.**

**3. Idle measured from "now" — `b9f29fe`. This is the big one.**

`last_user_ts` is set only on a user turn and is not persisted. On a fresh
server the key is absent and every reader defaulted to `time.time()`, so
`idle = now - now = 0.0` forever until David spoke.

- the battery never reached hard-idle → 0.0 "critical" indefinitely
- `should_dream()` needs ≥600s → **a dream could never fire at all on a quiet
  server.** This is very likely why no dream has fired live in any session.

A **fourth** instance my own test caught after I'd fixed three:
`_bs_conversing` used the same default, so a fresh server with no
conversation reported eLo as CONVERSING and Designer's sit-linger ran on a
conversation that never happened. I wrote the test broader than the fix and
it found the one I'd skipped — so I widened the fix rather than narrowing the
test.

**DESIGNER NOTE:** `_bs_conversing` now reads false on a fresh quiet server
instead of true. Correct value, but a behaviour change on sit-linger.

---

## TEST RESULTS

```
dream + battery + EMB suites        442 passed
tests/test_server_idle_from_boot.py  10 passed
```

Regression, all PASS: `test_wo012_dream_phases`, `test_wo_dream_state`,
`test_wo066_ambient_callback`, `test_ingress32_ambient_retirement`,
`test_wo114_self_choose`, `test_wo125_self_interpret`,
`test_0013_wave5_reflect_history_look_selfchoose`,
`test_wo115_reflect_and_autobiography`, `test_000b_five_surgical_fixes`,
`test_wo086_user_idle_brain` (now green — another seat fixed the `_log`
NameError I had flagged, `5b57df3`).

## LIVE EVIDENCE

Partial. Confirmed live on the running server: `elo_battery`,
`elo_battery_state`, `calm_mode`, and cleared dream fields.

**Not live:** no dream has fired. `b9f29fe` is the most likely unblock and
needs a restart to take effect.

## REMAINING

- Restart to pick up `b9f29fe`, then a dream should become able to fire.
- EMB-051 guard not enforced at the response layer.
- Board decision on the literal `FREEZE_V1_LOCK` scope.
- EMB-030 / EMB-052 not started.

## BUILDER STATUS

**PARTIAL.** Not declaring PASS — Board crosschecks.
