# B-DRIFT-04 — Persona Fallback Sync
**Card:** BDRIFT04
**Issued by:** Board / Lead Architect
**Date:** 2026-08-22
**Authority:** `docs/architecture/findings/BOARD_RULING_DRIFT_REMEDIATION_2026-08-22.md` §DR-4 + CA F-10 instruction
**Governing sources:**
- `docs/architecture/_intake/SOURCE_2026-08-22_CA_drift_remediation_reconciliation.md` §F-10 "BUILDER IMPLEMENTATION"
- `docs/architecture/findings/DRIFT_REMEDIATION_REPORT_2026-08-21.md` §F-10
- Volume I §1.7.1 (living_presence_spec.txt and _PERSONA must not be edited apart)
- Unlock Log entry: "AUTHORISED card 0062, task 2"

---

## SOURCE

CA F-10 instruction (not blocked on David): `docs/architecture/_intake/SOURCE_2026-08-22_CA_drift_remediation_reconciliation.md` §"F-10 — BUILDER IMPLEMENTATION"

Audit finding: `docs/architecture/findings/DRIFT_REMEDIATION_REPORT_2026-08-21.md` §F-10

---

## AUTHORITY

This card is not blocked on a David L3 ruling. The architecture finding (primary/fallback relationship) and the Unlock Log divergence are verified facts. CA has explicitly authorised Builder to proceed.

Builder determines the sync mechanism. Builder does not create a new independent persona source.

---

## FINDING

Two persona sources exist:

- **Primary:** `prompts/living_presence_spec.txt` — loaded by `runtime/prompt_builder.py:28` (`load_spec()` function). Used when the file is present.
- **Fallback:** `_PERSONA` constant in `runtime/prompt_builder.py` — used only when `living_presence_spec.txt` is missing.

The primary/fallback relationship is correctly documented at `runtime/prompt_builder.py:28`:
```
# Load spec from file. Falls back to embedded _PERSONA if file missing.
```

**Divergence confirmed (from DRIFT_REMEDIATION_REPORT_2026-08-21.md §F-10):**

The Unlock Log records: "AUTHORISED card 0062, task 2" — "You mentioned…" added to the anti-mirroring list.

This change is present in `prompts/living_presence_spec.txt:244`:
```
like a hidden nook…", "you mentioned…"). Describing the conversation is not having one.
```

It is NOT present in `runtime/prompt_builder.py` `_PERSONA` fallback block.

**Volume I §1.7.1** states the two must not be edited apart. This constraint has been violated.

**Risk:** If `prompts/living_presence_spec.txt` goes missing for any reason, eLo runs on the `_PERSONA` fallback which lacks the "you mentioned" anti-mirroring rule. The fallback would permit the "You mentioned…" opener that was banned by Unlock Log card 0062.

---

## CURRENT BEHAVIOUR (file:line)

- `prompts/living_presence_spec.txt` — PRIMARY; contains "you mentioned…" anti-mirroring rule at line 244
- `runtime/prompt_builder.py` `_PERSONA` constant — FALLBACK; does NOT contain "you mentioned…" anti-mirroring rule
- `runtime/prompt_builder.py:28` — `load_spec()` — loads primary; falls back to `_PERSONA` if file missing

---

## REQUIRED BEHAVIOUR

1. `living_presence_spec.txt` = primary (unchanged — no edits required to primary)
2. `_PERSONA` = fallback derivative — must be synchronised to match all mandatory constraints of `living_presence_spec.txt`
3. The "you mentioned…" anti-mirroring constraint must be present in `_PERSONA`
4. A regression test must prove: invoking the fallback does not resurrect removed or forbidden behaviour
5. Do not create another independent persona source

**Sync scope:**
The `_PERSONA` fallback may be more compact than the primary. Compactness is acceptable. What is NOT acceptable is for the fallback to omit mandatory behavioural constraints that are in the primary.

Mandatory constraints that must be in both:
- Anti-mirroring list including "you mentioned…" (card 0062 Unlock Log)
- Identity: David (not "the user" at identity-describing points — F-6 already applied to lines 157 and 193; verify these are still correct)
- Any other constraints that would be functionally absent in the fallback (Builder to audit `living_presence_spec.txt` against `_PERSONA` for other gaps)

