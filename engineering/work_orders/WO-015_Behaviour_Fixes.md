---
id: WO-015
title: "eLo behaviour fixes ×4 (prompt-level)"
status: BLOCKED · REQUIRES DECISION (D-K)
target_agent: Builder (Engineer)
priority: P2
owner: ""
depends_on: [decision D-K]
blocks: []
spec_refs:
  - ELO_BEHAVIOUR_SPEC.md
  - prompts/living_presence_spec.txt
audit_gap: ""
created: 2026-07-27
---

# WO-015 — eLo behaviour fixes ×4

## 1. Objective
Apply four behaviour refinements to eLo's voice: (1) first-person body language, (2) no
projecting emotional states back unprompted, (3) single direct questioning, (4) direct
self-reporting on movement.

## 2. Why now
Flagged ready by the Engineer. They are **prompt-level** → they touch `prompts/`, which is
under **FREEZE_V1_LOCK**, so they need a scoped unlock (D-K). David won't unlock blind.

## 3. PHASE 1 — Engineer relays the exact before/after (do this first, no unlock needed)
Post the literal change for each fix so David approves the actual edit, not a paraphrase.
**Do not edit `prompts/` yet** — this phase is relay only. Use this format, one block per fix:

```
### Fix N — <name>
File:        prompts/<file> (or ELO_BEHAVIOUR_SPEC.md) · approx line/section
Rationale:   <1 line — the behaviour it corrects>
BEFORE:
    <exact current text>
AFTER:
    <exact proposed text>
Risk:        <any downstream effect on CAL / tone / other rules>
```

Cover all four: first-person body language · no unprompted emotion projection · single
direct question · direct movement self-report.

## 4. PHASE 2 — apply (only after D-K unlock)
On David's scoped unlock: apply the approved AFTER text exactly, run a behaviour batch
(pitch / bad-day / movement / distress samples) to confirm no regression, then the freeze
re-applies. No other prompt text changes in the same pass.

## 5. Files to TOUCH
- Phase 1: none (relay only, post into this WO / `COMPLETION_LOG.md`).
- Phase 2: `prompts/living_presence_spec.txt` and/or `ELO_BEHAVIOUR_SPEC.md` — **only** the
  four approved edits.

## 6. MUST NOT touch
- `runtime/executive.py` (FREEZE_V1_LOCK), the DISENELO apps in `~/Desktop/Output/` (D-I).
- Any prompt text beyond the four approved diffs.

## 7. Acceptance
- [ ] Phase 1: all four before/after blocks posted (exact text) → David reviews.
- [ ] D-K unlock granted + logged.
- [ ] Phase 2: edits applied verbatim; behaviour batch shows no regression; freeze re-applied.

## 8. Handback
Phase 1 → the four diff blocks (David approves → D-K). Phase 2 → diff + batch output +
re-freeze confirmation → Architect verifies → David marks DONE.

> **Current step: PHASE 1 — Engineer, relay the four before/after prompt diffs.** David reviews
> those, then rules D-K. No `prompts/` edits until then.
