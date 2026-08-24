# 0074 — WO-CANON-VII · Executive Cortex. Three live decisions are standing on an unfinished volume.

**Seat:** builder (+ Architect for the canon half) · **Priority:** 🔴 P1 · **STATE: AUTHORISED**

## Builder called this, and Builder is right
> *"Vol VII being unfinished means decisions about routing authority are being made without a canonical
> ground to stand on. That's the highest-priority structural debt in the CANON family given what's actively
> running."*

**Three live items all sit on Volume VII, which is `status: REVIEW · implementation: PARTIAL`:**

| Live item | What it needs from VII |
|---|---|
| **CAL routing order** (`executive.py:219`) | the canonical statement of the Executive's routing contract |
| **`0065` WO-BRAIN-AUTHORS** | *"Brain applies the model"* — VII is where that authority is defined |
| **C1 — 29 pre-Executive early returns** | VII is what says they are wrong |

🔴 **And it changes something I was doing.** I have been holding the CAL routing order as a David decision
for two days. **Asking him to rule on the Executive's test order while Volume VII is unratified is asking
him to rule without a ground.** VII first, then the ruling is obvious or unnecessary.

## Scope — canonise what is TRUE, then close the gap
1. **Read `runtime/executive.py` and write down what it actually does.** VII must describe the live
   Executive, not an idealised one. Where they differ, that difference IS the finding.
2. **The routing contract:** the 9 CAL actions are frozen; **the ORDER they are tested in is not in the
   freeze and has never been canonised.** That omission is why `:219` drifted unnoticed. **Canonise the
   order, or canonise that the order is deliberately unspecified — but say which.**
3. **Authority boundary:** what may reach David without passing the Executive. C1 says 29 paths currently do.
   VII should state whether that is ever legitimate.
4. `Volume_VII/` already has 5 chapters and `runtime/executive.py` is live — **extend, don't restart.**

## 🔴 Boundaries — this is the most sensitive volume in the canon
- **`FREEZE_V1_LOCK.md` §5 stands.** The 9 CAL actions and the positive-momentum rule do not change.
- **Do NOT change routing behaviour on this card.** Canonise first. Behaviour change is a separate ruled card.
- **D3 stands:** the Executive stays frozen; `plan.lesson_id = ""` is not to be quietly reopened here.
- Anything that would change *who eLo is* stops at a **proposal**.

## Test
1. Every branch in `_conversation_action()` is described in VII, in order. Any undocumented branch = fail.
2. VII names which of C1's 29 early returns are legitimate.
3. `audit_status` moves off `OPEN` with a stated position on the routing order.

## Done when
VII describes the live Executive truthfully · the routing-order question has a written position ·
the CAL decision brief is rewritten to sit **on** VII. **Then David rules — once, with ground under it.**

## Result
- **commit:** `f8575b7`
- **undocumented branches found:** 0. Every branch in `_conversation_action()` (B1–B22) is
  described in Ch.1 §1.3.1 with source-line anchors. The 2 pre-CAL branches inside `decide()`
  (A1–A2), the 3 post-CAL WO-106 overrides (C1–C3), and the loop-guard (D1) are also enumerated.
  **Total: 28 dispatch points documented, 1:1 with `runtime/executive.py:138-406`.** B20 (`:227`)
  flagged as verified-unreachable dead code.
- **position on routing order:** STATED in §1.3.2. The nine-action set stays FROZEN; the
  `executive.py:149` docstring priority (`ANSWER > BUILD > ... > SILENCE`) is **retired from
  canonical status** — it did not describe live dispatch and its presence masked B18/`:219`.
  The **live A/B/C/D order enumerated in §1.3.1 IS canon** until superseded by a David-ruled
  behaviour-change card. Behaviour unchanged (0074 boundary). OQ-VII-8 tracks the single
  David L3 ratification the card DOD calls for.
- **C1 legitimate/illegitimate split:** RULE stated in §1.6.1; enumeration deferred to FINDING C1
  audit work (still NOT AUTHORISED per David 2026-08-18: *"Audit first. Correction second."*).
  Legitimate = all three of (a) not user-facing text eLo authors, (b) does not touch state the
  Executive later reconciles, (c) not a query about eLo's own state/self/reasoning. Anything
  failing any one is a second decider forbidden by ADR-Exec-001. "Why did you do that"
  file-reader named as paradigmatic violation of (c). VII does not enumerate the 29 — that
  is FINDING C1 audit work under David's own gate.
- **audit_status:** `OPEN` → `POSITION_STATED` (00_Metadata.md).
- **Files touched:** `docs/architecture/Volume_VII/00_Metadata.md`,
  `docs/architecture/Volume_VII/01_The_Executive_and_One_Plan_Per_Turn.md`. **No code touched
  (0074 boundary: Canonise first. Behaviour change is a separate ruled card).**
