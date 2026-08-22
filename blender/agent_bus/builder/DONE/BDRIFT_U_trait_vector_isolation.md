# BDRIFT-U — EloSelfState.core_values isolation

**SOURCE:** `_intake/SOURCE_2026-08-22_DAVID_U_trait_ruling.md`
**AUTHORITY:** David L3 ruling 2026-08-22. Classification: EXPERIENTIAL / NON-CANONICAL. Volume X UNRATIFIED.
**FINDING:** `EloSelfState.core_values` enters the canonical identity prompt path. It is not a canonical identity representation. It is legacy/dynamic self-state and must not be injected as identity.

**CURRENT BEHAVIOUR:**
- `elo_self_model.py:165–167` — `core_values` field populated
- `elo_self_model.py:274` — `core_values` used/accessed
- `elo_self_model.py:296` — `core_values` output path
- `server.py:3262` — `core_values` reaches the model input
- `elo_self_state.json` — live store for `EloSelfState`

**REQUIRED BEHAVIOUR:**
- `core_values` must NOT enter the canonical identity prompt path
- Canonical personality authority = `canonical_identity.md` (B-DRIFT-01 output)
- Legitimate experiential-state use of `core_values` (if any) must be preserved and clearly separated from identity injection

**EXACT CHANGE BOUNDARY:**
- `elo_self_model.py` — remove or isolate the path where `core_values` enters identity/personality block
- `server.py:3262` — verify `core_values` no longer injected as identity
- Do NOT modify `elo_self_state.json` schema — preserve the field, isolate the injection

**DO NOT CHANGE:**
- `FREEZE_V1_LOCK.md`
- `canonical_identity.md` (B-DRIFT-01 output)
- `living_presence_spec.txt`
- Any Volume architecture document
- Any canon document
- Volume X (UNRATIFIED — do not reference it as authority)
- No `core_values` trait is promoted to canonical identity

**INPUTS:** `EloSelfState` (read from `elo_self_state.json`)
**OUTPUT:** `core_values` remains in self-state; does NOT appear in identity/personality prompt block

**ACCEPTANCE TEST:**
1. Assemble a prompt and confirm `core_values` content does not appear in the identity/personality section
2. `EloSelfState` still loads and `core_values` field still exists in self-state (experiential-state use preserved)
3. Canonical identity block comes from `canonical_identity.md` only

**REGRESSION TEST:**
- If `core_values` is re-introduced into the identity prompt path, the test must go RED
- If `canonical_identity.md` is missing, the test must go RED (no silent fallback to `core_values`)

**EVIDENCE REQUIRED:**
- Commit hash
- Before/after: show `core_values` is absent from assembled identity prompt
- Tests: pass count and assertion text

**ESCALATION CONDITION:**
- If removing `core_values` from the identity path breaks another authorised capability, STOP and report to Architect before continuing
- If `core_values` is found to be the ONLY identity source (no `canonical_identity.md` yet), STOP — wait for B-DRIFT-01 to complete first
- Volume X must not be used as authority for any decision in this card
