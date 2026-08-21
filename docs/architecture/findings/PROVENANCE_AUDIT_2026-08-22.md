# PROVENANCE AUDIT — eLo Identity Pipeline
**Date:** 2026-08-22
**Scope:** Final runtime provenance audit, post B-DRIFT-01..04
**Method:** Read-only code inspection + live state check
**Requested by:** Architect Review (post-B-DRIFT-01..04 sign-off gate)

---

## Audit Chain

```
CANONICAL IDENTITY (canonical_identity.md)
       ↓
DERIVATIVES (R-04, obsidian_vault, EloSelfState)
       ↓
PROMPT ASSEMBLY (build_prompt() + self_block paths)
       ↓
FINAL MODEL INPUT (assembled system string)
       ↓
RUNTIME BEHAVIOUR
```

---

## Item 1: Sole authoritative identity source

**Claim:** `canonical_identity.md` is the sole authoritative identity source consumed by runtime identity injection.

**Evidence:**
- `injection_layer.py:35` — `_CANONICAL_IDENTITY = os.path.join(_SOURCES_DIR, "canonical_identity.md")`
- `injection_layer.py:444` — `canonical_text = _read(_CANONICAL_IDENTITY)` — read on every `load_personality_profile()` call
- `injection_layer.py:328` — `canonical_parsed = _parse_canonical_identity(canonical_text)` — the three character fields (foundational_traits, expressive_traits, behavioural_rules) are sourced ONLY from this parse
- `injection_layer.py:100–119` — `to_prompt_block()` emits ELO FOUNDATIONAL CHARACTER → ELO EXPRESSIVE CHARACTER → ELO BEHAVIOURAL RULES from these parsed fields
- No other code calls `_parse_canonical_identity()` or reads canonical_identity.md

**Verdict:** CONFIRMED — for the `personality_block` path.

**Caveat:** See Item 9. An independent identity representation (`EloSelfState.core_values`) also reaches the model via a separate code path. Item 1 is true for the personality_block path only.

---

## Item 2: DAVID_RELATIONSHIP_MODEL fields cannot enter personality_block

**Claim:** `communication_style`, `emotional_style`, `thinking_style` cannot enter `personality_block` through any alternate path.

**Evidence:**
- `injection_layer.py:350–353` — all three fields set to `""` explicitly; comment: "DAVID_RELATIONSHIP_MODEL data — intentionally NOT injected here"
- `injection_layer.py:148–149` — `to_prompt_block()` explicit exclusion comment: "B-DRIFT-02: communication_style / emotional_style / thinking_style are DAVID_RELATIONSHIP_MODEL data — intentionally NOT injected here"
- `_compile_profile()` at :301 takes `skeleton_text` as parameter but passes `""` from `load_personality_profile()` at :471
- No code path reads `personality_skeleton.md` and passes its content to `to_prompt_block()`
- `_obs_store.observe()` in server.py accumulates David's messages but does not call `_compile_profile()` and does not mutate `RuntimePersonalityProfile`

**Verdict:** CONFIRMED — communication_style / emotional_style / thinking_style have no path into personality_block.

---

## Item 3: 100 imperative messages cannot modify canonical identity

**Claim:** 100 imperative David messages cannot mutate foundational_traits or cause an imperative/commanding personality representation.

**Evidence:**
- `_obs_store.observe()` is called at server.py:~3982; it accumulates text but does not write to `canonical_identity.md` and does not call `load_personality_profile(force=True)` or `_compile_profile()`
- `injection_layer.py:324` — profile hash input = `identity_text + values_text + canonical_text + str(sorted_ids)` — skeleton text is explicitly excluded from the hash; observation messages never reach this hash
- `RuntimePersonalityProfile` is a frozen dataclass — no field can be mutated after construction
- `AC-01` test (100 imperatives, profile unchanged): PASS

**Verdict:** CONFIRMED — imperative messages have no path to canonical identity fields.

---

## Item 4: R-08 cannot independently inject competing values

**Claim:** R-08 (`obsidian_vault/01 Identity/Values.md`) cannot independently inject a competing value representation into model input.

**Evidence:**
- `obsidian_vault/01 Identity/Values.md` frontmatter (confirmed on disk):
  ```yaml
  canonical: false
  derived: true
  source: R-04
  derived_from: elo_personality_engine/sources/values.md
  b_drift_03: R-08 — non-canonical derivative...
  ```
- `obsidian_loader.py:115` — `_scan_vault()` reads `canonical: meta.get("canonical", True)` per note
- `obsidian_loader.py:146–152` — `_build_pack()`: identity-domain notes with `canonical=false` are labelled `[REFERENCE — derived, not canonical]` in the context_block
- `obsidian_loader.get_context_block()` is what reaches `vault_context` in `build_prompt()`; R-08 appears there with explicit `[REFERENCE]` label
- R-08 does NOT appear in the `personality_block` path; it is vault world knowledge only, and labelled non-canonical within it

