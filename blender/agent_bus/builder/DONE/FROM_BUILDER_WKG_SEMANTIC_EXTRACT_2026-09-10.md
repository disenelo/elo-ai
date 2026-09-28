# BUILDER EVIDENCE — WO-WKG-SEMANTIC-EXTRACT
Date: 2026-09-10
Status: DONE

## What was built

Decision 2 from `FROM_ARCHITECT_2026-09-10_BOARD_DECISIONS.md`.
Real semantic claim extraction replacing generic category-tag `ASSOCIATED_WITH` writes.

## Files changed

### `runtime/wkg_faculty.py` (appended)
- `extract_and_record_claims(turn_text, source_id, significance_score)` — extracts real factual claims from David's turn text.
- Three extraction passes:
  1. **Correction detection** (`_CORRECTION_SIGNALS` regex) → `CORRECTED` claim, confidence 0.9, significance 0.75
  2. **First-person statements** (`_FIRST_PERSON_VERBS` regex, per sentence) → `STATED` / `PREFERS` / `FEELS` / `DECIDED` / `WORKING_ON` based on verb
  3. **Named project references** (`_KNOWN_PROJECTS` dict, 12 keywords) → `ASSOCIATED_WITH` claim with verbatim context
- `_get_or_create_entity()` helper — find by exact label match or create; avoids duplicate entities.
- `record_claim()` was already updated with `claim_text` field (prior session).

### `memory/wkg/relationship_types.json`
- Already updated with: `STATED`, `PREFERS`, `FEELS`, `DECIDED`, `CORRECTED`, `WORKING_ON`, `BLOCKED_BY` (prior session).

### `server.py` (lines ~4714-4800 replaced)
- Removed two generic `ASSOCIATED_WITH` category-tag write blocks (88 lines).
- Replaced with single `extract_and_record_claims(raw, source_id=f"turn:{_action}", significance_score=float(_mem_sig))` call (10 lines).

## Smoke test evidence

Turn: `"I keep starting things and not finishing them, it's frustrating."`
→ `[STATED]` claim_text: `"I keep starting things and not finishing them, it's frustrating"`

Turn: `"I love working on the game, the start menu cinematic is incomplete."`
→ `[PREFERS]` claim_text: `"I love working on the game, the start menu cinematic is incomplete"`
→ `[ASSOCIATED_WITH]` claim_text: `"David mentioned eLo-Planet game in this turn: ..."`

Turn: `"No actually that's wrong — eLo is from London not Manchester."`
→ `[CORRECTED]` claim_text: `"No actually that's wrong — eLo is from London not Manchester."`

## Test suite
1568 pass, 4 fail (pre-existing, unchanged). No regressions.

## Acceptance criteria (Board Decision 2)
- ✅ 3 turns → actual claims written (entity + claim_text + claim_type + significance)
- ✅ claim_type from closed enum: STATED / PREFERS / CORRECTED / DECIDED / WORKING_ON / ASSOCIATED_WITH
- ✅ claim_text is verbatim/paraphrase of actual stated content
- ✅ Correction pattern triggers CORRECTED claim with higher significance weight
- ✅ No generic category-tag ASSOCIATED_WITH writes for every turn

## What remains (WO-ELO-LEARN-001)
WKG-first routing, SPG link layer, faculty writes to WKG, base_cognition faculty. Not started.
