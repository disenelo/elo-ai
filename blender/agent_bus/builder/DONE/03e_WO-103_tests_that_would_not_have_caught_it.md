# 03e_WO-103 — 🔴 THE ROOT CAUSE. Fix the test discipline or every card above rots again.

**WO:** WO-103 · **Seat:** builder · **Priority:** P1 — **but apply its rule to every card you do from now on**
**Gate?** none. **Origin:** Architect readiness verification 2026-08-13.

## Why this card exists — read this even if you skip the rest
Five separate builds shipped, passed their tests, were marked DONE, and **changed nothing**:
learning loop · temporal faculty · significance outcomes · the gaze cue · EmbodimentState.

They failed the same way every time: **the test called the new component directly instead of running the
live path.** `promote_pass` has a green test that invokes `promote_pass`. `faculties.temporal` has 3 green
tests and is imported by nothing real. `evaluate(outcome=…)` is tested with an outcome no caller passes.

**So "DONE" came to mean "the card's tests are green" instead of "the behaviour changed."** That is the
whole failure, and it is mine — I accepted that definition. This card changes it.

## The rule, from now on, on every WO
> **A test must fail if the feature is disconnected.**
> If the component could be deleted from the live path and the test would still pass, it is not a test.

Concretely, every card ships **at least one test that runs the real entry point** — the turn loop, the
server route, the actual publish — and asserts the observable outcome. Direct unit tests are welcome
*in addition*, never *instead*.

## Fix these three now

### 1. AT-1 — the ordering test that inspects a file
[VERIFIED] `tests/test_canon_xvi_coordination.py:48-76` reads `spine.py` with `readlines()` and checks line
order. **It never touches `server.py`, which is where the real order lives.**
Good news: the ordering is currently **correct** — `spine.run()` at `server.py:2330`, `exec_decide` only a
fallback at `:2349`. **But AT-1 would pass just the same if that regressed tomorrow.**
**Fix:** assert assemble-before-decide **at runtime** — instrument the real turn and assert the observed
sequence. Ruling C is the invariant; prove it on the live path.

### 2. An orphan-faculty alarm
Nothing currently notices that a faculty is registered, tested, and never imported by the turn. **Add a
test that fails when a faculty in `faculties/` is not reachable from the live path.** `faculties.temporal`
must fail it today — that's the proof it works.

### 3. A wiring test for publish channels
`gaze` was emitted and then silently stripped because it wasn't in `_PRESERVE_KEYS`. **Assert every key the
writer can emit survives a round-trip through a partial write.** (Overlaps WO-100 — do it once, properly.)

## Done when
The three tests exist and **fail against today's code where they should** (AT-1 runtime version passes;
orphan-faculty test fails on `temporal` until WO-CANON-XXV lands — that failure is correct, leave it red
and say so in the outbox). Committed, hash reported.

**From this card onward: no WO closes without a test that would have caught its own bug.**
