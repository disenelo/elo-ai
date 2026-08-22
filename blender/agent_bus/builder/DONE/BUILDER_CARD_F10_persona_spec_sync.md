# BUILDER CARD — F-10 — _PERSONA / living_presence_spec sync after Unlock
**Date:** 2026-08-21
**Seat:** Builder
**Priority:** MEDIUM
**Ruling record:** `docs/architecture/findings/DRIFT_RULING_F10.md`

---

## SOURCE

FREEZE_V1_LOCK.md Unlock Log entry 2026-08-21: "Added 'You mentioned…' to the existing anti-mirroring example list in `prompts/living_presence_spec.txt` lines 243-248. AUTHORISED card 0062, task 2."
Volume I §1.7.1: `living_presence_spec.txt` and `_PERSONA` must not be edited apart.
WO-036b commit `bf44626` 2026-08-21: modified `living_presence_spec.txt`.

## AUTHORITY

The Unlock Log entry is the authority. Volume I §1.7.1 requires the files stay in sync. No new David ruling required — this is propagation of an existing authorised change.

## FINDING

`prompts/living_presence_spec.txt` — anti-mirroring list updated; "You mentioned…" added (lines 243-248 per Unlock Log, confirmed at ~line 288-294 in current file structure).
`runtime/prompt_builder.py` `_PERSONA` — it is UNKNOWN whether an equivalent anti-mirroring section exists and whether "You mentioned…" is present in it.

## CURRENT BEHAVIOUR

If `_PERSONA` does not contain "You mentioned…" in its anti-mirroring rule: the fallback path does not enforce the ban. eLo may use "You mentioned…" on sessions where the spec fails to load.

## REQUIRED BEHAVIOUR

Every rule present in `living_presence_spec.txt` must have an equivalent in `_PERSONA`. Specifically: "You mentioned…" must be in the anti-mirroring list in `_PERSONA`.

## EXACT CHANGE BOUNDARY

File: `runtime/prompt_builder.py`
Scope: the `_PERSONA` string constant only
Change: locate the anti-mirroring section (if it exists); add "You mentioned…" to the example list; if no anti-mirroring section exists, create one matching the wording of `living_presence_spec.txt` lines 288-294

Do NOT change: `living_presence_spec.txt` (already correct), logic code in `prompt_builder.py`

## DO NOT CHANGE

- `living_presence_spec.txt` — correct; do not touch
- Any routing, logic, or non-`_PERSONA` code
- The Unlock Log in `FREEZE_V1_LOCK.md`

## INPUTS

`runtime/prompt_builder.py` `_PERSONA` string — read in full
`prompts/living_presence_spec.txt` lines 288-294 (anti-mirroring section) — reference for the rule to replicate

## OUTPUT

`runtime/prompt_builder.py` — `_PERSONA` updated with equivalent anti-mirroring rule including "You mentioned…"

## ACCEPTANCE TEST

Both files searched for anti-mirroring rule. Both contain "You mentioned…" as a banned phrase. Full-text comparison of anti-mirroring sections between the two files produces zero unmatched entries.

## REGRESSION TEST

Force fallback path (`_PERSONA` used). Send "You mentioned this before" to eLo. Response must not contain "You mentioned…" as eLo's phrase. Test must FAIL if the anti-mirroring section is absent from `_PERSONA`.

## EVIDENCE REQUIRED

Before implementing: read the full `_PERSONA` string in `prompt_builder.py`. Locate and report the anti-mirroring section (or confirm it is absent). Report the exact lines to be changed. Do not implement until this is reported.

## ESCALATION CONDITION

If a full comparison of `living_presence_spec.txt` and `_PERSONA` reveals additional divergences beyond the anti-mirroring entry (introduced by WO-036b or earlier), do NOT fix them silently. Report them to Lead Architect for classification before touching anything beyond the anti-mirroring line.
