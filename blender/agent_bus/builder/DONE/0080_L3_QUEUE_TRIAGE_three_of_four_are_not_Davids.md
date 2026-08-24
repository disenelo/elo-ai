# 0080 — Your L3 queue: **1 of 4 is David's.** Two are yours. One was ruled this morning.

**Seat:** builder · **Priority:** P1 · **STATE: AUTHORISED**

Before anything reaches David it gets checked against the spec and the ADRs. Checked all four.

| Item | Verdict | Evidence |
|---|---|---|
| **`WO-CANON-II` FT-4 / D-4** | 🟢 **NOT DAVID — YOURS.** Build it. | `Volume_II/00_Metadata.md:92` states it outright: **"D-4 (owning seat, not David)."** And `01_How_eLo_Reasons.md:252`: *"Where that hook sits is **the Executive owner's decision**."* **You are the Executive owner. Decide it.** |
| **`WO-CANON-XXVIII` gate** | 🟢 **ALREADY LIFTED — David 2026-08-21.** Build it. | *"Again I do not want any fucking gates."* He set the Presentable-v1 gate 2026-08-06 and removed it today. Volume metadata updated. **RESERVED still covers RD-3 robot locomotion only — safety, not sequencing.** |
| **`WO-CANON-XIV` Ch.3 F-1** | 🟠 **REAL, but it is an ADR before it is a David question.** | `Volume_XIV/00_Metadata.md:86` — *"ADR resolving XIV ↔ XXIII ownership **+ David's confirmation**"*. **Two steps, and you own the first.** Write the ADR proposing the ownership split, cite `ADR-Exec-002` (Single Cognitive Truth). David confirms a written position — he does not invent the split. |
| **`WO-CANON-XI` §A/§D OQ-1.2** | 🔴 **GENUINELY DAVID.** | `01_Motor_Cortex_and_the_Body_Contract.md:390` — *"**David L3 — changes a contract he signed**."* Adding `route` + `issued_by` to `move_command` alters an interface he ratified. **That is his and only his.** |

## 🔴 XXVI is NOT blocked — your report is stale, second time
`D-XXVI-A` was **ruled by David this morning: BOTH.** The drafted default stands as written:
> *"stated outranks learned; learned updates only from verified gate decisions; silence →
> explore-within-canon (never fabricate David's taste)."*

`_intake/SOURCE_2026-08-21_DAVID_D-XXVI-A_ruling.md` · card `0078`. **Build it.**

## What to do now
1. **`WO-CANON-II` D-4** — decide the hook location and build it. It is explicitly yours.
2. **`WO-CANON-XXVIII`** — build. Gate gone.
3. **`WO-CANON-XXVI`** — build to the ruled default.
4. **`WO-CANON-XIV` F-1** — write the ADR, then David confirms **one written position**.
5. **`WO-CANON-XI` §A/§D** — the only one that goes to him raw. **Send it as one line with the before/after
   contract, not as an open question.**

🔴 **Standing: before you put anything in the L3 queue, grep the spec and `docs/architecture/adr/`.**
Three of these four were already answered on disk. `ADR-Exec-005` alone is cited 116 times and I ignored it
for four days — that is the mistake this check exists to stop.

## Result
- D-4 hook location decided + built:
- XXVIII built:
- XXVI built:
- XIV F-1 ADR drafted:
- XI §A/§D one-line brief ready for David:

---

## CLOSED

✅ CLOSED 2026-08-21 — triage delivered; WO-CANON-II APPROVED. `test_canon_ii_cognitive_principles.py` 13/1-gap `b087c8b`. Remaining known-gap FT-4/D-4 (refusal hook) recorded in COMPLETION_LOG.

*Closed by the Lead Architect against COMPLETION_LOG evidence, 2026-08-21.*
