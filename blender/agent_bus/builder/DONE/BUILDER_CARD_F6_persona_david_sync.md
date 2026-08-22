# BUILDER CARD — F-6 — _PERSONA "the user" → "David" sync
**Date:** 2026-08-21
**Seat:** Builder
**Priority:** MEDIUM
**Ruling record:** `docs/architecture/findings/DRIFT_RULING_F6.md`

---

## SOURCE

WO-CANON-I (commit `c0e1841`, 2026-08-13) — "eLo knows he is with David — second-person address rule."
Volume I §1.3: eLo's person is David Charles.
Volume I §1.7.1: `living_presence_spec.txt` and `_PERSONA` must not be edited apart.

## AUTHORITY

WO-CANON-I ruling already authorised. This is a completion gap — the ruling was applied to `living_presence_spec.txt` but not fully propagated to `_PERSONA` in `runtime/prompt_builder.py`.
No new David ruling required.

## FINDING

`prompt_builder.py:157` — "When the user is building…" (generic)
`prompt_builder.py:193` — "Help the user move forward." (generic)
`living_presence_spec.txt:12,46-65` — fully updated to "David" ✅

The `_PERSONA` block is the fallback when `living_presence_spec.txt` fails to load. Every "the user" reference in `_PERSONA` is a regression path back to generic identity.

## CURRENT BEHAVIOUR

On the fallback path (`_PERSONA` used instead of spec): the assembled system prompt contains "When the user is building" (line 157) and "Help the user move forward" (line 193). These do not reflect WO-CANON-I's ruling.

## REQUIRED BEHAVIOUR

All person references in `_PERSONA` must use "David." No occurrence of "the user" in the `_PERSONA` block.

## EXACT CHANGE BOUNDARY

File: `runtime/prompt_builder.py`
Scope: the `_PERSONA` string constant only (the multi-line string that constitutes the fallback system prompt)
Lines confirmed to contain "the user": 157, 193
Additional scan required: full text of `_PERSONA` for any other "the user" occurrences

Do NOT change: any logic, routing, or non-`_PERSONA` strings in prompt_builder.py

## DO NOT CHANGE

- `living_presence_spec.txt` — already correct; do not touch
- Any logic in `prompt_builder.py` outside the `_PERSONA` string
- Any other file

## INPUTS

`runtime/prompt_builder.py` — the `_PERSONA` string constant
`prompts/living_presence_spec.txt` lines 46-65 — the reference text for how David is described (match this style)

## OUTPUT

`runtime/prompt_builder.py` — `_PERSONA` updated, "the user" replaced with "David" at all occurrences within `_PERSONA`

## ACCEPTANCE TEST

Full-text search of the `_PERSONA` string for "the user" returns zero results.
`living_presence_spec.txt` and `_PERSONA` produce identical framing for the person eLo serves ("David", "your", "you").

## REGRESSION TEST

Simulate spec load failure (force `_PERSONA` to be used as the system prompt). Confirm the assembled prompt contains "David" not "the user" in lines corresponding to original 157 and 193. A grep for "the user" in the assembled fallback prompt must return zero results.

## EVIDENCE REQUIRED

Before implementing: read the full `_PERSONA` string in `prompt_builder.py` to find ALL occurrences of "the user." Report the count. Fix all of them in one commit.

## ESCALATION CONDITION

If any "the user" reference in `_PERSONA` is structurally significant (e.g., used as a variable or conditional) and cannot be mechanically replaced with "David," escalate to Lead Architect before touching it.
