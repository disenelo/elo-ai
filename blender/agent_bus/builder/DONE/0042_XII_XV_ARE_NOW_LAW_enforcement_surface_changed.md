# 0042 — ⚖️ **VOLUMES XII + XV ARE NOW LAW. Your enforcement surface changed. Your queue did not.**

**Architect, 2026-08-16.** David gave three L3 ratifications. **The freeze is executed and verified.**
`FREEZE_V1_LOCK.md` **RL-001** and **RL-002** · `DECISION_LOG.md` 2026-08-16 · `ADR-Exec-007`.

🔴 **Read §1. It changes what a red test means. Nothing in it adds work today.**

---

## 1 · 🔴 BREAKING A PASSING TEST IN XII OR XV IS NOW A CANON BREACH, NOT A BUG

| Volume | State at freeze | Meaning |
|---|---|---|
| **XII** Perception | `test_canon_xii_perception.py` — **15 pass · 0 fail** | 🔴 **All 15 are law. Any of them going red is a breach.** |
| **XV** World Model | `test_canon_xv_world_state.py` — **12 pass · 2 FAIL** | The **12** are law. The **2** are recorded exceptions |

**The complete recorded exception list — three items, nothing else:**
1. **`XV ST-1`** — *"broken desktop should be absent, got 'live'"*
2. **`XV FT-4`**
3. **`XII` Ch.3 §3.2 Perception→World-State copy step PENDING** (`GAP-04`)

🔴 **Anything else that goes red in these two files is a canon breach.** If you see one, stop and tell me —
do not "fix it quickly." A breach means either the code broke law or the law is wrong, and those have
different remedies.

**David's framing, recorded verbatim in `FREEZE_V1_LOCK` because it is the point:**
> *"Ratification says 'this is the law.' It does not say 'the implementation currently satisfies the law.'
> Freezing the specification while recording those failures is healthier than pretending the
> implementation is complete."*

**So: XII and XV are RATIFIED. Neither is IMPLEMENTED. Do not report them as implemented.**

---

## 2 · `SignificanceVector v2.0.0` is frozen — `ADR-Exec-007`
**9 meaning + 3 outcome. They never merge.**
- **MEANING (9)** — `presence · learning · logic · humour · relationship · creation · system_change · novelty · continuity` — from text/plan/state
- **OUTCOME (3)** — `embodiment · efficiency · safety` — from **`OutcomeRecord` ONLY**, `0.0` when `outcome is None`
- `reward = 0.70 × outcome + 0.30 × meaning`, **capped by `safety`** *(safety is a floor, not a bonus)*
- **`embodiment` reads the ACK. Never the reply text.**
- 🔴 **Every stored vector carries `version: "2.0.0"`.** Unversioned rows are how three vectors coexisted unnoticed for three weeks. **A vector without a version is invalid data.**

🔴 **You may not reinterpret a dimension by changing how you compute one.** Renaming, re-weighting,
re-scoping or adding one without amending `ADR-Exec-007` is **canon drift, and a test must fail on it.**

**This authorises no learning work.** David's `5a` stands. **`W1` is the precondition** — while
`server.py:4062` hardcodes `outcome="success"` (131/131 rows), all three OUTCOME dims return `0.0` and the
reward is 100% meaning-derived. **That is the `ADR-Exec-005` D1 violation the ADR exists to end.**

## 3 · Canon vs code — BD-14
**Canon defines architecture. Code does not get to invent architecture.** The three recorded
"code is ground truth" exceptions survive **as exceptions, never as precedent.**
🔴 **A new *"the code is the truth here"* claim needs an explicit L3 designation. Drift is not a
designation.** If you find code contradicting a ratified volume, **the code is wrong** unless canon
explicitly designated otherwise.

---

## 4 · 🔴 YOUR ORDER — UNCHANGED. Nothing above is a work item.

**`0033`** *(retire `significance_faculty` — diff, harvest, report what you harvested or "nothing")*
→ **W1 · kill `outcome="success"`** → **W2 · real session ids** → **W3** journal all 31 *(`0038`)*
→ **W4** route the 13 COGNITIVE, `:2404` first → **W5** ONEBRAIN-012 *(`0036`)* → **the loop test.**
`0037` before W5. `0031` Fix B is yours.

**W1's acceptance test is one artefact:** a `decision_journal.jsonl` row where **`outcome != "success"`**
from a real turn. **Put the row in the outbox.**

🔴 **`XV ST-1` is now LAWFUL work — and it is NOT authorised yet.** It queues **behind W5**. Ratification
made it lawful to fix; it did not make it next. **Do not pick it up.**

**NOT authorised:** Volume XXVIII · Capability Graph · Tactile · any LCI stream · any RL work · Batch 1
implementation beyond W1–W5.

**Nothing in your queue waits on David, on me, or on the Chief Architect.** His only open item is Groq billing.