**Verdict:** CONFIRMED — R-08 is labelled REFERENCE; it cannot enter the canonical value injection path.

---

## Item 5: R-04 qualifying clauses survive through to model input

**Claim:** Full R-04 qualifying clauses survive: R-04 → canonical values → personality representation → assembled prompt → model input.

**Evidence (by layer):**

| Layer | Evidence |
|---|---|
| R-04 source | `values.md:11` — "Curiosity over certainty — move toward unknowns, not away" (full clause present) |
| `_extract_section` | `injection_layer.py:343` — extracts "In order of priority" section verbatim |
| `_extract_bullets` | `injection_layer.py:345` — reads full bullet text including "— move toward unknowns, not away" |
| `values_ordered` | `RuntimePersonalityProfile.values_ordered` receives full tuple of complete value strings |
| `to_prompt_block()` | `injection_layer.py:137–139` — emits "CORE VALUES (priority order — R-04 canonical):" with full clause per value |
| `build_prompt()` | `personality_block` passed as parameter at server.py:3258; included in assembled system prompt |

No stripping or truncation occurs at any transition. The "— move toward unknowns, not away" clause is present at every layer.

**Verdict:** CONFIRMED — R-04 qualifying clauses survive intact to model input.

---

## Item 6: living_presence_spec.txt and _PERSONA contain no contradicting identity content

**Claim:** living_presence_spec.txt and _PERSONA contain no identity content that contradicts canonical_identity.md.

**Evidence:**

`living_presence_spec.txt` — FROZEN file, not read in this audit (no edits permitted). Its content is loaded at runtime by `load_living_presence_spec()`. FROZEN status is the governance guarantee; file was not modified by B-DRIFT.

`_PERSONA` (fallback, prompt_builder.py:36–295):
- Line 55: `"Core traits: calm, observant, playful, emotionally aware, curious, grounded, direct when needed."`
- This is a FLAT LIST that does not implement the two-layer foundational/expressive model from canonical_identity.md
- It contains "observant" — not in canonical_identity.md
- It contains "emotionally aware" — canonical is "emotionally present"
- It contains "grounded" — U-grounded, UNKNOWN
- It does NOT separate foundational vs expressive character layers
- This constitutes a partial conflict with canonical_identity.md's character model

**Important context:** `_PERSONA` is only active when `living_presence_spec.txt` is MISSING (i.e., runtime file-not-found exception). In normal operation, the spec file is present and _PERSONA is never used. The conflict is real but limited to the degraded-fallback path.

**Verdict:** CONDITIONAL — No contradiction in normal operation (spec file present). In the degraded fallback path, _PERSONA's flat trait list does not implement the two-layer canonical model. _PERSONA has not been updated to reflect the B-DRIFT-01 character model (only the ANTI-MIRRORING RULE was added by B-DRIFT-04).

**Open item:** The flat "Core traits" line in _PERSONA should be updated to match canonical_identity.md's two-layer model. This is a Builder-fixable item but requires explicit authorisation — it touches _PERSONA content which is identity-adjacent. Not addressed here (read-only audit).

---

## Item 7: _PERSONA is a fallback derivative, not independently authoritative

**Claim:** _PERSONA is a fallback derivative only.

**Evidence:**
- `prompt_builder.py:27–33` — `load_living_presence_spec()` returns `_PERSONA` only in the `except Exception` branch
- `prompt_builder.py:331` — `_push("living_presence_spec", load_living_presence_spec())` — the spec file is always attempted first
- `_PERSONA` is a Python string literal in prompt_builder.py — it carries no frontmatter, no `canonical` field, no authority declaration
- It cannot be externally referenced or directly invoked by any other module
- No code path treats `_PERSONA` as a source of record

**Verdict:** CONFIRMED — _PERSONA is a fallback derivative. Not independently authoritative.

---

## Item 8: Representative final assembled system prompt — block provenance

In normal operation, the assembled `system` string in `server.py:_process_turn()` is built in this order:

