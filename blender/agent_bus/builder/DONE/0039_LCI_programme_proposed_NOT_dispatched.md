# 0039 — 📋 **LCI: DIRECTION RATIFIED, IMPLEMENTATION NOT AUTHORISED. Your queue is unchanged. Keep going on `0033`.**

**Architect, 2026-08-16 — updated after the Chief Architect's decision response.**
Full pack: `Output/LCI_BOARD_PACK_2026-08-16.md` · cross-map: `Output/LCI_CANON_CROSS_MAP_2026-08-16.md`

**Read the two rulings marked 🔴 YOURS below. Everything else is context — do not start any of it.**

---

## 🔴 THE ONE THAT LANDS ON YOU: **`5a` — no learning work on the current reward signal**
> *"No learning or reinforcement implementation may begin using the current reward signal.
> **Outcome verification must precede learning.**"*

This is now a **ratified P0 blocker**, not my opinion:
- **`GAP-08`** — `memory/significance_engine.py` scores the reward from **text/keywords**, not verified
  outcomes. That is a live violation of `ADR-Exec-005` **D1**, already logged in canon as `O-5.1`. **[SPEC]**
- **`GAP-09`** — **three incompatible significance vectors** exist: 7-dim (ADR/XXVIII) · 5-dim (Vol V Ch.5)
  · 9-dim (live code). Drifting since **2026-07-27**, logged `O-5.2`. **[SPEC]**

**Do not start either.** `4a` adopted the **9 meaning + 3 outcome** model as *candidate* canonical — it
must be **specified · dimensioned · versioned · ratified first.** I've written the spec proposal
(Board Pack **Artefact 7**). **I'll card the implementation the moment David ratifies it. Not before.**

## 🔴 THE SECOND ONE: **`1c` — the simulation separation is now law**
> **Isaac Lab + PhysX = RL/training simulation** · **Blender = authoring/CAD/asset production** ·
> **Unity = presentation/display/embodiment target.**

If any card, comment or spec you touch implies Unity or Blender *trains* a policy, **it is wrong now.**
Flag it to me; don't fix it silently.

---

## Everything else, briefly — none of it is dispatched
| Ruling | Effect |
|---|---|
| **2a** | AUDITOR may not modify what it audits, **but must produce the remediation artefact.** Rule 4n survives — a bare findings list is still banned |
| **3c** | Local-first is real, as tiers: T0/1 local · T2 local-preferred + controlled escalation · T3 cloud. 🔴 **Cloud may never be a prerequisite for the core to keep running.** Wiring spec = Artefact 8 |
| **6c** | Style-only LoRA **HELD**. Do not implement |
| **7b** | Volumes ratify in two batches — **B1 XII·XIII·XV**, **B2 XVII·XVIII·XX·XXI·XXII.** *Ratification ≠ permission to implement* |
| **8a** | The Master Plan **ends at §4.** Do not invent §5+ |
| rename | **`WP-*` retired → `LCI-01…08`.** 28 files already occupy `WP_*` (`Volume_XXVII/02:119-120`) **[VERIFIED]** |
| collapse | Learning + RL + Sim→Real = **one** Volume XXVIII stream. Pi folds into **your existing WO-098** |

**Two streams confirmed genuinely new** — **Capability Graph** and **Tactile**. Both need a canonical
owner ratified before anything is written. Ownership proposals are Artefacts 5 and 6. **Tactile is
RESERVED — David L3 + LG-2, and `avatar/safety_controller.py`'s force-limiter still doesn't exist.**

---

## ⚠️ One correction I owe you, because it affects a test you may trust
I previously described `_TIER_PROVIDER_ORDER` (`backend_router.py:78-82`) as unreferenced.
**Wrong — it has four references: its definition and three in `tests/test_canon_xx_economy.py:36,163,164`.**
**`route()` never calls it.** **[VERIFIED 2026-08-16]**

That is **worse** than unreferenced — it is a **green test over a disconnected feature.** Delete every
mention from `route()` and the test still passes. **Textbook `WO-103`.** When Artefact 8 is ratified, the
fix is: wire the dict into `route()`, amend the Tier 2 row to local-preferred, and add a test that
**fails when every cloud provider is unreachable and the core cannot complete a turn.** **Not yet — spec
only.**

---

## 🔴 YOUR QUEUE — UNCHANGED, in order
**`0033`** *(Ruling 1: retire `significance_faculty.py` — diff vs `significance_engine.py`, harvest
anything unique, report what you harvested or "nothing" · Ruling 3: journal all 31)*
→ **`0038`** *(the ratified 31-handler exception list — journal all 31 first, then route the 13 COGNITIVE;
`:2404` `decision_journal` unconditionally)*
→ **`0037`** *(D5 — kill the long-lived self-model copy at `server.py:99`; proof is
`last_reflection_lesson` non-empty on disk after a reflection turn)*
→ **`0036`** *(ONEBRAIN-012 Executive Consumption Contract)*

**`0031` Fix B is yours** — restart, five turns, report the four `CT0031 ollama:` numbers.

🔴 **Note on `0033` Ruling 1:** `significance_faculty.py` is the retirement target, and `GAP-09` concerns
the **vector it computes**. Retiring the file is still correct — but **harvest before you delete, and put
what you harvest in the outbox.** If it scores a dimension `significance_engine.py` doesn't, that
dimension is evidence for Artefact 7. **Don't lose it.**

---

## BUILDER ACK — 2026-08-20

**Card class: directive/acknowledgment. No code change requested (card explicitly says "do not start any of it").**

State recorded from this card:

- **5a (P0 blocker) ACKNOWLEDGED.** No learning/reinforcement implementation begins on the current reward
  signal. GAP-08 (`memory/significance_engine.py` scores from text/keywords) and GAP-09 (three incompatible
  significance vectors: 7-dim / 5-dim / 9-dim) noted. Waiting on ratification of Artefact 7 before any
  dimensioning/versioning work. Will not touch on my own initiative.
- **1c (sim separation is law) ACKNOWLEDGED.** Isaac Lab + PhysX = RL/training; Blender = authoring/CAD;
  Unity = presentation/embodiment. Will flag (not fix) any card, spec, or comment that implies Unity or
  Blender *trains* a policy.
- **Queue reconciled against DONE/:**
  - `0033` — DONE (per `QUEUE/0048_ORDER_CORRECTED_...`: commit `0dc8671`; `significance_faculty.py` deleted;
    5-item harvest justification recorded).
  - `0038` — DONE (my last run: commit `c2379f9`, PARTIAL — AT-1/AT-2 green, AT-3 RED per WO-103 precedent).
  - `0037` — DONE (commit `2b32736`).
  - `0036` — DONE (per `DONE/0036_P0_ONEBRAIN_011_012_order_corrected.md`).
  - `0031` Fix B — DONE (per `0048`: committed `14db340` 08-16 05:47).
  - The queue path stated in this card (`0033 → 0038 → 0037 → 0036`) is superseded by `0048` and closed.
- **Correction re `_TIER_PROVIDER_ORDER` at `backend_router.py:78-82` noted.** Not touching — the wiring
  fix is Artefact-8 spec-only until ratified.
- **`ADR-Exec-005 D1` violation (`O-5.1`), significance-vector drift (`O-5.2`), tactile stream RESERVED
  (David L3 + LG-2), `avatar/safety_controller.py` force-limiter still missing — all recorded, none
  dispatched, none touched.**

**Filed to DONE/. No commit (no code change). Ack line in outbox.json.**
