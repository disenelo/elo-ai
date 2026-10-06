# WO-CREATE-CAPABILITY — Wire CREATE Capability into Capability Registry
**Seat:** Builder  
**Priority:** P2  
**Date:** 2026-08-30  
**Authorised:** David L3 global ruling 2026-08-30 ("Anything not authorised, I authorised it")  
**Source:** Build List §6; SOURCE_ALIGNMENT_REGISTER_2026-08-30.md G-05; SPEC_CE_001_file_output_capability_2026-08-27.md; CE-001–008 R&D (all DONE)  
**Lane note:** Builder ONLY.

---

## Intent

CREATE capability R&D (CE-001–008) is DONE. The tools exist:
- `tools/llm_file_agent.py` — LLM-driven file generation
- `tools/draft_agent.py` — draft / iterate on content
- `tools/model_gen_agent.py` — model/structure generation
- `tools/file_reader_agent.py` — file reading for context

These tools are NOT registered in the capability registry and NOT dispatchable by the Executive. This WO wires them in.

---

## Scope

### ⚡ VERIFY FIRST
1. Run `python3 -c "from tools.llm_file_agent import LLMFileAgent; print('ok')"` — confirm import.
2. Run `python3 -c "from tools.draft_agent import DraftAgent; print('ok')"` — confirm import.
3. Check the capability registry: `grep -n "CREATE\|create\|file_gen\|draft" runtime/capability_registry.py 2>/dev/null || find . -name "*capability_registry*"`
4. Read `SPEC_CE_001_file_output_capability_2026-08-27.md` for the full CREATE spec before implementing.

### Step 1 — Register CREATE capability
In `runtime/capability_registry.py` (or equivalent), register:
```
capability: "CREATE"
sub_capabilities:
  - CREATE_FILE         → llm_file_agent.py
  - CREATE_DRAFT        → draft_agent.py
  - CREATE_MODEL        → model_gen_agent.py
  - READ_FILE_CONTEXT   → file_reader_agent.py
required_tier: REASONING  (file generation needs strong LLM)
```

### Step 2 — Executive dispatch
`executive.py` reads CREATE intent from `CognitivePlan` and dispatches to capability registry → correct tool. File output goes to `Output/` directory (David's Desktop/Output, already the output convention).

### Step 3 — Output gate
CREATE output is NEVER auto-delivered without David's confirmation gate. Draft is produced, stored in `data/create_drafts/`, and eLo notifies David: "I've made a draft of X — want to see it?" David's confirmation → delivery. This is the L3 gate (LAW-017): eLo prepares, David approves before anything writes or emits.

### Step 4 — Response gate integration
CREATE output passes through `response_gate.py` (WO-RESPONSE-GATE) before notification to David.

---

## Definition of Done

- [ ] AT-1: `CREATE` capability appears in the capability registry and is dispatchable.
- [ ] AT-2: Executive receives intent "create a draft of X" → dispatches to `draft_agent.py` → draft written to `data/create_drafts/`.
- [ ] AT-3: eLo's notification to David ("I've made a draft…") is emitted but the file is NOT auto-opened or auto-delivered.
- [ ] AT-4: `llm_file_agent.py` can be invoked via the capability registry (import + call test).
- [ ] AT-5: CREATE capability is listed in `_TIER_CAPABILITY` dict in `backend_router.py` (after BA-11 removes ladder).
- [ ] AT-6: Full test suite passes with no new failures.

---

## Files in scope

- `runtime/capability_registry.py` (register CREATE)
- `runtime/executive.py` (dispatch CREATE — Builder-only)
- `runtime/backend_router.py` (`_TIER_CAPABILITY` entry)
- `tools/llm_file_agent.py`, `tools/draft_agent.py`, `tools/model_gen_agent.py`, `tools/file_reader_agent.py` (read-only — do not rewrite)
- `data/create_drafts/` (create directory)

## Files NOT in scope

- `Output/` (destination for approved files only — do not auto-write there)
- Unity / Design / MT files
