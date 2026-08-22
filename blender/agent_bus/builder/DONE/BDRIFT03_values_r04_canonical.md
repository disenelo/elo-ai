# B-DRIFT-03 — Values: R-04 Canonical, R-08 Derivative
**Card:** BDRIFT03
**Issued by:** Board / Lead Architect
**Date:** 2026-08-22
**Authority:** `docs/architecture/findings/BOARD_RULING_DRIFT_REMEDIATION_2026-08-22.md` §DR-3
**Governing sources:**
- `docs/architecture/_intake/SOURCE_2026-08-22_DAVID_drift_remediation_L3_rulings.md` §DR-3
- `docs/architecture/_intake/SOURCE_2026-08-22_CA_drift_remediation_reconciliation.md` §DR-3

---

## SOURCE

David L3 Ruling: `docs/architecture/_intake/SOURCE_2026-08-22_DAVID_drift_remediation_L3_rulings.md` §DR-3

A-1 Ruling (values authorship confirmed): `docs/architecture/findings/DRIFT_AUDIT_2026-08-21.md` §2

Audit Evidence: `docs/architecture/findings/DRIFT_AUDIT_2026-08-21.md` §F-9 (Finding F-9)
Remediation Investigation: `docs/architecture/findings/DRIFT_REMEDIATION_REPORT_2026-08-21.md` §F-9

---

## AUTHORITY

David L3. R-04 is canonical by David's ruling. The qualifying clauses are part of the values by David's ruling. "Gets things done" remains UNKNOWN — Builder does not decide its status.

---

## FINDING

Two values sources exist:

- **R-04:** `elo_personality_engine/sources/values.md` — 7 values WITH qualifying clauses (e.g., "Curiosity over certainty — move toward unknowns, not away"). David confirmed as author (A-1, 2026-08-21). This file is injected via `injection_layer.py` as `values_ordered` in `personality_block`.

- **R-08:** `obsidian_vault/01 Identity/Values.md` — same 7 headings, qualifying clauses stripped (e.g., "Curiosity over certainty" only). No authorisation record found for the clause-stripping. R-08 is potentially injected via the `vault_context → world_knowledge` path in `runtime/prompt_builder.py:382-384`.

Both representations may reach the model simultaneously in the same prompt. One is complete; one is stripped. This creates a dual values injection where one representation is internally contradictory with the authorised source.

---

## CURRENT BEHAVIOUR (file:line)

- `elo_personality_engine/sources/values.md` (R-04) — canonical values WITH clauses; reaches model via `injection_layer.py → personality_block`
- `obsidian_vault/01 Identity/Values.md` (R-08) — stripped values WITHOUT clauses; potentially reaches model via `runtime/prompt_builder.py:382-384` (vault_context → world_knowledge)
- `elo_personality_engine/injection_layer.py` — loads R-04 and injects as `values_ordered`
- `runtime/prompt_builder.py:382-384` — vault_context may include R-08 under the world_knowledge block

---

## REQUIRED BEHAVIOUR

R-04 is the single canonical values source. The qualifying clauses are part of the value. They must survive every path from R-04 to the model.

**What must change:**

1. **Prevent R-08 from independently injecting values into the prompt.** If vault_context includes `obsidian_vault/01 Identity/Values.md`, that content must be treated as reference material — not as canonical identity input. Builder must determine the vault_context filtering mechanism and implement a guard.

2. **R-08 must carry provenance metadata.** If R-08 remains in the vault (do not delete it), add a frontmatter or header block:
```
source: elo_personality_engine/sources/values.md (R-04)
derived: true
canonical: false
generation_method: UNKNOWN — manually maintained, not generated from R-04
last_verified: 2026-08-22
note: This is a non-canonical derivative. Do not independently edit. If vault context is injected, treat as reference only.
```

3. **Do not strip qualifying clauses from any path.** Any code or template that extracts only value headings (without the "— clause" part) must be identified and corrected.

