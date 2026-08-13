# ADR Index — `docs/architecture/adr/`

Architecture Decision Records for eLo OS, as **real documents**. Opened 2026-08-10 to close the
hole found by `AUDIT_MASTER_2026-08-10.md` §5: *"the ADRs everything cites were never actually
written"* — ADR-Exec-003/004/005/006 carried **231 combined citations** while existing only as rows
in a summary table, and `LAW-017` was cited 25 times with no definition in the repo.

**Nothing in this folder is new policy.** Each file formalises a decision the canon already relies
on, sourced to its origin. Where a citation implied something that could not be confirmed, the ADR
states the rule conservatively and carries an **OPEN — needs David** section.

**Relationship to `DECISION_LOG.md`:** the Decision Log remains the append-only ledger and keeps its
summary rows. These files are the addressable long-form home those rows point at.

---

## Written (this folder)

| ID | Title | File | Status | Ratified |
|---|---|---|---|---|
| **ADR-Exec-001** | Verified Executive Authority — Verified Speech | [`ADR-Exec-001_Verified_Speech.md`](ADR-Exec-001_Verified_Speech.md) | ACCEPTED · CANON · LAW | 2026-08-03 (CA + David L3) |
| **ADR-Exec-002** | Single Cognitive Truth | [`ADR-Exec-002_Single_Cognitive_Truth.md`](ADR-Exec-002_Single_Cognitive_Truth.md) | ACCEPTED · CANON · LAW | 2026-08-03 (CA + David L3) |
| **ADR-Exec-003** | Embodied & Situated Cognition (5 principles) | [`ADR-Exec-003_Embodied_Situated_Cognition.md`](ADR-Exec-003_Embodied_Situated_Cognition.md) | ACCEPTED · CANON · LAW | 2026-08-05 (David L3) |
| **ADR-Exec-004** | Situated Self (Runtime Invariant #5) | [`ADR-Exec-004_Situated_Self.md`](ADR-Exec-004_Situated_Self.md) | ACCEPTED · CANON · LAW | 2026-08-05 (David L3) |
| **ADR-Exec-005** | Learning Through Verified Consequences | [`ADR-Exec-005_Learning_Through_Verified_Consequences.md`](ADR-Exec-005_Learning_Through_Verified_Consequences.md) | ACCEPTED · CANON · LAW | 2026-08-06 (David L3) |
| **ADR-Exec-006** | Executive Assembly — The Moment | [`ADR-Exec-006_Executive_Assembly_The_Moment.md`](ADR-Exec-006_Executive_Assembly_The_Moment.md) | ACCEPTED · CANON · LAW | 2026-08-06 (David L3); amended by Ruling C 2026-08-10 |
| **LAW-017** | Approval Scope & Runtime Composition | [`LAW-017_Approval_Scope.md`](LAW-017_Approval_Scope.md) | Part B §B4 = David L3 2026-08-10; Part A reconstructed | see PROVENANCE in the file |

**Reading order for a new seat:** 001 → 002 → 003 → 004 → 006 → 005 → LAW-017.
(001 is the founding honesty rule; each of 002/003/004 extends it into a domain; 006 is the
assembly that makes them one; 005 governs what may change over time; LAW-017 governs who may
approve what.)

## Also fully written, but in `DECISION_LOG.md` (not duplicated here)

`ADR-0001` (Faculty Bus envelope + 7 laws) · `ADR-0002` (Unified faculty lifecycle) ·
`ADR-0003` (Volumes XXIII–XXVII become Canon) · `D-A…D-M` · `D-PRESENCE` · `D-SESSIONS` ·
`D-LANES` · `D-VOL-V-READY` · `D-BUILD-NOW` (supersedes `D-FREEZE`) · `FC-1` · `FC-2`.
David's 2026-08-10 rulings live in `../CANON_RULINGS_2026-08-10.md`.

---

## 🔴 STILL MISSING — cited but never written

These could **not** be reconstructed. They are listed so the hole is visible instead of silent.
None of them should be invented; each needs either a located source, an author, or a retirement.

| ID | Cited where | What it is claimed to be | Recommendation |
|---|---|---|---|
| **ADR-Corp-001** | `_intake/SOURCE_2026-08-08_self_model_becoming.md` — *"Canon: ADR-Corp-001"* for **WO-080** (Company Knowledge Interface) | The canon authority for eLo reading his own company state from a permissioned read-only sandbox | **Write it or retire the citation** before WO-080 is authored — a WO is currently specced against a canon reference that does not exist. |
| **CA-001** | `DISPATCH_BOARD.md` (awaiting David L3) | Chief-Architect recommendation: DISENELO Operating Model | Locate the CA source doc; if it lives in `Output/`, intake it verbatim. |
| **CA-002** | `DISPATCH_BOARD.md` (awaiting David L3) | Chief-Architect recommendation: Creative Production House (incl. the in-house creative-AI decision) | As above. |
| **CA-006** | `01_PRINCIPLES.md` line 108; `WO-PRIN-1` | *"Decision Taxonomy (EA-0 CA-006 Rec 8)"* — the recommendation WO-PRIN-1 pairs with | Locate; WO-PRIN-1 cites a recommendation number with no record. |
| **CA-010** | `DISPATCH_BOARD.md` (relayed to CA for review) | A CA review/recommendation set | Locate or retire. |
| **CA-011** | `01_PRINCIPLES.md`; `AGENT_HANDOFF_PACKETS.md`; EA-3 §4/§6 | The "missing engines" list that EA-3 renames to faculties; company-memory pattern | Partially recoverable **from EA-3's restatement only** — the original CA-011 doc is not in the canon. |
| **CA-012** | `00_MANIFESTO.md` §75; `01_PRINCIPLES.md` | *"Chief Co-Architect alignment review (CA-012) — Manifesto vs. the real `elo-ai`"* | The Manifesto quotes its conclusions; the source doc is absent. |
| **EA-0** | `00_MANIFESTO.md` §112; `01_PRINCIPLES.md` §106 | *"EA-0 §14 already unifies them"* (mind runtime + company runtime) | **Not located.** Cited with a section number, which implies a real document somewhere. |
| **EA-2** | `AGENT_HANDOFF_PACKETS.md`; `00_MANIFESTO.md` | Runtime architecture predecessor to EA-3 | Likely `Output/DISENELO_RUNTIME_ARCHITECTURE_EA2.md` + `Output/DISENELO_EA2_ELOAI_ALIGNMENT_REVIEW.md` — **outside the repo** (D-I lane). Intake verbatim to make the canon self-contained. |
| **EA-3** | 24 citations across canon + WOs | Universal Runtime; **the source of LAW-017** | `Output/DISENELO_UNIVERSAL_RUNTIME_EA3.md` — **exists, outside the repo.** Intake verbatim. |
| **ADR-0001 / 0002 / 0003** | Widely | Faculty Bus envelope · lifecycle · Vols XXIII–XXVII | **Written** — full sections in `DECISION_LOG.md`. Listed here only because the audit brief grouped them; they are **not** a hole. Optional: mirror into this folder for uniform addressability. |
| **Ruling B** | `AUDIT_MASTER_2026-08-10.md`; `CANON_RULINGS_2026-08-10.md` | One attention driver (Vol VI) | **Written** 2026-08-10 (was omitted from the first pass), in `CANON_RULINGS_2026-08-10.md`. Not a hole; noted because the gap A → C → D is visible in the file. |
| **D-C, D-D** | — | Never existed; the `D-<letter>` series runs A, B, *skip*, E | Cosmetic. Record the gap; do not back-fill. |
| **LAW-001 … LAW-016** | — | **Do not exist anywhere** (`elo-ai/` or `Output/`) | See `LAW-017_Approval_Scope.md` §PROVENANCE. **Do not invent sixteen laws.** |
| **DEC-EMERGENCE** | `00_MANIFESTO.md` line 101 — *"✅ RATIFIED by David 2026-07-29"* | A ratified decision | Ratified but **never appended to `DECISION_LOG.md`** — violates Vol XXVII §1.1 (one append-only ledger). Append it. |

### Known ID-scheme problem (recorded, not fixed here)

Six incompatible ID schemes are live simultaneously: `ADR-NNNN`, `ADR-Exec-NNN`,
`ADR-Executive-NNN`, `D-<letter>`, `D-<WORD>`, `CA-NNN`, `EA-N`, `FC-N`, `LAW-NNN`, `DEC-<WORD>`,
plus untagged `Ruling A/B/C/D`. Volume XXVII §1.9 Q2 proposes `ADR-YYYY-NNN` — **still unratified**.
Canonical spellings used in this folder: **`ADR-Exec-NNN`** (with `ADR-Executive-NNN` as an alias).

---

*Folder opened 2026-08-10 by the Lead Architect. Files here are Markdown canon only — no code.*