---

## EXACT CHANGE BOUNDARY

Builder must:

1. Read `prompts/living_presence_spec.txt:244` — confirm exact wording of the "you mentioned…" constraint
2. Read `runtime/prompt_builder.py` `_PERSONA` block — locate the anti-mirroring section (or confirm it is absent)
3. Add the "you mentioned…" constraint to `_PERSONA` at the equivalent position within the anti-mirroring / forbidden phrases section
4. Audit for other gaps between primary and fallback — add any other missing mandatory constraints
5. Write a test: load `_PERSONA` (simulate missing spec file), verify it does not permit "You mentioned…" as an opener

---

## DO NOT CHANGE

- `prompts/living_presence_spec.txt` — do not modify (primary source; this card syncs the fallback TO it, not the other way)
- `FREEZE_V1_LOCK.md`
- `docs/architecture/elo_canonical_identity.md` (created by B-DRIFT-01)
- `elo_personality_engine/sources/values.md` (R-04)
- Any canon or Volume Markdown files

---

## INPUTS

- `prompts/living_presence_spec.txt` — full content (primary source; find anti-mirroring section)
- `runtime/prompt_builder.py` — `_PERSONA` constant (full content; find anti-mirroring / forbidden phrases section)
- Unlock Log in `FREEZE_V1_LOCK.md` — card 0062, task 2 entry (exact wording of authorised change)
- `docs/architecture/findings/DRIFT_REMEDIATION_REPORT_2026-08-21.md` §F-10 — divergence details

---

## OUTPUT

- Modified `runtime/prompt_builder.py` — `_PERSONA` fallback updated to include "you mentioned…" anti-mirroring constraint and any other missing mandatory constraints
- New test (or addition to existing test): fallback persona does not permit behaviour forbidden by the primary spec
- Comment at the change site: `# B-DRIFT-04 — sync from living_presence_spec.txt:244, card 0062 Unlock Log 2026-08-22`

---

## ACCEPTANCE TEST

1. Simulate missing `living_presence_spec.txt` (rename or path override in test)
2. Invoke `load_spec()` and confirm fallback `_PERSONA` is loaded
3. Verify: the assembled system prompt from `_PERSONA` does NOT contain "You mentioned…" as a permitted opener
4. Verify: the assembled system prompt from `_PERSONA` refers to David (not "the user" at identity-describing points)
5. Verify: all mandatory constraints of the primary spec are present in the fallback

---

## REGRESSION TEST

```
PRIMARY_SPEC_CONSTRAINTS == FALLBACK_REQUIRED_CONSTRAINTS
```

1. Extract mandatory constraint set from `living_presence_spec.txt` (anti-mirroring list + identity markers + forbidden phrases)
2. Extract corresponding constraint set from `_PERSONA`
3. Assert: no constraint in set 1 is absent from set 2
4. Run with the "you mentioned…" constraint specifically: it must be present in `_PERSONA` and must cause a "forbidden" verdict if eLo produces "You mentioned…" as a turn opener

---

## EVIDENCE REQUIRED

- Content of `_PERSONA` anti-mirroring / forbidden phrases section (before and after)
- Test output: fallback + "You mentioned…" test → PASS (constraint is enforced)
- Test output: fallback + primary constraint audit → PASS (no missing mandatory constraints)
- Git diff: only `runtime/prompt_builder.py` and test file modified; `living_presence_spec.txt` unmodified

---

## ESCALATION CONDITION

Escalate to Board (Lead Architect) if:

- Builder discovers additional constraints in `living_presence_spec.txt` that are absent from `_PERSONA` and their status (mandatory vs optional) is ambiguous — report the list; Board will rule on which are mandatory
- The `_PERSONA` structure makes it impossible to add the anti-mirroring constraint without a structural rewrite — report before proceeding
- Any question arises about whether a constraint in the primary should be in the fallback — the governing principle is that the fallback must not permit behaviour that the primary forbids; report if uncertain
