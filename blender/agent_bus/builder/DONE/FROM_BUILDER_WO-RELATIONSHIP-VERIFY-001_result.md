# FROM BUILDER — WO-RELATIONSHIP-VERIFY-001 RESULT

**Status:** DONE — 2026-09-08  
**Verification: PASS — relationship style reaches prompt dynamically per turn**

## Findings

`prompt_builder.py` now reads `relationship_mode` from `exec_decision` and injects a relationship instruction into the directive block (added by WO-EXEC-DECISION-FIELDS-001 this session).

## AT-1: relationship_mode="close" → prompt includes relationship context

**PASS.** Prompt directive contains:
> "Relationship: close — speak as someone who knows him well; no formality"

## AT-2: relationship_mode="professional" → prompt changes

**PASS.** Prompt directive contains:
> "Relationship: professional — clear, respectful, measured"

`prompt_close != prompt_prof` — confirmed different.

## Was this previously absent?

**YES.** Before WO-EXEC-DECISION-FIELDS-001, `exec_decision` did not contain `relationship_mode`. prompt_builder read from `exec_decision` but the field was never there. The spec was authored (BA-07 SPEC_relationship_style_2026-08-30.md) but never consumed.

## State after fix

- `relationship_mode` set by `relationship_faculty` in spine → `plan.relationship_mode`
- `server.py` exec_decision now includes `"relationship_mode": getattr(_plan, "relationship_mode", "")`
- `prompt_builder.py` consumes it in the directive block with `_REL_INSTRUCTIONS` map

*Builder · 2026-09-08*
