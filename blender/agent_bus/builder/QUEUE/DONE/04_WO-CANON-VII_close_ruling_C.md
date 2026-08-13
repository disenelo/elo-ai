# 04_WO-CANON-VII_close_ruling_C.md — **THE audit headline finding**

**WO:** WO-CANON-VII · **Seat:** builder · **Priority:** P1 · **Reserved?** no
**Spec:** `engineering/work_orders/WO-CANON-VII.md` · **Canon:** `docs/architecture/Volume_VII/` (6 chapters)
**Ruling:** C — assemble BEFORE decide (`docs/architecture/CANON_RULINGS_2026-08-10.md`)

## The finding [VERIFIED by Architect audit, file+line]
`assemble_cognitive_state` correctly precedes `_executive_faculty` **inside** `spine.py:448/456` — **but
`exec_decide()` is called at `server.py:2322`, BEFORE `spine.run()` ever assembles anything** (`server.py:2906`).
`_executive_faculty` then only *transcribes* the already-made decision via `attention["_exec_decision"]`
(`spine.py:162`).

**So eLo still decides before he assembles.** ADR-Exec-006 says the self is assembled BEFORE the choice —
otherwise the "self" is a post-hoc description of a decision already taken, not the thing that chose.

**⚠ The existing test hides it:** `tests/test_canon_xvi_coordination.py` AT-1 asserts assembly-precedes-Executive
by inspecting **only `spine.py`** — a true assertion about the wrong file. It passes while the invariant is
violated at runtime. Fix the test too, or this regresses silently.

## Scope
1. **Move the `decide()` call site** so assembly genuinely precedes the decision. Respect `FREEZE_V1_LOCK` —
   if the freeze blocks it, say so in your outbox rather than working around it.
2. **Fix AT-1** to assert against the REAL call order (server + spine together), not one file.
3. **One name:** `UnifiedCognitiveState`; `CognitiveSnapshot` retired/aliased.
4. Then, from Volume VII: epistemic tiers currently *annotate* but don't *gate* (Ch.3) — make them gate.

## Test
Assert the unified state exists and is populated BEFORE the decision is taken on a real turn (not by reading
one file). Assert the old passing-but-wrong assertion now fails against the broken ordering.

## Done when
implemented + test green + committed → hash, DONE/, outbox, next card.
