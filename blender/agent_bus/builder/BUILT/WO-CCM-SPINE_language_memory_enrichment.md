# WO-CCM-SPINE — Wire CCM Enrichment Between Language Faculty and Memory Faculty
**Seat:** Builder  
**Priority:** P1  
**Date:** 2026-08-30  
**Authorised:** David L3 global ruling 2026-08-30 ("CCM get it started no more Gates")  
**Source:** ELO_Conversation Context Matrix (SOURCE_ARCHIVE); SOURCE_ALIGNMENT_REGISTER_2026-08-30.md CF-04; CCM_RECONCILIATION_2026-08-23.md  
**Lane note:** Builder ONLY. spine.py is Builder territory.

---

## Intent

The Conversation Context Matrix (CCM) defines 26 dimensions of conversational context (intent / relationship / energy / humour / emotion / cultural register / etc.). 19 of 26 are partially reconciled. The CCM YAML data exists. The gap: the CCM enrichment step is **not in the cognitive spine**. Source document CF-04: "CCM belongs between Language Faculty and Memory Faculty in spine."

Current spine order: Language Faculty → Memory Faculty  
Required spine order: Language Faculty → **CCM Enrichment** → Memory Faculty

---

## Scope

### ⚡ VERIFY FIRST
1. Confirm YAML data location: `grep -r "ccm" /sessions/eager-inspiring-hopper/mnt/elo-ai --include="*.yaml" -l`
2. Confirm CCM reconciliation file: `cat docs/architecture/CCM_RECONCILIATION_2026-08-23.md | head -60`
3. Check if CCM class/module exists: `find . -name "*ccm*" -o -name "*conversation_context*"`

### Step 1 — CCM enrichment module
If a CCM enricher module already exists, use it. If not, create `faculties/ccm/ccm_enricher.py` (Builder authors this — it is runtime code, not a spec file). The enricher:
- Takes current `CognitiveState` (post Language Faculty output)
- Scores the active CCM dimensions (use YAML data + existing 19-dim reconciliation)
- Returns `ccm_context: dict` — active dimensions and their values for this turn

### Step 2 — Spine insertion
Insert CCM enrichment step in `spine.py` after Language Faculty output and before Memory Faculty write:
```
language_output = language_faculty.process(turn)
ccm_context = ccm_enricher.enrich(turn, language_output, cognitive_state)
cognitive_state.ccm_context = ccm_context          # attach for Memory Faculty
memory_faculty.process(turn, cognitive_state)      # Memory sees CCM context
```

### Step 3 — Memory Faculty consumption
Memory Faculty uses `ccm_context` to improve tagging: relationship dimension → tag as `relationship` memory; emotional dimension → weight significance; cultural dimension → preserve register in recall.

### Step 4 — All 26 dims (authorised 2026-08-30)
All 26 CCM dimensions including the 3 cultural dims (storytelling / cultural / street — previously blocked as G-04) are now AUTHORISED. Wire all 26. Use source document values; do not invent.

---

## Definition of Done

- [ ] AT-1: CCM enricher runs per turn and produces a `ccm_context` dict with at least the 19 reconciled dims.
- [ ] AT-2: CCM enrichment step appears in spine.py AFTER Language Faculty and BEFORE Memory Faculty.
- [ ] AT-3: `cognitive_state.ccm_context` is populated (or equivalent dict passed to Memory Faculty).
- [ ] AT-4: Memory Faculty receives CCM context and uses at least one dim to improve tagging (unit test asserts the dict is non-empty on a test turn).
- [ ] AT-5: All 3 cultural dims (storytelling / cultural / street) are present in the CCM output (may be null/default if not triggered — presence is required, not always non-null).
- [ ] AT-6: Existing tests pass. No regressions.

---

## Files in scope

- `spine.py` (insert CCM enrichment step)
- `faculties/ccm/ccm_enricher.py` (create if not present, use if present)
- `runtime/contracts.py` (add `ccm_context` field to CognitiveState if needed)
- CCM YAML data (read-only — do not modify)

## Files NOT in scope

- `executive.py` (CCM enrichment is a spine-level step, not an executive decision)
- Unity / Design / MT files
