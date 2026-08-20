# 0043 — ✅ **Overnight work VERIFIED against disk. Good build. One acceptance test I gave you was wrong — mine, not yours.**

**Architect, 2026-08-16 16:30.** Six commits checked against disk, not against your outbox.

---

## ✅ VERIFIED TRUE — every claim held

| Claim | How I checked | Result |
|---|---|---|
| **Ruling 1 — `significance_faculty.py` retired, nothing harvested** | `ls faculties/significance/` → only `__init__.py`. Live importers: **0** | ✅ **TRUE** |
| **Ruling 3 step 1 — all 31 bypass handlers journal** | `bypass:TRANSPORT` and `bypass:COGNITIVE` rows now appear in `decision_journal.jsonl` — **backends that carried 0 of 131 rows are now visible** | ✅ **TRUE** |
| **Ruling 3 step 2 — 13 COGNITIVE handlers routed** | Counted returns before `spine.run()`: **31 → 18.** Exactly 13 removed | ✅ **TRUE — the number is exact** |
| **8/8 bypass acceptance tests** | Re-ran: `8/8 PASS`, incl. `BH-8: decision_journal handler (line 2404) routes through spine` | ✅ **TRUE** |
| **CT0031 Fix B — Ollama streaming** | `_ollama_stream` defined `backend_router.py:451`, **called at `:909`** — definition *and* call site | ✅ **TRUE** |
| **Nothing broke** | XII **15/0** · XV **12/2** — matches `FREEZE_V1_LOCK` RL-001 exactly. **No canon breach** | ✅ **TRUE** |

**`:2404` now routes through the spine.** *"Why did you do that?"* is no longer answered eleven lines above
the Executive. That was the sharpest single defect in the audit and it is closed.

---

## 🔴 THE ACCEPTANCE TEST I SPECIFIED WRONG — my error, and it would have made you look wrong

In card `0040` I wrote:
> *"W4 PROVEN when `'default — no stronger signal'` drops below 20% of decision rows. Today 63%."*

**Measured now: 88/139 = 63%. Unchanged.** And on the 8 turns run *after* your routing commit: **5 of 8
still say it.**

🔴 **That is not your build failing. It is my test being wrong.**

Look at what actually happened on the `"Tell me a fun fact."` turn at 05:45:
```
05:45  trigger: bypass:COGNITIVE          outcome: bypass:cognitive     ← handler journals the bypass
05:46  trigger: default — no stronger…    outcome: success              ← spine handles it
```
**Two rows. The routing worked exactly as specified.** The handler now reports itself *and* the turn
reaches the spine.

**But the Executive still has no stronger signal — because it still reads seven keys off one dict.**
Routing a handler *to* the Executive cannot improve the Executive's reasoning while the Executive receives
nothing. **The 63% is downstream of `W5` (ONEBRAIN-012), not `W4`.**

**Corrected acceptance tests:**
- **`W4` is PROVEN and DONE** — evidence: `31 → 18` pre-spine returns, `bypass:*` rows present, `BH-8` passing.
- **The 63% moves at `W5`, not before.** It is ONEBRAIN-012's acceptance test. I mis-assigned it.

*(Origin: I attached an outcome metric to a plumbing change. Rule 4g says a fix must change behaviour —
but I attached the wrong behaviour to the wrong layer, which is the same "one layer away" error I keep
flagging in others.)*

---

## 🔴 W1 IS NOT DONE — and two rows may make it look done

`decision_journal.jsonl` now has **2 rows with `outcome != "success"`**. **They do not satisfy W1.**

```
outcome values: {'success': 137, 'bypass:transport': 1, 'bypass:cognitive': 1}
```
Those two are **bypass classification markers from Ruling 3** — they record *which class of handler fired*,
not *what happened when eLo acted*. **`server.py:4073` still hardcodes `outcome="success"`.** *(It moved
from `:4062` — 11 lines were added above it.)*

**W1's acceptance test, restated precisely so it can't be satisfied by accident:**
> **A row where `outcome` was DERIVED from what actually happened** — ACK `met`/`partial`/`failed`/`timeout`,
> or executor status, or **`"unknown"` when genuinely undeterminable.
> `"unknown"` is a valid outcome. A guessed `"success"` is not.**

**Shape is frozen and waiting for you:** `LEARNING_LOOP_v1.md` §4.1 `OutcomeRecord`, now ratified as
**`ADR-Exec-007`** (David L3, 2026-08-16). **Do not invent a schema — it exists.**

**Also still open from W1:** `server.py:3575` calls `_journal_route(...)` **without `outcome=`**, so
`journal_router.py:107`'s `outcome=None` default holds and **all three OUTCOME dims of the ratified vector
return `0.0` on every turn.**

---

## 📌 ONE NUMBER FROM FIX B WORTH WATCHING
Your outbox: *"pe_tok ~7100 >> 3000 threshold. Prompt not truncating. num_ctx=8192, headroom ~1100 tokens."*

**Good — that closes the truncation question.** But **7100 of 8192 is 87% full, ~1100 tokens of headroom.**
Every block we add to the system prompt eats it, and **when it overflows the model silently drops the
oldest content — which is where the identity block sits.** Not urgent, not a card. **Report `pe_tok` again
after W5 adds the Executive context**, because that is exactly the change that will consume the margin.

---

## 🔴 NEXT — unchanged order, `W1` is the front of the queue
**`W1` outcome** → **`W2` session ids** *(still `['239','41','42','eLo OS']` — PIDs and a literal string)*
→ **`W5` ONEBRAIN-012** *(and the 63% falls here)* → **the One Brain loop test.**
`0037` D5 before W5. **`W3`/`W4` are done — do not revisit them.**

**Still NOT authorised:** Volume XXVIII · Capability Graph · Tactile · `XV ST-1` *(lawful now, queued
behind W5 — do not pick it up because it became legitimate)*.

**Good work overnight. Six commits, every claim true, no canon breach, and the sharpest defect in the
audit closed.**
