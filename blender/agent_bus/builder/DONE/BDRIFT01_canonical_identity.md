# B-DRIFT-01 — Canonical Identity Source
**Card:** BDRIFT01
**Issued by:** Board / Lead Architect
**Date:** 2026-08-22
**Authority:** `docs/architecture/findings/BOARD_RULING_DRIFT_REMEDIATION_2026-08-22.md` §DR-1 + §DR-4
**Governing sources:**
- `docs/architecture/_intake/SOURCE_2026-08-22_DAVID_drift_remediation_L3_rulings.md` §DR-1, §DR-4, §DR-5
- `docs/architecture/_intake/SOURCE_2026-08-22_CA_drift_remediation_reconciliation.md` §DR-1, §BUILDER WORK ORDER
- `docs/architecture/_intake/SOURCE_2026-06-06_DAVID_elo_ai_origin_conversations.md` (S-01)
- `FREEZE_V1_LOCK.md` §1

---

## SOURCE

S-01: `docs/architecture/_intake/SOURCE_2026-06-06_DAVID_elo_ai_origin_conversations.md` — David-authored, 2026-06-06, pre-code. Authorship confirmed A-3 (2026-08-21).

FREEZE: `FREEZE_V1_LOCK.md` §1 — David-declared 2026-06-29. ACTIVE.

Board Ruling: `docs/architecture/findings/BOARD_RULING_DRIFT_REMEDIATION_2026-08-22.md` §DR-1.

---

## AUTHORITY

David L3. These traits are governed decisions — not Builder interpretations. Builder determines WHERE and HOW to create the file. Builder does NOT determine what goes in it beyond what is specified here.

---

## FINDING

No canonical identity source file exists at `docs/architecture/` or anywhere in the `elo_personality_engine/` tree that carries the structured layered representation (FOUNDATIONAL + EXPRESSIVE + BEHAVIOURAL_RULES + VALUES) with provenance metadata. The seven S-01 traits have never been implemented in code in any form (git-verified in `DRIFT_REMEDIATION_REPORT_2026-08-21.md` §F-1).

Current prompt assembly injects `living_presence_spec.txt` (primary) and `personality_block` from `personality_skeleton.md` (derived from David's messages, not eLo's traits). Neither is a single-source canonical identity document with provenance.

---

## CURRENT BEHAVIOUR (file:line)

- `runtime/prompt_builder.py:28` — `load_spec()` loads `prompts/living_presence_spec.txt` as primary identity source; falls back to `_PERSONA` if file missing
- `elo_personality_engine/injection_layer.py` — loads `personality_skeleton.md` and injects `communication_style`, `emotional_style`, `thinking_style` as `personality_block`
- `prompts/living_presence_spec.txt:44` — `Core: calm, curious, playful, direct, emotionally present, creative, grounded` — a flat trait list with no layer distinction and no provenance
- `runtime/prompt_builder.py` `_PERSONA` — fallback identity block; carries `calm, observant, playful, emotionally aware, curious, grounded, direct when needed` — also a flat list
- No canonical identity file with structured layers and provenance exists anywhere in the repo

---

## REQUIRED BEHAVIOUR

Builder must create ONE canonical identity source file at:
`docs/architecture/elo_canonical_identity.md`

**Before creating this file:** confirm that no equivalent already exists under `docs/architecture/` or `elo_personality_engine/sources/`. If one exists, extend it — do not create a duplicate (Rule 6).

The file must contain these four structures, exactly:

### ELO_FOUNDATIONAL_CHARACTER
```
source: docs/architecture/_intake/SOURCE_2026-06-06_DAVID_elo_ai_origin_conversations.md
authored_by: David Charles
date: 2026-06-06
confirmed_by: A-3 ruling, 2026-08-21
last_verified: 2026-08-22

traits:
  - curious
  - encouraging
  - playful
  - creative
  - non-judgmental
  - speaks simply but intelligently
  - focuses on exploration rather than giving orders
```

### ELO_EXPRESSIVE_CHARACTER
```
source: FREEZE_V1_LOCK.md §1
declared_by: David Charles
date: 2026-06-29
status: ACTIVE
ruling: SOURCE_2026-08-22_DAVID_drift_remediation_L3_rulings.md §DR-1
note: These describe HOW eLo expresses — they do not replace or revoke foundational character.

traits:
  - calm
  - direct
  - emotionally present
```

### ELO_BEHAVIOURAL_RULES
```
source: SOURCE_2026-08-22_DAVID_drift_remediation_L3_rulings.md §DR-1 "Important distinction"
date: 2026-08-22

rules:
  - "direct" means clarity of communication — never authority over David
  - "calm" describes regulation of expression — does not replace encouraging or emotionally present behaviour
  - "emotionally present" means eLo may respond warmly — not that eLo may claim David feels something David has not expressed
  - A flat trait list collapsing foundational and expressive layers is forbidden
  - No model-generated personality profile may override these canonical traits
```

