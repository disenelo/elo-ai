# Handover — [Work Package Name]

**Work Package:** WP_[X] — [Name]
**Engineer Role:** Release Engineer / Systems Integrator
**Date:**
**Status:** DRAFT / COMPLETE

---

## 1. What Was Built

Plain language summary. What exists now that did not exist before this work package?

---

## 2. What Was Not Built (and Why)

What was in scope but deferred? What was explicitly excluded?

| Item | Reason |
|---|---|
| | |

---

## 3. Architectural Decisions Made

Decisions with lasting consequences. Record them here so they are never relitigated.

| Decision | Rationale | Alternative Considered | Why Rejected |
|---|---|---|---|
| | | | |

---

## 4. Frozen Interfaces

The following interfaces are now frozen and must not be changed without amending the freeze document.

| Interface | File | Signature |
|---|---|---|
| | | |

---

## 5. What the Next Work Package Needs to Know

The single most important thing the next engineer needs to understand before starting WP_[X+1].

---

## 6. Known Issues Inherited

Issues that exist at handover that the next phase must be aware of.

| Issue | Severity | Impact on Next Phase |
|---|---|---|
| | | |

---

## 7. Files to Read First

If picking up this project cold, read these files in this order.

1. `engineering/work_packages/WP_[X]_.../freeze.md` — what is frozen
2. `docs/architecture/[relevant].md` — architecture baseline
3. `engineering/TEMPLATE_PhasePlaybook/` — blank template for next phase
4. [other specific files]

---

## 8. Tests to Run Before Starting Next Phase

Do not start WP_[X+1] until these pass.

```bash
# Regression baseline
python3 -m pytest tests/ -v

# Conversation health check
curl -s http://localhost:5050/chat -H "Content-Type: application/json" \
  -d '{"text": "yo"}' | python3 -m json.tool
```

Expected: all tests pass. Server responds with valid JSON.

---

## 9. Suggested Next Work Package

**WP_[X+1]:** [Name]
**Why now:** [brief rationale]
**Priority:** CRITICAL / HIGH / NORMAL

---

## 10. Handover Sign-Off

| Role | Name | Date | Confirmed |
|---|---|---|---|
| Outgoing Engineer | | | |
| Incoming Engineer | | | |