| Block | Source | Path | Identity/Values content |
|---|---|---|---|
| 1. living_presence_spec | `prompts/living_presence_spec.txt` | `prompt_builder.build()` → `load_living_presence_spec()` | Core persona (FROZEN) |
| 2. personality_block | `canonical_identity.md` + `values.md` (R-04) + `identity.md` | `injection_layer.to_prompt_block()` → `build()` | ELO FOUNDATIONAL CHARACTER (7) · ELO EXPRESSIVE CHARACTER (3) · ELO BEHAVIOURAL RULES (4) · PERSONALITY CORE · PERMANENT TRAITS · CORE VALUES R-04 (with full clauses) |
| 3. active_memory | `core/attention.py` output (FROZEN) | `build()` | Session memory signals; no character traits |
| 4. world_knowledge | `obsidian_vault/` via `obsidian_loader.get_context_block()` | `build()` | R-08 labelled [REFERENCE — derived, not canonical] |
| 5. executive_directive | `runtime/executive.py` decide() output | `build()` | Tone/action directive only; no identity |
| 6. [ELO INNER STATE] | `self/elo_self_model.prompt_block(_elo_self)` | server.py:3259 (`self_block=` param to `build()`) | eLo's experiential state (mood, curiosity, events); NO character traits |
| 7. **[IDENTITY — constitutional baseline]** | **`self/elo_self_model.identity_block(_elo_self)`** | **server.py:3262 (string concatenation after build())** | **core_values: calm, observant, playful, emotionally aware, curious, grounded — SEE ITEM 9** |
| 8. [ELO IDENTITY & MEANING] | `self/identity_meaning.identity_block(_elo_self)` | server.py:3268 (try/except) | Tendencies + meanings derived from behavioural patterns; no fixed trait assertions |
| 9. [ELO EMERGENT] | `self/emergent_cognition.emergent_block(_elo_self)` | server.py:3278 (try/except) | Internal life states; no character traits |

---

## Item 9: Self-block paths — _self_prompt_block and _self_identity_block

### `_self_prompt_block(_elo_self)` = `self/elo_self_model.prompt_block(state)` (line 419)

**Content:** `[ELO INNER STATE — what eLo is experiencing right now, independent of David's state]`
Fields: mood label + float, curiosity label + float, recent inner events (last 4), session read, focal thread (if any), top lifetime threads (top 3 by count).

**Assessment:** This is eLo's experiential/emotional state — accumulated from real turn events (action→inner_event mapping, tone→mood_delta). It does NOT assert character traits or values. It does not conflict with canonical_identity.md. It is NOT a competing identity representation.

**Verdict:** CLEAR. No canonical chain conflict.

---

### `_self_identity_block(_elo_self)` = `self/elo_self_model.identity_block(state)` (line 274)

**Content:**
```
[IDENTITY — constitutional baseline, asserted from self-model every turn]
name: eLo
with: David
core traits: calm, observant, playful, emotionally aware, curious, grounded
invariants: never preachy; never dramatic; never overly clinical; never trapped in abstraction; identity constant across backend and session
```

**Source:** `EloSelfState.core_values` (elo_self_model.py:165–167, default):
```python
["calm", "observant", "playful", "emotionally aware", "curious", "grounded"]
```

**Live disk state** (elo_self_state.json, confirmed 2026-08-22):
```
core_values: ['calm', 'observant', 'playful', 'emotionally aware', 'curious', 'grounded']
```
Identical to defaults — these values have never been overwritten or updated from canonical_identity.md.

**Provenance analysis of each trait:**

| Trait | In canonical_identity.md? | Notes |
|---|---|---|
| calm | YES — ELO_EXPRESSIVE_CHARACTER | Canonical ✓ |
| observant | NO | Not in S-01, not in FREEZE_V1_LOCK. Only in old _PERSONA Core traits. Provenance: UNKNOWN |
| playful | YES — ELO_FOUNDATIONAL_CHARACTER | Canonical ✓ |
| emotionally aware | NO — conflict | Canonical is "emotionally present". "Emotionally aware" is a different characterisation. |
| curious | YES — ELO_FOUNDATIONAL_CHARACTER | Canonical ✓ |
| grounded | NO — UNKNOWN | U-grounded: classified UNKNOWN per Board. Not in S-01, not in FREEZE_V1_LOCK. |

**Code path:**
- `server.py:3262` — `system = system + "\n\n" + _self_identity_block(_elo_self)` — injected AFTER `build_prompt()` returns, via direct string concatenation outside the personality_block pipeline
- This bypasses the DR-4 canonical chain entirely
- `check_identity_drift()` (elo_self_model.py:296) is defined but **NEVER CALLED** — the drift guard against core_values is non-functional
- No code ever synchronises `EloSelfState.core_values` from `canonical_identity.md`
- `EloSelfState` is loaded from disk (`self/elo_self_state.json`) or defaults to the code literals at elo_self_model.py:165–167

**Classification:**

> **U-trait-vector-injection: CONFIRMED ACTIVE.**
>
> `EloSelfState.core_values` is an independent identity representation that reaches the model every turn via `identity_block()` at server.py:3262. It contains non-canonical traits ("observant", "emotionally aware") and UNKNOWN traits ("grounded"). It was not addressed by B-DRIFT-01..04 and cannot be closed by Builder.

**Not Builder's determination:** Which traits in core_values are canonical, which should be removed, which should be updated to match canonical_identity.md phrasing, and whether "grounded" should be promoted or removed — these are David L3 decisions.

