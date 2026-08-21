---
chapter: 4
title: "Governed Index — the routable map of canon governance"
volume: XXVII
status: IMPLEMENTATION READY
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PENDING
audit_status: OPEN
built: 2026-08-21
---

# Chapter 4: Governed Index

> **This index points. It does not restate.** For each governance concern there is one row naming the
> authoritative file and section. The content lives there; the index tells you where to look.

---

## §4.1 Governance concerns — authoritative locations

| Concern | Authoritative file and section |
|---|---|
| **Canon vs ADR vs Audit** | [`docs/architecture/Volume_XXVII/01_Canon_Governance.md §1.1`](01_Canon_Governance.md) |
| **Change process (D-M)** | [`engineering/work_orders/CHANGE_CONTROL.md`](../../../engineering/work_orders/CHANGE_CONTROL.md) |
| **8-item Definition of Done** | [`docs/architecture/00_CANON_INDEX.md §Definition of Done`](../00_CANON_INDEX.md) |
| **Engineering standards** | [`engineering/standards/`](../../../engineering/standards/) |
| **WO lifecycle (DRAFT→READY→BLOCKED→IN_PROGRESS→IN_REVIEW→DONE)** | [`engineering/work_orders/CHANGE_CONTROL.md`](../../../engineering/work_orders/CHANGE_CONTROL.md) |
| **Release / review / freeze** | [`docs/architecture/Volume_XXVII/03_Release_and_Review_Process.md`](03_Release_and_Review_Process.md) |
| **Versioning** | [`VERSIONING.md`](../../../VERSIONING.md) |
| **Freeze discipline** | [`FREEZE_V1_LOCK.md`](../../../FREEZE_V1_LOCK.md) |
| **Contracts / envelope standard** | [`docs/architecture/Volume_V/CONTRACTS.md`](../Volume_V/CONTRACTS.md) |
| **Dispatch / board** | [`engineering/work_orders/DISPATCH_BOARD.md`](../../../engineering/work_orders/DISPATCH_BOARD.md) |
| **Completion / sign-off** | [`engineering/work_orders/COMPLETION_LOG.md`](../../../engineering/work_orders/COMPLETION_LOG.md) |
| **ADR ledger** | [`docs/architecture/DECISION_LOG.md`](../DECISION_LOG.md) |
| **Canon master map** | [`docs/architecture/00_CANON_INDEX.md`](../00_CANON_INDEX.md) |
| **Approval scope (LG-2 / David L3)** | [`docs/architecture/adr/LAW-017_Approval_Scope.md`](../adr/LAW-017_Approval_Scope.md) |
| **Coding standards** | [`engineering/standards/coding.md`](../../../engineering/standards/coding.md) |
| **Documentation standards** | [`engineering/standards/documentation.md`](../../../engineering/standards/documentation.md) |
| **Testing standards** | [`engineering/standards/testing.md`](../../../engineering/standards/testing.md) |
| **Architecture standards** | [`engineering/standards/architecture.md`](../../../engineering/standards/architecture.md) |

---

## §4.2 Four rules enforced by this index

1. **A promotion not reflected in `00_CANON_INDEX.md` did not happen.** The affected volume and the Index
   are updated in the same pass.

2. **Canon changes only via the Architect, by ADR** (D-LANES, `CHANGE_CONTROL.md`). No seat writes
   canon unilaterally.

3. **Decision IDs are immutable and append-only.** Superseded is marked in place (`— superseded YYYY-MM-DD`),
   never deleted. Governed by: [`docs/architecture/DECISION_LOG.md`](../DECISION_LOG.md).

4. **Self-approval is forbidden. DONE is conferred only in `COMPLETION_LOG.md`, with David's sign-off.**
   A `DISPATCH_BOARD.md` line is a *status*, never a conferral.

---

## §4.3 OPEN REGISTER — unruled governance questions

Every question below is recorded and named. Unruled items are recorded here, not used as blockers.

| ID | Question | Recommendation | Decider | Status |
|---|---|---|---|---|
| GOV-OQ-1 | `LAW-001`–`LAW-016` do not exist. Keep `LAW-017` as the sole law, or back-fill 16? | **Do not back-fill** — inventing laws to fill a gap is worse than a sparse numbering. | David L3 | PENDING |
| GOV-OQ-2 | `LAW-017` covers two distinct scopes (O-17.1). Split into `LAW-017a`/`LAW-017b`, or keep combined? | Keep combined — 25 citations would need updating for marginal clarity gain. | David L3 | PENDING |
| GOV-OQ-3 | Governance-DoD variant — does the 8-item DoD in `00_CANON_INDEX.md` bind governance docs? | Yes, apply it as written. | Architect | PENDING |
| GOV-OQ-4 | Standards home — is `engineering/standards/` permanent, or should it migrate to `docs/`? | Keep `engineering/standards/` — it is referenced by 15+ files; migration is churn. | Architect | PENDING |
| GOV-OQ-5 | Release cadence for personal-use mode — what triggers a "release"? | David feels it is coherent. No cadence needed. | David L3 | PENDING |
| GOV-OQ-6 | 103 pre-cutoff WOs lack "Files to TOUCH" — sweep to backfill, or report-only? | Report-only (G-3 reports the backlog count). Backfilling is archaeology, not governance. | Architect | PENDING |

> **Rule:** a GOV-OQ entry here is not a gate. The work proceeds; the question is recorded for future resolution.

---

## §4.4 G-4 known board lines to correct

G-4 (DONE ownership check) flags any `DISPATCH_BOARD.md` line marked `DONE ✅` with no `COMPLETION_LOG.md`
entry carrying David's sign-off. The following are known false-DONE lines (non-exhaustive; G-4 generates the
full list):

- **WO-CANON-XXV** — temporal build is dead code; `00_CANON_INDEX.md` was corrected 2026-08-10 but the
  board line still shows `DONE ✅`. Verified by WO-CANON-XXV IRV.
- **WO-CANON-XV** — consumers absent; verified by WO-CANON-XV IRV.

**Architect action:** correct these board lines. The check is intentionally left strict — fixing the check
rather than the board lines would defeat the purpose of governance.

---

*This chapter was built by Builder (eLo OS) as part of WO-CANON-XXVII §A. Authorisation: no L3 required
for the governed index — it points at existing authoritative files, invents nothing.*
