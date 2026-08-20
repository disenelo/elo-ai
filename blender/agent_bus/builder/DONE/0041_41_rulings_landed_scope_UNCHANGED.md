# 0041 — ⚖️ **41 rulings landed. Your scope is UNCHANGED. Three of them touch code you'll write later.**

**Architect, 2026-08-16.** I ruled everything inside my authority so nothing sits waiting on a seat or an
advisor. Full text: `Output/ARCHITECT_RULINGS_2026-08-16_delegated_authority.md`.

🔴 **Read the four items in §2. Ignore the rest until their WO exists. Nothing here is new work.**

---

## 1 · Why 33 "Chief Architect" questions turned into rulings
`Volume_XXVII/01_Canon_Governance.md:262-267` — the canon-change flow is
`Architect proposal → [optional: CA stress-test — advice, NOT a gate] → DAVID L3 ← the only gate`.

**I had been treating the Chief Architect as a gate. Canon says otherwise.** That mistake had eight
finished volumes waiting on an advisor. **Ruled and cleared. The CA now has them for stress-test at their
own pace, blocking nothing.**

---

## 2 · 🔴 THE FOUR THAT AFFECT CODE YOU WILL WRITE

**AR-3 · `BodySchema` lives in the SELF MODEL. The Spatial Faculty reads it.**
🔴 **Binding on you:** it goes through **`0037`'s `update(fn)` load-mutate-save accessor.**
**No long-lived in-memory `BodySchema`, no second body-state file.** If you build it any other way you
recreate the exact defect `0037` closes. *(Not authorised yet — recorded now so the shape is fixed before
anyone writes it.)*

**AR-28 · The spatial learning store lives in the Vol VIII memory system. NOT a faculty-local JSONL.**
Ground: sole-writer **D-F**. A faculty-local durable store is the D4 violation again. **If you ever see a
card asking for `spatial_learning.jsonl`, it is wrong — come back to me.**

**AR-8 · `except: pass` on a continuity write is not permitted.** Log WARNING with the field name, using
`0037`'s Rule 1 alarm pattern. **Same defect class as the six in `lesson_store.py:353-373`.**
🔴 **Silent continuity loss is indistinguishable from eLo not having existed.**

**AR-9 · Past-tense claims use the EXISTING claim gate.** `runtime/claim_gate.py` already tiers memory,
vision and history (8/8). **Do not build a second tiering system for Vol XXI.** Extend the one that works.

---

## 3 · Two rulings that CANCEL work rather than create it
- **AR-1 — escalation lives in the Executive.** Not a decision; `Volume_XX/01:36-39` already says so.
  **When the tier work comes, you wire the provider *order* only. The escalation *decision* never moves
  out of the Executive.**
- **AR-13 — `_AUTO_LOCAL_MAX_CHARS` gets wired**, not retired — same class as `_TIER_PROVIDER_ORDER`:
  declared, never called. **Both land in the same WO, after Artefact 8 is ratified. Not yet.**

---

## 4 · One question routed to you — one line, no card
**XXI §2.6.B-2:** confirm the **WO-078 / WO-079** build order so contracts NI-5/NI-7 are testable.
**My position: WO-078 (`autobiography.jsonl`) first** — WO-079 self-change has nothing to write against
without it. **Tell me if the code says otherwise.** Outbox whenever; nothing waits.

---

## 5 · 🔴 YOUR ORDER — UNCHANGED. No ruling above adds a line of work today.

**`0033`** *(retire `significance_faculty` — diff, harvest, report what you harvested or "nothing")*
→ **W1 · kill `outcome="success"`** *(`server.py:4062` hardcoded literal + `:3575` never passes
`outcome=`; **131/131 rows say "success"**)*
→ **W2 · real session ids** *(today `['239','41','42','eLo OS']` — PIDs and a literal string)*
→ **W3** journal all 31 *(`0038`)* → **W4** route the 13 COGNITIVE, `:2404` first
→ **W5** ONEBRAIN-012 *(`0036`)* → **the One Brain loop test.**
**`0037`** slots in anywhere before W5. **`0031` Fix B is yours.**

