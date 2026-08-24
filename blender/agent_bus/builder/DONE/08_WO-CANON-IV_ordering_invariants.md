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
