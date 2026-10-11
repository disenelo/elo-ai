# 0025 — 🔴🔴 **A SECOND PERMANENT MEMORY STORE IS LIVE AND CANON-INVISIBLE.** Plus: Ruling B is fiction.

**Architect, 03:15.** Volumes VI · VII · VIII · IX audited. **Three findings outrank everything currently
in the queue.**

---

## 🔴🔴 P0-1 · `core/memory_engine.py` — 1,146 lines, live, load-bearing, **owned by no volume**
Vol VIII §4.35-40: *"there is exactly one place bytes become durable memory."*
Vol VIII §4.113-117: *"none of these four may open its own permanent-memory store… Any new store claiming
to 'remember' for the relationship is a fork of Vol VIII and must be reconciled here."*

**It is false on every conversational turn.**
- `core/memory_engine.py:46` — its own store: `memory/interactions.json`; `:177-179` writes it directly
- **Live on the response path:** `server.py:3518-3519` (`store_interaction`, `load_registry`),
  `server.py:3322-3323` (`retrieve`, `retrieve_by_project`)
- Also imported by `core/core_engine.py:35`, `world/world_state.py:138,277`, `core/visual_memory.py:145`
- **It never touches the chokepoint** — grep for `write_memory` returns only `memory/vault_layer.py`,
  `memory/memory_faculty.py` and tests. `core/memory_engine.py` does not appear.
- Its **five categories** (Identity · Project · Creative · World · User) contradict Vol VIII's **four
  biological types** (episodic · semantic · procedural · emotional)
- There is even a root shim — `/memory_engine.py:2` — `from core.memory_engine import *`
- **Canon mentions: zero in Vol VIII.** The only references anywhere are `Volume_V/02:133` (citing a
  **non-existent path**) and a passing note in `Volume_XV/01:77`

🔴 **And `tests/test_canon_viii_memory.py` asserts sole-writer *within `memory/`* — it is structurally
blind to `core/`. The test passes while the invariant fails.** That is worse than having no test.

**This is the largest single finding of the audit.** Runtime Invariant 7 (Memory Ownership) is violated in
production, and has been the whole time.

**Needs David L3 — three options, "leave it" isn't one:**
(a) **Retire** — migrate `interactions.json` into the vault, route callers through `MemoryFaculty.submit()`
(b) **Absorb** — name it in Vol VIII as an explicit non-durable interaction log with a migration path
(c) **Split** — two legitimate stores with a written boundary *(not recommended — this is Ruling A's
two-world-graphs problem again, and Ruling A retired the duplicate)*

**Builder, regardless of the ruling — do this now:** extend `test_canon_viii_memory.py` to scan the
**whole repo** for durable-write sites, not just `memory/`. **A test that cannot see the violation is the
defect.**

---

## 🔴 P0-2 · Ruling B is satisfied at the docstring level and nowhere else
`wm_winner` is **the user's raw input truncated to 80 characters** (`spine.py:441` — `item=raw[:80]`).
The Executive's only use of it is `executive.py:313`:
```python
if _wm_winner in ("creation", "build") and action == "reflect":
```
**That fires only if David types the single word "build" or "creation".**

**And the competition has a predetermined winner.** `spine.py:443-445` hardcodes the scores:
raw input = `0.35·0.5 + 0.40·0.5 + 0.25·0.4` = **0.475**; memory = **0.400**. **Raw input always wins.
There is no competition.**

More: `wm_mode`/`wm_budget` are dead keys · `carry_wm()` has no non-test caller and
`continuity/wm_carry.json` doesn't exist · SEED re-runs **every turn** so `frames` never exceeds 1 and
capacity/eviction/pinning never execute · `core/attention.py` was never renamed as Ruling B required.

**Removal test: delete `spine.py:416-461` and the only observable change is one dead dict key.**

⚠️ **`Volume_IV/01:515` asserts "✅ Satisfied" and `Volume_IV/02:99` calls it "the sole attention driver."
Both are false.** And `tests/test_wo_rows_4_6_16.py:114` passes `wm_winner="build"` as a **hand-made
fixture the production wiring cannot produce** — it verifies a path reality never takes.

**David L3:** reopen Ruling B (unimplemented) or retract it (accept `core/attention.py` as the driver).
**A ruling on the books that code contradicts is worse than no ruling.**

---

## 🔴 P0-3 · WO-109 fixed one violation by creating another — **my verification missed it**
I counted row 7 REMEMBER as VERIFIED because `reinforce()` moved into `lookup()`. **It does now run — and
it puts a durable file write on the response path**, which Vol VIII forbids **twice**:
- `04:70` — *"Retrieval runs in the response path… **reading only; durable writes never happen in the hot loop**"*
- `03:126` — the volume's own instruction for this exact fix: *"integration-window, **not hot-loop**"*

Three defects: **wrong lane** (hot-loop write) · **wrong trigger** — §3.4 requires *"retrieved **and
actually used**"*, the code reinforces on *retrieval*, so a record surfaced and discarded is strengthened
identically to one that shaped the answer, **inverting the forgetting curve** · **silently swallowed**
(`vault_layer.py:344-345 except: pass`) — a permanently failing reinforce is invisible while decay runs
uncountered.

**Fix:** move reinforcement behind the Executive's *use* signal, in the integration window (pairs with
`0024` CT4V-01). Log the failure.

---

## ✅ Two corrections to the record — one of them is mine
1. **Volume VII is NOT ratified.** I briefed the auditor that it was. **Only Volume V is L3 RATIFIED**
   (`00_CANON_INDEX.md:72`). Vol VII is `status: REVIEW`. Downstream volumes cite VI and VII **as though
   ratified** — that needs David's confirmation that the review state is intentional.
2. **Ruling C IS closed in code** — `server.py:2368-2400`, `spine.py:171-172`, and
   `tests/test_canon_vii_ruling_c.py` exists. **But four canon locations still say it's open**
   (`Volume_VII/00:101-106`, `02:131-150`, `02:268`, `01:454`) with six stale line numbers.
   **A volume that understates delivered capability causes closed work to be re-issued.** Architect's to fix.

## Scores this batch
**VIII 64 · VI 67 · VII 71 · IX 76.** *(Vol IX is the most honest volume audited — its stated
implementation status matches code.)* **16 of 28 audited; all still below the 75 gate except IX.**

## Order
`P0-1` test scope fix (immediate, small) → `P0-3` reinforce lane → `P0-2` awaits David's ruling on B →
then `0022` CT4V-07.
