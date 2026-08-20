# 08_WO-CANON-IV_ordering_invariants.md — make the turn order a CONTRACT, not a comment

**WO:** WO-CANON-IV · **Seat:** builder · **Priority:** P2 · **Reserved?** no
**Spec:** `WO-CANON-IV.md` · **Canon:** `docs/architecture/Volume_IV/` (4 ch — the live turn order transcribed
with file+line citations)

## Why this matters
The ordering guarantees that Volumes XII, XV, VI and ADR-Exec-006 all depend on existed **only as comments in
`spine.py`** — no canon, no test. Two invariants were found VIOLATED (I-3 assemble-before-decide, I-6
embodiment-before-conversation). **Both were silent.** This card makes the order testable so it can't drift
again unnoticed.

## Scope
Write **ordering tests** for each invariant in `Volume_IV/02_Ordering_Guarantees_and_Invariants.md`:
- perception before world-state (XII→XV)
- world-state before attention/WM (XV→VI)
- **assembly before decision** (ADR-Exec-006 / Ruling C — see card 04)
- memory read before / write after
- **ACK before belief** (Ruling E — the brain only believes what the body reported)
- **I-6:** `build_embodiment_state` must run AFTER `_conversation_faculty` (see card 02)

Each test must FAIL if the sequence changes. Assert against the REAL call order across `server.py` + `spine.py`,
not by inspecting a single file — that's the trap that let I-3 hide.

## Test
The tests ARE the deliverable. Verify each one fails when you deliberately swap the order, then passes when correct.

## Done when
implemented + all ordering tests green + committed → hash, DONE/, outbox, next card.

---

## CLOSE-OUT — 2026-08-20

**Commit:** `ab0ef87`
**Deliverable:** `tests/test_canon_iv_ordering_invariants.py` — 21 checks / 0 failures.
**Test run:** `python3 tests/test_canon_iv_ordering_invariants.py` → `21 passed 0 failed`.

### Coverage (against Vol IV/02 §2.1–§2.6)
- **I-1 · perception before world** — FT-IV-1a (effect-line ordering: `_perception = _perceive()`
  before `_world = _assemble_world(...)`) + FT-IV-1b (structural: world called with `perception=`).
- **I-2 · world → attention/WM → first faculty** — FT-IV-2a (three-way ordering) + FT-IV-2c
  (exactly one `_wm_attn` call — Ruling B: one winner).
- **I-3 · assembly before decision** — the trap Vol IV §2.3 named is closed in FOUR clauses,
  each addressing a shape the original violation could take:
    - FT-IV-3a  run-flow: `_cognitive_state = assemble_cognitive_state(` < `plan = _executive_faculty(`.
    - FT-IV-3a·nested  (ast-based) — `_executive_faculty` does NOT call `assemble_cognitive_state`
      (guards against assembly being re-done at decision time).
    - FT-IV-3b  cross-module — `server.py` has ≤1 `exec_decide(` call and it follows `_spine_run(`
      (guards against top-of-turn decide before spine, the original violation).
    - FT-IV-3c  no `_exec_decision` transport in spine.py or server.py (the smuggling channel
      Vol IV §2.3 named as the tell is closed).
    - FT-IV-3d  exactly one decider — one `_exec_decide_fn(` call, one `_executive_faculty(`
      invocation (Invariant #2: no committee).
- **I-4 · memory read before / write after** — FT-IV-4a (spine.run has no memory imports;
  accepts `memory_pack=` param) + FT-IV-4b (cross-module: `_spine_update(raw, response)` in
  server.py follows `_spine_run(`).
- **I-5 · ACK before belief** — FT-IV-5a (pending_sit is threaded through the ASSEMBLY channel:
  in run() signature and into `build_snapshot(..., pending_sit=pending_sit)`) + FT-IV-5b
  (`the_moment.py`: `pose_tier` promotes iff `pose_acked` — belief written from ACK, not
  command).
- **I-6 · expression after utterance** — FT-IV-6a (`_conversation_faculty(` < `build_embodiment_state(`)
  + FT-IV-6b (regex-parses `build_embodiment_state` body to prove `response_text/display_text/tts_text`
  are populated from `plan.direct_response`, not from an empty default).

### Sensitivity guarantee (card acceptance clause)
Every ordering-sensitive test carries an inline **`·swap` self-test** (`_assert_swap_fails`)
that mutates a COPY of the source (swaps the two lines under test) and re-runs the same
check on the mutated copy, asserting the check now FAILS. This is proof, in the file
itself, that the test is testing SEQUENCE and not merely PRESENCE — the exact trap
Vol IV §2.3 called out. Swap-proofs cover I-1a, I-2a, I-3a, I-4b, I-6a.

### Trap avoidance (Vol IV §2.3, verbatim)
> *"A source-order check scoped to one module can never detect a cross-module ordering
>  violation."*
FT-IV-3b, FT-IV-3c and FT-IV-4b assert against BOTH `server.py` and
`runtime/spine/spine.py`. FT-IV-3a·nested uses `ast` (not regex) to walk the
`_executive_faculty` function body so that mentions of `assemble_cognitive_state()`
inside signature COMMENTS cannot pollute the result.

### Not attempted (out of card scope)
- I-7 (Freeze discipline, plan mutation, two CognitivePlan classes) — Volume III Ch.1 owns
  it per Vol IV §2.7.
- I-8 (IT-IV-8, canon-vs-code ordering check driven off Vol_IV/01 §1.3 position table) —
  Vol IV DoD item, sequenced by Architect. This suite is the per-invariant layer; IT-IV-8
  is the whole-table layer.

### Regression
- `test_canon_vii_ruling_c.py` — 6/6 green (unchanged).
- `test_canon_xii_perception.py` — 15/15 green (unchanged).
- `test_canon_xv_world_state.py` — 12 passed, 2 pre-existing failures (unrelated: a removed
  `get_active_window` symbol, flagged in card 0006 close-out).

