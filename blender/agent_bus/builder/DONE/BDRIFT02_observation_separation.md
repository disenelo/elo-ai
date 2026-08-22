# B-DRIFT-02 — Observation Separation
**Card:** BDRIFT02
**Issued by:** Board / Lead Architect
**Date:** 2026-08-22
**Authority:** `docs/architecture/findings/BOARD_RULING_DRIFT_REMEDIATION_2026-08-22.md` §DR-2
**Governing sources:**
- `docs/architecture/_intake/SOURCE_2026-08-22_DAVID_drift_remediation_L3_rulings.md` §DR-2
- `docs/architecture/_intake/SOURCE_2026-08-22_CA_drift_remediation_reconciliation.md` §DR-2

---

## SOURCE

David L3 Ruling: `docs/architecture/_intake/SOURCE_2026-08-22_DAVID_drift_remediation_L3_rulings.md` §DR-2

CA Reconciliation: `docs/architecture/_intake/SOURCE_2026-08-22_CA_drift_remediation_reconciliation.md` §DR-2

Audit Evidence: `docs/architecture/findings/DRIFT_AUDIT_2026-08-21.md` §DRIFT-2
Remediation Investigation: `docs/architecture/findings/DRIFT_REMEDIATION_REPORT_2026-08-21.md` §F-2

---

## AUTHORITY

David L3. The decision on what the observation system may produce is governed. Builder determines HOW to implement the separation and reclassification. Builder does not determine what eLo's identity is or may observe.

---

## FINDING

`personality_skeleton.md` is generated from David's raw input messages. The pipeline:

```
David's messages
      ↓
server.py:3982 — _obs_store.observe(raw)
      ↓
server.py:4779-4780 — _export_skeleton(_gen_skeleton(_obs_store))
      ↓
personality_skeleton.md
      ↓
elo_personality_engine/injection_layer.py — extracts communication_style, emotional_style, thinking_style
      ↓
personality_block — injected into every system prompt as eLo's personality calibration
```

What `personality_skeleton.md` actually contains is a profile of DAVID's imperative command patterns (R-11 v0.1 confirms: "Directness: highly direct — imperative commands dominant ('Create', 'Build', 'Add', 'Implement', 'Fix', 'Run' are frequent openers)"). The document is titled "eLo Identity Skeleton" and injected as eLo's communication calibration.

No authorisation record was found for using David's communication profile as eLo's identity input. The mechanism was built without a documented authority decision.

---

## CURRENT BEHAVIOUR (file:line)

- `server.py:3982` — `_obs_store.observe(raw)` — raw is David's input text
- `server.py:4779-4780` — `_export_skeleton(_gen_skeleton(_obs_store))` — writes `personality_skeleton.md` on session shutdown (≥10 messages)
- `elo_personality_engine/skeleton_generator.py` — generates the skeleton; profiles David's communication style
- `elo_personality_engine/injection_layer.py` — loads `personality_skeleton.md`; extracts `communication_style`, `emotional_style`, `thinking_style`; injects as `personality_block` via `to_prompt_block()`
- `runtime/prompt_builder.py` — assembles `personality_block` into the system prompt (CONDITIONAL, if profile loads)

---

## REQUIRED BEHAVIOUR

The observation pipeline must remain intact as machinery. What must change is its output classification and its injection target.

**What must stop:**
The output of `_obs_store → _gen_skeleton → personality_skeleton.md → injection_layer.py → personality_block` must no longer be classified or injected as eLo identity.

**What must be preserved:**
- `_obs_store` and its observation data — do not delete
- `skeleton_generator.py` and its generation logic — do not delete
- `personality_skeleton.md` — do not delete; historical data must be preserved
- The observation machinery — mark superseded, do not silently destroy

**What the output may become:**
If the observation output is useful, it may be reclassified and exposed as:
- `relationship_model` — how David tends to communicate
- `communication_context` — current conversational register, topic, terminology
- `interaction_preferences` — level of detail preferred, playful vs serious

It must NOT be classified or injected as:
- `elo_personality`
- `elo_identity`
- `canonical_traits`
- `personality_block` (as currently named and positioned)

**Three-system boundary (from DR-2 ruling):**
```
ELO_IDENTITY          — canonical, authoritative, stable
                        source: docs/architecture/elo_canonical_identity.md (B-DRIFT-01)
DAVID_RELATIONSHIP_MODEL — observational, contextual, adaptive
                        source: _obs_store output (reclassified)
CONVERSATIONAL_STATE  — current, transient
                        source: current interaction
```
These three must remain separately addressable and must never be merged.