### ELO_VALUES
```
source: elo_personality_engine/sources/values.md (R-04)
authored_by: David Charles
confirmed_by: A-1 ruling, 2026-08-21
canonical: true
last_verified: 2026-08-22
note: Values must be included WITH their qualifying clauses. Clauses are part of the value — not commentary.
      See B-DRIFT-03 for values pipeline governance.
```

Every field in this file must carry provenance. No field may be empty or UNKNOWN without being explicitly labelled UNKNOWN.

**What this file must NOT contain:**
- User observation data
- Anything derived from `personality_skeleton.md`
- Anything derived from `_obs_store`

---

## EXACT CHANGE BOUNDARY

**CREATE:** `docs/architecture/elo_canonical_identity.md` — new Markdown file with the four structures above.

**DO NOT MODIFY:** `prompts/living_presence_spec.txt` · `FREEZE_V1_LOCK.md` · `runtime/prompt_builder.py` · `elo_personality_engine/injection_layer.py` · any `.py` or `.cs` file.

Note: `living_presence_spec.txt` and `_PERSONA` must eventually derive from this canonical source (DR-4), but that wiring is a separate implementation step that follows this card. This card establishes the source only.

---

## DO NOT CHANGE

- `FREEZE_V1_LOCK.md` — do not edit
- `prompts/living_presence_spec.txt` — do not edit
- `runtime/prompt_builder.py` — do not edit
- `elo_personality_engine/injection_layer.py` — do not edit
- `personality_skeleton.md` — do not edit (see B-DRIFT-02)
- `elo_personality_engine/sources/values.md` (R-04) — do not edit
- Any existing canon Volume Markdown files

---

## INPUTS

- `docs/architecture/_intake/SOURCE_2026-06-06_DAVID_elo_ai_origin_conversations.md` — S-01 traits (verbatim)
- `FREEZE_V1_LOCK.md` §1 — FREEZE traits
- `docs/architecture/findings/BOARD_RULING_DRIFT_REMEDIATION_2026-08-22.md` — governing ruling
- `docs/architecture/_intake/SOURCE_2026-08-22_DAVID_drift_remediation_L3_rulings.md` §DR-1 — David ruling verbatim

---

## OUTPUT

`docs/architecture/elo_canonical_identity.md` — canonical identity source file with ELO_FOUNDATIONAL_CHARACTER, ELO_EXPRESSIVE_CHARACTER, ELO_BEHAVIOURAL_RULES, and ELO_VALUES blocks, each with full provenance metadata.

---

## ACCEPTANCE TEST

1. File exists at `docs/architecture/elo_canonical_identity.md`
2. File contains all four sections: ELO_FOUNDATIONAL_CHARACTER, ELO_EXPRESSIVE_CHARACTER, ELO_BEHAVIOURAL_RULES, ELO_VALUES
3. ELO_FOUNDATIONAL_CHARACTER contains all seven S-01 traits verbatim
4. ELO_EXPRESSIVE_CHARACTER contains calm, direct, emotionally present — and carries the ruling note that these describe expression, not replacement
5. ELO_BEHAVIOURAL_RULES contains all four behavioural constraints from the DR-1 ruling
6. Every field carries a `source:` provenance tag
7. No field contains observation-derived content from `personality_skeleton.md` or `_obs_store`
8. No field is populated from a model-generated personality profile

---

## REGRESSION TEST

1. Read `docs/architecture/elo_canonical_identity.md` and confirm the seven S-01 traits are present and unaltered
2. Read `docs/architecture/elo_canonical_identity.md` and confirm no "gets things done" appears (UNKNOWN — not to be added)
3. Confirm `FREEZE_V1_LOCK.md` is unmodified after this card (git diff)
4. Confirm `prompts/living_presence_spec.txt` is unmodified after this card (git diff)

---

## EVIDENCE REQUIRED

- File content of `docs/architecture/elo_canonical_identity.md` (full)
- Confirmation that `docs/architecture/` was checked for existing canonical identity source before creating (Rule 6)
- Git diff confirming no `.py`, `.cs`, `.txt`, or frozen files were modified

---

## ESCALATION CONDITION

Escalate to Board (Lead Architect) if:

- Any trait is ambiguous between foundational and expressive layer and Builder cannot classify it from the sources above
- "grounded" appears and Builder does not know which layer it belongs to (it is UNKNOWN per the Board Ruling — do not add it to either layer; note it as UNKNOWN with source reference to `living_presence_spec.txt:44`)
- A canonical identity file is found at an unexpected location — halt and report before creating a duplicate
