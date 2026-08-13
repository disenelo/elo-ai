# Freeze Decision — [Work Package Name]

**Work Package:** WP_[X] — [Name]
**Engineer Role:** Release Engineer
**Date:**
**Status:** PENDING / FROZEN / REJECTED / ROLLBACK

---

## 1. Freeze Criteria

The following criteria must all be met before a freeze is approved.

| Criterion | Required | Status |
|---|---|---|
| Architecture Review complete | ✅ | |
| Implementation complete | ✅ | |
| Unit tests pass | ✅ | |
| Conversation validation complete | ✅ | |
| Regression tests pass | ✅ | |
| Stress tests pass | ✅ | |
| No second decision-maker introduced | ✅ | |
| Silence is valid output | ✅ | |
| Documentation updated | ✅ | |
| Handover document complete | ✅ | |

---

## 2. Evidence

Link to or paste the evidence for each criterion above.

| Criterion | Evidence |
|---|---|
| Regression | `engineering/work_packages/WP_[X]_*/regression.md` — PASS |
| Conversation | [log or summary] |
| Stress | [log or summary] |

---

## 3. Behaviour Locked

The following behaviours are locked by this freeze. Any future work package that changes these behaviours must amend this freeze document.

1.
2.
3.

---

## 4. Interfaces Locked

The following interfaces are locked. Changes require a new work package.

| Interface | Location | Signature |
|---|---|---|
| | | |

---

## 5. Known Issues at Freeze

Issues that exist at freeze time but did not block freeze (documented risk accepted):

| Issue | Risk Level | Reason Not Blocked | Tracking |
|---|---|---|---|
| | | | |

---

## 6. Rollback Procedure

If a future phase requires rollback to this freeze:

1. `git checkout [commit hash]` — restore to this freeze state
2. Run regression suite from `engineering/work_packages/WP_[X]_*/regression.md`
3. Confirm all criteria pass
4. Document the rollback event in this file (append, never overwrite)

**Freeze commit hash:**
**Freeze branch:**

---

## 7. Freeze Decision

| Decision | By | Date |
|---|---|---|
| ☐ APPROVED — phase frozen | | |
| ☐ REJECTED — return to implementation | | |
| ☐ DEFERRED — specific condition required | | |

**Notes:**

---

## 8. Amendment Log

If this freeze is ever amended (critical regression fix), record here. Never delete the original freeze entry.

| Date | Amendment | Reason | Re-tested By |
|---|---|---|---|
| | | | |