---

## EXACT CHANGE BOUNDARY

Builder must:

1. In `elo_personality_engine/injection_layer.py` — stop injecting the skeleton output as `personality_block` (or rename/reclassify it so it does not enter the identity position in the prompt)
2. In `server.py` — the calls to `_obs_store.observe(raw)` and `_export_skeleton` may remain but the output must not be injected as eLo identity
3. Reclassify the output: if the output is passed to the prompt at all, it must be clearly labelled as DAVID_RELATIONSHIP_MODEL or equivalent — not identity
4. Add a comment at every injection site removed/reclassified, citing this card and DR-2

**Builder determines:** the exact mechanism — whether to rename the block, reroute it, guard it with a clear classification label, or gate it from the identity assembly path. The governing constraint is that David's communication profile must not reach the prompt labelled as eLo's personality.

**Do not:** delete observation data, delete `personality_skeleton.md`, or delete `skeleton_generator.py`.

---

## DO NOT CHANGE

- `_obs_store` observation data — preserve
- `personality_skeleton.md` content — preserve (mark superseded use, do not delete content)
- `skeleton_generator.py` logic — preserve (mark superseded injection use)
- `docs/architecture/elo_canonical_identity.md` — B-DRIFT-01 creates this; do not modify its content from this card
- `elo_personality_engine/sources/values.md` (R-04)
- `prompts/living_presence_spec.txt`
- `FREEZE_V1_LOCK.md`

---

## INPUTS

- `docs/architecture/findings/BOARD_RULING_DRIFT_REMEDIATION_2026-08-22.md` §DR-2 — governing ruling
- `docs/architecture/_intake/SOURCE_2026-08-22_DAVID_drift_remediation_L3_rulings.md` §DR-2 — David ruling verbatim
- `elo_personality_engine/skeleton_generator.py` — read to understand current skeleton generation
- `elo_personality_engine/injection_layer.py` — read to understand current injection mechanism
- `server.py` — lines 3982 (observe call) and 4779-4780 (export call)
- `runtime/prompt_builder.py` — locate personality_block assembly point

---

## OUTPUT

- Modified `elo_personality_engine/injection_layer.py` — personality_block injection removed or reclassified
- Modified `server.py` — observation calls retained; export reclassified or gated from identity injection
- Comments at every changed injection site: `# B-DRIFT-02 — DR-2 ruling 2026-08-22 — David's communication profile is not eLo identity`
- No deletion of observation machinery or data

---

## ACCEPTANCE TEST

1. Feed `_obs_store` with 100 messages containing BUILD / CREATE / FIX / IMPLEMENT / RUN / ADD / CHANGE
2. Run session shutdown (≥10 messages) to trigger skeleton generation
3. Assemble the system prompt
4. Verify: the assembled system prompt's identity section does NOT contain imperative command patterns derived from David's messages
5. Verify: ELO_FOUNDATIONAL_CHARACTER traits from `docs/architecture/elo_canonical_identity.md` are present in the prompt (or accessible through the canonical path)
6. Verify: `personality_skeleton.md` still exists and its data is preserved
7. Verify: if observation output reaches the prompt at all, it is labelled as relationship model / communication context — not eLo identity

---

## REGRESSION TEST

1. Before change: capture `personality_block` content from a representative assembled prompt (runtime snapshot)
2. After change: confirm `personality_block` no longer contains David's imperative patterns under an eLo identity label
3. Confirm `personality_skeleton.md` file exists and is undeleted (git status)
4. Confirm `skeleton_generator.py` exists and is undeleted (git status)
5. Confirm `_obs_store` observation calls still execute (no silent removal)

---

## EVIDENCE REQUIRED

- Assembled system prompt snippet (before and after) showing the identity/personality block content
- Confirmation that `personality_skeleton.md` exists post-change
- Git diff showing what changed and what was preserved
- Confirmation that observation calls (`_obs_store.observe`) still execute

---

## ESCALATION CONDITION

Escalate to Board (Lead Architect) if:

- The injection_layer.py or server.py structure means the reclassification cannot be done without also changing the canonical identity path — halt and report
- Builder determines that removing the skeleton from personality_block will cause a prompt assembly error that cannot be resolved without a structural change to `prompt_builder.py` — report before proceeding
- Any question about what the relationship model content should contain — the governing allowed uses are listed in DR-2; those are the boundaries
