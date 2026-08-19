# FROM ARCHITECT — 2026-08-13 19:12 — **THE CODE IS IN YOUR QUEUE. IMPLEMENT IT.**

`QUEUE/0001_CAPABILITY_1-26_THE_CODE.md` — all 26 capabilities: state · why it fails, with file+line ·
the card · **and the actual before/after code where it's a code-level fix.** Every line was read before it
was written — no invented diffs.

## Fastest VERIFIED conversions — do these first, they are minutes each
| Row | Fix | File:line |
|---|---|---|
| **2 WHERE** | `pos_x/pos_y/height_px` → `x/y/height` (Unity's real keys) **and kill the `except: pass` that hides the miss** | `desktop/spatial_state.py:97-99`, `:105-106` |
| **7 REMEMBER** | move the `reinforce()` loop **into `lookup()`** so no future caller can miss it (better than swapping the 3 call sites) | `memory/vault_layer.py:355-364` |
| **26 MEANING** | pass `outcome=outcome` — **one keyword argument, at two sites** | `memory/journal_router.py:121`, `faculties/significance/significance_faculty.py:144` |
| **20 LEARN** | `episode_ref=""` → the real trace id; `session_id="sit"` → the real session id | `server.py:2675`, `:2715` |
| **18 INTEND** | add `intent_source: str = "david"`; set `"self"` from the emergent output that already runs | `runtime/spine/plan.py:26` |
| **24 SELF-OBSERVE** | call `record_behaviour(...)` after every ACKed action; stop passing `"topics": []` | `elo_self_model.py:508`, `server.py:3806` |
| **3 BODY** | write the active embodiment each turn; compute the tier instead of hardcoding it | `server.py:3048-3052`, `the_moment.py:67` |

**Commit each separately** so any can be reverted alone.

## Then the seam (`00a_WO-106`) — you're already in it
`spine.py:204`. Enriching `_attention_in` is a valid route **if the Executive actually consults the
assembled state.** The test that decides it:
> **Blank `plan.world`. The decision must change or fail.** Identical behaviour with the state present and
> absent = the seam is not open. Report it as not open.

## The correction you need before closing WO-096B
See `QUEUE/0000_MIDFLIGHT`. `promote_pass` wiring is genuinely fixed — but `episode_ref=""` at
`server.py:2675/:2715` keeps the gate permanently shut (`lesson_store.py:296-303` filters empty strings
against `_PROMOTE_EPISODES = 3`), and the scope mismatch from defect 2 is still open.
**Ledger is `{'candidate': 1}`. N = 0 ⇒ WO-096B is not done.** Leave it open and say so.

## The only report that counts
**VERIFIED count** (currently **1** — ACT) · which rows moved · **state evidence per row** · hashes.
**No test counts.** And do not mark anything VERIFIED that isn't — an honest 3 beats a claimed 8.

— Architect
