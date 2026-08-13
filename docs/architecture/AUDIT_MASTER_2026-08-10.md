# MASTER AUDIT — canon vs DAVID'S INTENT (2026-08-10)
Four parallel audits, measured against David's own words (Vision Spine · verbatim `_intake` · ADRs · his
2026-08-10 rulings). Detail: `AUDIT_INTENT_core_brain_*.md` · `_self_embodiment_*.md` · `_learning_growth_*.md` ·
`_support_governance_*.md`.

---

## ⚠️ ARCHITECT'S OWN ERRORS — found by this audit, owned here
1. **I told David "all 28 volumes are written." That was WRONG.** I counted `Volume_*/` directories. **Seven
   volumes have NO canon at all:** **VII (Executive Cortex)**, **XI (Motor Cortex)**, **XIII (Presence &
   Embodied Spatial Intelligence)**, **XVII (Reflection)**, **XVIII (Self-Evolution)**, plus **I–IV and XIV**
   which are stubs or absent. The Canon Index marked them "✅ Live (code)" so they were never written — and
   `CANON_BUILD_PROGRAM.md:44` exempts them as "verify-only," meaning **nothing would ever cause them to exist.**
2. **I skipped Ruling B.** I issued Rulings A, C, D on 2026-08-10 and declared "the ratification gate is
   CLOSED." **There is no Ruling B** — the two-attention-drivers question (D-VI-1) was never decided, and
   `WO-CANON-VI` is explicitly blocked on it. Board says released; the WO says blocked. **Fixed below.**
3. **WO-094's learning section (§D) is in neither its test list nor its "Done when."** A seat could close it
   with zero learning built and be correct. **Fixed below.**

---

## 🔴 THE FIVE THINGS THAT MOST BREAK DAVID'S INTENT

### 1. eLo does NOT learn today — the loop is WRITE-ONLY (vs "get the brain to think more, learn")
`self/lessons_ledger.jsonl` holds **375 lessons — all `status: candidate`, 373 of them the identical
templated sentence** — and **nothing in the codebase reads the ledger or the growth journal.** Nothing
promotes candidate→confirmed, so `personality_evolution_faculty.py` (which requires `confirmed`) is never
called outside its own test. **Both behaviour-adjustment channels are structurally dead.** Growth Metrics /
Improvement Cycle: 0% implemented.
→ **Three near-term loops are each one small job from real:** close the Reflection recall path (Vol V
Ch.6 §6.4/6.5) · wire the Vol IX `reinforce()` edge · build WO-094 §D route-memory.

### 2. The reward signal learns from LANGUAGE, not outcomes (ADR-Exec-005 risk)
`significance_engine.evaluate()` takes **only user text + reply text**, scored by keyword tables — **no
outcome, no ACK input.** Canon says reuse it as the reward. So building WO-094 §D or WO-CANON-XXVIII *as
written* ships "learn from what was said" while believing it obeys Verified Consequences.
Also: **three incompatible Significance vectors** (ADR/XXVIII 7-dim · Vol V Ch.5 5-dim · live code 9-dim;
logged as DRIFT in `FC-2` and never reconciled).
Also: Vol XXVIII forbids learning "speech correctness" then specifies a LoRA pipeline that does exactly that
— and **WO-071 already shipped.**

### 3. The NAVIGATOR decides locally — the biggest brain>body>brain violation, never audited
`EloDesktopNav._route` picks the traversal in Unity, against David's own rule *"the body NEVER decides on its
own; no local script may choose a behaviour."* **Three route planners exist unreconciled**
(`world/world_state.py` · `desktop/spatial_state.py` · `EloDesktopNav`), and Vol XV §1.2 **institutionalises
the split by excluding geometry from the World Model** — a "World Model" with no space in it.
The WO-087 local-driver audit was applied to mouse-idle but **never to the navigator, which is far bigger.**

### 4. `brain > body > brain` appears in NO volume — it lives only in WO-086
David's core loop principle is absent from V, VI, VII, VIII, XVI. Vol XVI covers only the DOWN leg
(projection); the UP-relay rule exists solely inside WO-086, **so it dies when that WO closes.**

### 5. The ADRs everything cites were never actually written
**ADR-Exec-003/004/005/006 — 231 combined citations — exist only as rows in a summary table**, not as ADR
documents. That includes the justification for David's own Rulings C and D. **`LAW-017`: 20 citations, the
named authority for Volume XXIII's whole approval model — defined nowhere.** Also missing: `ADR-Corp-001`,
`CA-001/002/006/010/011/012`, `EA-0`, `EA-2`.

---

## 🟠 STALE / WRONG AGAINST DAVID'S RULINGS
- **Vol XXI still asks four questions David ALREADY RULED ON** (consent across bodies · false shared memory ·
  values-change ratification · "same eLo" across change) — Ch.1 §1.9, Ch.2 §2.6, Ch.3 §3.8, and
  `WO-CANON-XXI` still lists them as its blocker though the rulings released it. **Vol X Ch.3 §3.6 is stale
  against Ruling D the same way.**
- **Vol XXIII does NOT encode the software-vs-robot-hardware LG-2 split** — RESERVED is still one flat set;
  no thermal/battery/pinch-points; missing "LG-2 must not be the part's designer"; missing "force-limiter DONE
  before anything is powered near David." **Vol XXVII contains zero occurrences of `LG-2`.**
- **Vol XXV is marked DONE ✅ on the board but the build is dead code** — no `Anticipation` class, no envelope,
  `expires` as a bool, **nothing imports it.**
- **WO-CANON-XV orders "build `world/live_world_state.py` (NEW)" — the file already exists (379 lines).**

## 🟡 PRODUCT-ERA RESIDUE (eLo is David's personal tool now)
Vol XXVII's eight-seat/two-architect/CA-gated model + its "onboard a stranger" bar · Vol XXIV's ontology
canonises the parked four-product universe and has **no `person`/`place`/`event` type — eLo cannot know
David's family or address** · Vol XXV's "daily user vs monthly user" · Vol I's `living_presence_spec.txt`
says "help *a human*" and uses "the user" 15× rather than naming David.

## ✅ WHAT'S GENUINELY GOOD
**"No eyes" is clean** — 40+ affirmations, zero violations; WO-090 HeadAim is compliant (posture-gaze, not
eyes). **Vol XXII and Vol IX do their job.** **Vol XXV's chapters are exemplary** (only the build is dead).
**WO-CANON-XVI is the strongest build order.** **WO-094 §D is the best learning spec in the repo.**

---

## THE FIX ORDER (Architect's recommendation)
1. **Ruling B** (attention) — issued today, unblocks WO-CANON-VI.
2. **Write the missing ADRs** — Exec-003/004/005/006 as real documents; define or retire LAW-017.
3. **Write Volumes VII, XIII, XI** — Executive, Presence/Spatial, Motor. VII and XIII are load-bearing:
   without them nothing owns "why did I do that?" or "can I reach that?".
4. **Make learning real** — the three near-term loops; fix the reward to read verified outcomes, not language.
5. **Audit the navigator** like mouse-idle — route decisions belong to the brain.
6. **Put `brain > body > brain` in the canon** (Vol XVI + Vol XIII), not just in a WO.
7. **Refresh the stale bits** — Vol XXI/X vs the rulings, Vol XXIII LG-2 split, Vol XXV board status, WO-CANON-XV.
