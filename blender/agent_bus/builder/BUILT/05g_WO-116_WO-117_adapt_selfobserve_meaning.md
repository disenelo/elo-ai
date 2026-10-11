# 05g_WO-116 + WO-117 — **ADAPT · SELF-OBSERVE · SELF-INTERPRET · MEANING (rows 20, 22, 24, 25, 26)**

**Seat:** builder · **Priority:** P2 (after the rows below it unblock) · **Gate?** none
**These four are the ones marked BLOCKED. This card names exactly what unblocks each — nothing is waiting
on David, and nothing is waiting on a decision.**

---

## Why they read BLOCKED — the honest answer
Not because they're hard. Because **nothing writes eLo's own actions and outcomes back into his own
state**, so there is no *before* and *after* to compare. Every one of these needs a delta, and no delta
exists.

| Row | BLOCKED on | Card that unblocks it |
|---|---|---|
| 22 ADAPT | no measurable before/after | this card + `00_WO-096B` + `00b_WO-104` |
| 24 SELF-OBSERVE | `record_behaviour` / `update_habits` have **zero callers** | one-liner #4 (`000b_`) then this |
| 25 SELF-INTERPRET | reflection→self-model, autobiography, behaviour store | `05d_WO-115` + this |
| 26 MEANING | significance omits `outcome=` at both call sites | `03c_WO-101` + `05d_WO-115` |

**Row 26's blocker is literally two omitted keyword arguments:** `memory/journal_router.py:121` and
`faculties/significance/significance_faculty.py:144` both call `evaluate()` without `outcome=`, while
`significance_engine.py:167-174` accepts it and `:217-231` scores it. That's why MEANING is blocked —
not philosophy.

---

## WO-116 — SELF-OBSERVE + ADAPT *(rows 24, 22)*
`self/identity_meaning.py:53-83 derive_tendencies` **already runs live** (`server.py:2903-2905`).
**Two of its three inputs are permanently empty** — `record_behaviour` (`elo_self_model.py:508`) and
`update_habits` (`emergent_cognition.py:93`) have zero production callers; `server.py:3806` passes
`"topics": []`. Live state: `recent_behavior: {}`, `lifetime_threads: []`.

**Build:** write behaviour on every executed action (with its ACK outcome) → aggregate → feed the Executive.

**Test — §7's brutal one, verbatim:**
```
BEFORE   wall_jump confidence = 0.71
EXPERIENCE  attempt = success
REFLECTION  route = viable
AFTER    wall_jump confidence = 0.78 · known_route = true
```
**If nothing changes after experience, eLo has memory but has not demonstrated learning.** That is the
acceptance criterion — not a test count.

## WO-117 — SELF-INTERPRET + MEANING *(rows 25, 26)*
**Do not start until 21 · 23 · 24 · 101 are real.** These are emergent: they don't get built, they
**become true** when the layers beneath them work. Starting early produces a component with no inputs —
the exact fault this whole card exists to end.

**When the prerequisites land, this is the test:** eLo names a pattern in his own behaviour that is
traceable to real logged actions, and says why something mattered **with the significance score and the
outcome that produced it**. Anything he can't trace to state, he doesn't claim.

## Done when
WO-116: behaviour store non-empty on a real run · `derive_tendencies` returns something real · the §7
before/after delta demonstrably moves.
**Outbox: the before number and the after number. Nothing else counts.**