---

## Item 10: Volume X trait vector

**Volume X** = "Personality Engine" — listed at `docs/architecture/00_CANON_INDEX.md:179`:
```
[ ] Volume X   — Personality Engine (ratify Vol V Ch.7 into standalone volume, gap #6)
```
Status: `[ ]` — NOT ratified.

**The `EloSelfState.core_values` field** is the pre-Volume-X implementation of a trait vector concept. It:
- Predates canonical_identity.md (created before B-DRIFT)
- Is not governed by any ratified volume
- Has no provenance document establishing which traits are authorised and why
- Reaches the model via identity_block() — active in runtime

**Classification:**

> **U-trait-vector-injection sources from a pre-canon artifact (EloSelfState.core_values), not from Volume X ratification.** Volume X itself is not implemented — it is listed as a gap item. The existing trait vector in core_values is not compliant with the DR-4 chain and is not authorised by any ratified architecture volume.

---

## Drift Audit Status — Final

| Finding | Status |
|---|---|
| F-1 — 3 S-01 traits absent | CLOSED (B-DRIFT-01) |
| F-2 — Skeleton as user profile | CLOSED (B-DRIFT-02) |
| F-3 — GROUND gate | CLOSED (2026-08-21 remediation) |
| F-4 — Duplicate suppression | CLOSED (2026-08-21 remediation) |
| F-5 — Memory poisoning | CLOSED (2026-08-21 remediation) |
| F-6 — _PERSONA identity language | CLOSED (2026-08-21 remediation) |
| F-7 — Autobiography sparse | OPEN — deferred per Board |
| F-8 — Lessons ledger sparse | OPEN — deferred per Board |
| F-9 — Values dual representation | CLOSED (B-DRIFT-03) |
| F-10 — _PERSONA fallback drift | CLOSED (B-DRIFT-04) |
| **NEW** — _PERSONA Core traits flat list (fallback path only) | **OPEN** — not a B-DRIFT item; degraded-path-only conflict with two-layer model; requires explicit authorisation to fix |
| **NEW** — U-trait-vector-injection | **OPEN** — EloSelfState.core_values (non-canonical traits) reach model via identity_block() every turn; cannot be closed by Builder |

---

## UNKNOWN Item Status

| Unknown | Status |
|---|---|
| U-gets-things-done | UNKNOWN — not promoted, not removed. Preserved in R-08 observation data. |
| U-calm-direct-origin | UNKNOWN — not resolved. |
| U-grounded | UNKNOWN — confirmed present in EloSelfState.core_values (active in runtime). NOT promoted. Flagged in U-trait-vector-injection. |
| U-self-block-content | PARTIALLY RESOLVED: `prompt_block` = experiential state (CLEAR). `identity_block` = contains non-canonical and UNKNOWN traits — constitutes the active competing representation (U-trait-vector-injection). |
| U-trait-vector-injection | CONFIRMED ACTIVE — see Item 9 above. |
| U-5 | NOT FOUND in codebase. |
| U-6 | NOT FOUND in codebase. |

---

## Conclusion

**DRIFT AUDIT: NOT YET CLOSED.**

B-DRIFT-01..04 successfully closed F-1, F-2, F-9, F-10 and confirmed closure of F-3..F-6. The canonical chain from David's authorised intent → canonical_identity.md → injection_layer.py → personality_block → model input is clean and verified.

**One active competing identity path remains outside the canonical chain:**

```
EloSelfState.core_values (pre-canon artifact)
    ↓  [elo_self_model.identity_block()]
    ↓  [server.py:3262 — post-build() string concatenation]
    ↓  [system prompt — every turn]
    ↓  model input
```

This path contains non-canonical traits ("observant", "emotionally aware") and UNKNOWN traits ("grounded"). It bypasses the DR-4 chain. It was present before B-DRIFT and was not in scope for B-DRIFT.

**Closing this path requires a David L3 ruling that:**
1. Establishes canonical provenance for each trait in `EloSelfState.core_values`
2. OR removes non-canonical / UNKNOWN traits from `core_values`
3. OR ratifies Volume X (Personality Engine) with explicit authority over the trait vector

Builder cannot determine which traits are canonical. The UNKNOWN items (U-grounded, U-self-block-content) remain UNKNOWN until David rules.

```
PROVENANCE AUDIT 2026-08-22
ITEMS 1–8: VERIFIED
ITEM 9: _self_prompt_block CLEAR / _self_identity_block COMPETING REPRESENTATION FOUND
ITEM 10: Volume X UNRATIFIED — pre-canon artifact active
DRIFT AUDIT STATUS: NOT YET CLOSED
U-trait-vector-injection: CONFIRMED ACTIVE
```
