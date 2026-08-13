# Documentation Standards — eLo OS

**Status:** ACTIVE
**Authority:** Lead Systems Architect

---

## What Must Be Documented

Every phase produces documentation before freeze. Documentation is not optional. A phase without documentation is not frozen — it is incomplete.

| Document | Required For | Template |
|---|---|---|
| Architecture Review | Every WP | `engineering/templates/architecture_review.md` |
| Implementation Plan | Every WP | `engineering/templates/implementation_plan.md` |
| Diagnostics | Every WP | `engineering/templates/diagnostics.md` |
| Regression | Every WP | `engineering/templates/regression.md` |
| Freeze Decision | Every WP | `engineering/templates/freeze.md` |
| Handover | Every WP | `engineering/templates/handover.md` |
| Architecture Doc | Every new component | `docs/architecture/NN_name.md` |

---

## The Append Rule

**Never delete or rewrite history.** If a fact becomes wrong, write "— superseded YYYY-MM-DD: [new fact]" next to the old line.

Old architecture documents are never deleted. They are marked superseded and archived in `.memory-archive/` if necessary.

Change logs are append-only. The most recent entry is at the bottom.

---

## Architecture Documents

Architecture documents describe what eLo IS — the cognitive structure.

**Location:** `docs/architecture/NN_name.md`
**Numbering:** Sequential. Never reuse a number. If a document is superseded, mark it in the header.

**Required sections:**

1. Purpose (one sentence)
2. Role in the One Brain
3. Interface (input/output schema)
4. Runtime Flow
5. Invariants
6. What This Component Does Not Do
7. Interaction Map
8. Known Limitations
9. Freeze Status

**What architecture documents are not:**
- Implementation guides (those live in work packages)
- Todo lists
- Design proposals (those live in architecture_review.md before approval)

---

## Engineering Documents

Engineering documents describe how eLo is BUILT — the process.

**Location:** `engineering/work_packages/WP_[X]_[Name]/`

Each work package folder contains the completed templates for that phase, plus any additional notes specific to that phase.

---

## Tracker

`TRACKER.md` at the repo root is the single source of project truth — status, decisions, change log.

**Update TRACKER.md after:**
- Any phase freeze
- Any freeze amendment
- Any significant decision
- Any session that produces production code

Format for change log entries:

```markdown
### YYYY-MM-DD — [Session Summary]
- What was built
- Decisions made
- Status changes
```

---

## Work Package Naming

| Format | Example |
|---|---|
| `WP_A_ENGINEERING_MANUAL.md` | Work Package A |
| `WP_B_ONE_BRAIN.md` | Work Package B |
| `WP_C_LANGUAGE_FACULTY.md` | Work Package C |

Letters A–Z. When the alphabet is exhausted, use `WP_A2_...` etc.

---

## Handover Quality Standard

A handover is complete when a person who has never seen the project can:

1. Read `engineering/README.md` — understand the programme
2. Read the last frozen WP handover — understand where the project is
3. Read the next WP architecture review — understand what to build next
4. Start implementing within one session

If any of those steps would fail, the handover is incomplete.

---

## Claude Session Documentation

Every Claude session that produces production code or architectural decisions must:

1. Update the relevant work package template with what was done
2. Update `TRACKER.md` change log
3. Note any deferred items in the relevant WP handover

Sessions that only discuss without building do not require documentation updates.