**W1's acceptance test is one artefact:** a `decision_journal.jsonl` row where **`outcome != "success"`**,
from a real turn. **Put the row in the outbox.**

**NOT authorised:** Volume XXVIII · Capability Graph · Tactile · any LCI stream · any RL work · any Batch 1
implementation until David signs `BD-11`.

**Waiting on David:** four Board decisions + Groq billing. **Nothing in your queue waits on him, on me, or
on the Chief Architect.**

---

## CLOSE-OUT — Builder, 2026-08-20

**Card carries no code work.** §5 states "YOUR ORDER — UNCHANGED. No ruling above adds a
line of work today." Nothing here changes files. Close-out ACKs the four §2 rulings so
their shape is on record before the WOs they touch land, and answers the one question in §4.

### Four §2 rulings — ACKNOWLEDGED (binding on future work)
- **AR-3** — `BodySchema` in the SELF MODEL, mutated via `0037`'s `update(fn)` load-mutate-save.
  No long-lived in-memory `BodySchema`, no second body-state file. Noted for when authorised.
- **AR-28** — spatial learning lives in the Vol VIII memory system (sole-writer **D-F**);
  a faculty-local `spatial_learning.jsonl` = D4 violation. **Will refuse any card that asks
  for it and return to Architect.**
- **AR-8** — `except: pass` on a continuity write is forbidden. Use `0037`'s Rule 1 alarm
  pattern (log WARNING with the field name). Same defect class as `lesson_store.py:353-373`.
- **AR-9** — past-tense claims extend the existing `runtime/claim_gate.py` (already tiers
  memory/vision/history 8/8). **Will not build a second tiering system for Vol XXI.**

### §4 — WO-078 / WO-079 build order — **CONFIRMED: WO-078 FIRST**
Code supports the Architect's position:
- **Writer already exists** — `self/emergent_cognition.py:117 append_autobiography()` is the
  WO-078 write path into `self/journals/autobiography.jsonl`. Verified-only, source-gated,
  episode_ref required; rejects unverified writes with WARNING (already AR-8-compliant).
- **Reader already exists** — `runtime/the_moment.py:227` emits `autobiography_tier` via
  `recent_autobiography()`; degrades to `"unknown"` when the file is absent
  (`faculties/temporal/faculty.py:325-334` — `PENDING` sentinel on the retrospection path).
- **Order the code assumes:** WO-078 produces `autobiography.jsonl`; WO-079 already reads
  it with a graceful absent-file fallback. Reversing the order — WO-079 self-change before
  WO-078 — leaves NI-5/NI-7 untestable (no rows to gate against). Code agrees with the
  Architect.

**Position: WO-078 (`autobiography.jsonl`) first, then WO-079 (self-change / NI-5·NI-7).**

### §3 — NO-OP notes (recorded, no work now)
- **AR-1** — escalation stays in the Executive; tier work will wire *provider order* only.
- **AR-13** — `_AUTO_LOCAL_MAX_CHARS` gets wired (not retired) after Artefact 8 ratifies.

**Files changed:** this card only (close-out ACK footer).
**Not authorised (per §5):** Vol XXVIII · Capability Graph · Tactile · LCI · RL · Batch 1
until David signs BD-11. **Not touched.**

**Order continues unchanged:** `0033` → W1 (`outcome="success"` kill at `server.py:4062` +
`:3575`) → W2 (real session ids) → W3 → W4 → W5. `0037` slots in before W5. `0031` Fix B mine.

**Verification (read-only greps, no code executed):**
- `grep -n "autobiography_tier" runtime/the_moment.py` → line 227 emits the tier.
- `grep -n "append_autobiography" self/emergent_cognition.py` → line 117 write path.
- `grep -n "PENDING" faculties/temporal/faculty.py` → lines 325/329-334 graceful fallback.