4. **B-DRIFT-01 note:** Once `docs/architecture/elo_canonical_identity.md` exists (B-DRIFT-01), the ELO_VALUES section there must reference R-04 as the canonical source. This card does not modify that file — B-DRIFT-01 owns it.

**"Gets things done" clause:**
This clause was noted in the A-1 session (2026-08-21) but its exact authorisation status is UNKNOWN.

```
CLASSIFICATION: UNKNOWN — pending explicit David authorisation
ACTION: Do not add to R-04. Do not add to canonical identity. Leave as UNKNOWN.
```

Builder must not decide this question.

---

## EXACT CHANGE BOUNDARY

Builder must:

1. Locate the vault_context injection path in `runtime/prompt_builder.py:382-384` and inspect what files are included
2. If `obsidian_vault/01 Identity/Values.md` (R-08) can reach that path — add a guard, filter, or reclassification so its content is treated as reference material, not canonical identity
3. Add provenance metadata header to `obsidian_vault/01 Identity/Values.md` (R-08) — Markdown header, not a code change
4. Do not modify `elo_personality_engine/sources/values.md` (R-04) content
5. Verify that the qualifying clauses from R-04 reach `personality_block` intact — read the assembled `values_ordered` output and confirm

---

## DO NOT CHANGE

- `elo_personality_engine/sources/values.md` (R-04) — do not modify content; it is canonical
- `docs/architecture/elo_canonical_identity.md` — this card may reference it; B-DRIFT-01 owns its content
- `prompts/living_presence_spec.txt`
- `FREEZE_V1_LOCK.md`
- Any Volume Markdown files

---

## INPUTS

- `elo_personality_engine/sources/values.md` — R-04 canonical content (read to verify clauses intact)
- `obsidian_vault/01 Identity/Values.md` — R-08 stripped content (read to verify what is missing)
- `elo_personality_engine/injection_layer.py` — verify values_ordered extraction
- `runtime/prompt_builder.py:382-384` — locate vault_context / world_knowledge injection path
- `docs/architecture/findings/BOARD_RULING_DRIFT_REMEDIATION_2026-08-22.md` §DR-3

---

## OUTPUT

- `obsidian_vault/01 Identity/Values.md` — provenance header added
- `runtime/prompt_builder.py` or vault_context mechanism — guard/filter preventing R-08 from entering identity/value injection path as canonical source
- Assembled values block from a representative prompt (evidence)

---

## ACCEPTANCE TEST

1. Assemble a system prompt and capture the `values_ordered` / values block content
2. Verify: "Curiosity over certainty — move toward unknowns, not away" appears (clause preserved, not stripped)
3. Verify: all seven R-04 value entries appear with their qualifying clauses
4. Verify: R-08 stripped content does not appear in the identity/values position of the assembled prompt
5. Verify: if R-08 content appears anywhere in the prompt, it is in the world_knowledge / reference position only — not in personality_block or values position
6. Verify: "gets things done" does not appear in canonical values (it is UNKNOWN)

---

## REGRESSION TEST

1. Read `elo_personality_engine/sources/values.md` — confirm all seven values with clauses intact, unmodified
2. Read `obsidian_vault/01 Identity/Values.md` — confirm provenance header is present and content is otherwise unmodified
3. Run a prompt assembly and capture the full system prompt text — confirm R-04 clauses survive
4. Confirm no prompt assembly path injects both R-04 and R-08 values in contradictory form

---

## EVIDENCE REQUIRED

- Full content of `values_ordered` or equivalent extracted from the assembled prompt
- Confirmation of what files vault_context can include (list)
- Confirmation that R-08 is now classified as reference material in any vault_context path
- Git diff showing what changed

---

## ESCALATION CONDITION

Escalate to Board (Lead Architect) if:

- Builder determines that vault_context cannot be filtered without a structural change that would affect other vault files — report before proceeding
- Any ambiguity arises about which of the seven R-04 values has an equivalent stripped form in R-08 that may conflict — the Board Ruling is clear: R-04 wins; escalate only if the filtering mechanism itself is ambiguous
- "Gets things done" appears anywhere in existing code as a canonical value — report its location without adding or removing it; Board will rule
