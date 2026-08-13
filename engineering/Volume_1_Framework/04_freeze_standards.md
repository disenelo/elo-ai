# Volume 1 — Freeze Standards

A freeze is a permanent architectural decision. It is not a milestone or a checkpoint — it is a commitment that this phase's behaviour is the baseline for everything that follows.

---

## What Freezing Means

When a phase is FROZEN:

- Its documented runtime interfaces are fixed
- Its behaviour under normal conditions is the regression baseline
- Its architecture cannot be redesigned (bugs can be fixed; architecture cannot change)
- All future phases must pass their regression tests against this phase's frozen behaviour

**A freeze is not reversible except by ROLLBACK** (see below). There is no "unfreeze."

---

## The Freeze Gate

Before a phase can be frozen, all of the following must be true:

- [ ] Steps 01–09 of the lifecycle are complete
- [ ] All unit tests pass
- [ ] All conversation tests pass (happy path + regression)
- [ ] Long-session test (minimum 1 hour) shows stable behaviour
- [ ] No unresolved regressions against prior frozen phases
- [ ] All 6 Architecture Constants verified as compliant
- [ ] `11_handover.md` is drafted (the handover must exist before the freeze is signed)

If any item is unchecked, the freeze does not happen. The phase returns to the step where the gap exists.

---

## Freeze Decisions

### FROZEN ✅

All criteria met. Phase is complete. Architecture is locked. Document the date.

```
FREEZE DECISION: FROZEN
Date: YYYY-MM-DD
Signed: David Charles
```

### CONDITIONAL ⚠️

All critical criteria met. One or more non-critical gaps exist. Freeze proceeds with named exceptions.

```
FREEZE DECISION: CONDITIONAL
Date: YYYY-MM-DD
Exceptions:
  - [exception 1]: to be resolved in Phase N
  - [exception 2]: known limitation, documented in gap analysis
Signed: David Charles
```

A CONDITIONAL freeze is still a freeze. The exceptions are binding commitments, not intentions.

### REJECTED 🔴

A fundamental problem with the phase. Implementation does not match the Runtime Design, or a critical test fails, or an Architecture Constant is violated.

```
FREEZE DECISION: REJECTED
Date: YYYY-MM-DD
Reason: [specific failure]
Return to: Step [N]
```

After REJECTED, the phase returns to the indicated step. The freeze document is updated with the rejection and the resolution once the step is re-completed.

### ROLLBACK 🔴🔴

The phase introduced a regression against a prior frozen phase that cannot be resolved without reverting. All changes from this phase are reverted. Prior phase state is restored.

```
FREEZE DECISION: ROLLBACK
Date: YYYY-MM-DD
Regression: [what broke, what was expected]
Reverted to: Phase [N] state
Root cause: [what went wrong]
Prevention: [what changes to the design or process prevent this]
```

A ROLLBACK is a learning event, not a failure. It means the validation process worked — it caught the problem before it compounded.

---

## What a Freeze Locks (Specific to eLo OS)

| Component | What Freezing Means |
|---|---|
| Runtime interfaces | Function signatures, return types, and error behaviour |
| `g_ctx` injection format | The `__str__` output that the Executive reads |
| Stream registry API | `register_stream()` signature |
| AttentionSnapshot fields | All fields present in Phase 2 are permanent |
| Conversation behaviour | Validated conversation patterns are the regression baseline |
| Cooldown defaults | `ELO_CS_COOLDOWN=5`, `ELO_CS_COOLDOWN_SEC=30.0` — tunable via env but defaults are frozen |

---

## What a Freeze Does NOT Lock

- Internal implementation details (can refactor internals without changing interfaces)
- Default values configurable via environment variables (user can tune these)
- Log output format (cosmetic, not functional)
- Performance characteristics (can improve without changing behaviour)

---

## The Rollback Protocol

If a rollback is required:

1. Document what failed in `10_freeze.md`
2. Identify the commit that introduced the regression (use `git log`)
3. Revert to that commit using `git revert` (not `git reset --hard` — preserves history)
4. Verify all prior frozen phase tests pass at the reverted state
5. Document the root cause
6. Revise the design before re-attempting implementation

The code history of a failed attempt is preserved in git. It is not lost. The freeze document records why it failed.

---

## Freeze Numbering

Each freeze gets a version number within the phase:

- First freeze attempt: `v1`
- After a rejection and revision: `v2`
- After a rollback and re-implementation: `v3`

This creates an audit trail. A phase that required three attempts to freeze has three entries in its freeze document, each with a date and outcome.
