# WO-PROVENANCE — Wire EpistemicClass / AuthorityLevel into D-2/D-3 Guards
**Seat:** Builder  
**Priority:** P2  
**Date:** 2026-08-30  
**Authorised:** David L3 global ruling 2026-08-30  
**Source:** SOURCE_ALIGNMENT_REGISTER_2026-08-30.md G-13; BOARD COMMAND — eLo Response Authority §memory integrity; `memory/provenance.py`  
**Lane note:** Builder ONLY.

---

## Intent

`memory/provenance.py` defines `EpistemicClass` and `AuthorityLevel` — a provenance contract for memory records. The D-2 (tool agent rewrite) and D-3 (memory claim qualify) guards in `runtime/response_authority_guards.py` currently have a stub comment reading "not yet wired" where the provenance check should be.

The source document (eLo Response Authority) requires: **memory claims must be qualified by their epistemic class** — eLo must know whether a memory is VERIFIED (experienced), INFERRED (concluded), or HYPOTHETICAL (guessed), and must qualify claims accordingly in its response.

---

## Scope

### ⚡ VERIFY FIRST
1. Run `python3 -c "from memory.provenance import EpistemicClass, AuthorityLevel; print(list(EpistemicClass))"` — confirm the enum values.
2. Grep `response_authority_guards.py` for "not yet wired" comment — confirm exact location.

### Step 1 — D-3 guard: memory claim qualification
In `response_authority_guards.py`, wire the D-3 guard:
- When eLo's draft response contains a memory claim ("I remember…", "Last time…", "You said…", "I know that…"):
  - Look up the memory record's `EpistemicClass` from the vault/WKG retrieve result.
  - If `EpistemicClass.INFERRED` → qualify the claim: "I think…", "As I understand it…"
  - If `EpistemicClass.HYPOTHETICAL` → qualify: "I may be wrong but…", "I'm not certain, but…"
  - If `EpistemicClass.VERIFIED` → claim stands unmodified.
  - If no provenance record found → apply `AuthorityLevel.LOW` qualification by default.

### Step 2 — D-2 guard: tool agent rewrite
When a tool agent produced the content (D-2 trigger), attach `EpistemicClass.INFERRED` to the claim before D-3 runs. Tool agent output is never VERIFIED by eLo's own experience.

### Step 3 — Attach EpistemicClass to vault writes
On memory vault write (write-path live from WO-067), attach `epistemic_class` field to the written record. Default: `VERIFIED` for experienced events, `INFERRED` for LLM-generated summaries.

---

## Definition of Done

- [ ] AT-1: The "not yet wired" stub comment in `response_authority_guards.py` is replaced with active code.
- [ ] AT-2: A response claiming "I remember X" where X has `EpistemicClass.INFERRED` is qualified to "I think X" or equivalent.
- [ ] AT-3: A response claiming "I remember X" where X has `EpistemicClass.VERIFIED` passes unmodified.
- [ ] AT-4: A vault write triggered by the memory write-path includes an `epistemic_class` field.
- [ ] AT-5: D-2 guard triggers before D-3 when content is from a tool agent (order preserved).
- [ ] AT-6: Existing D-1/D-2/D-3 tests (WO-GUARD-001 6/6) remain green.
- [ ] AT-7: Full test suite passes with no new failures.

---

## Files in scope

- `runtime/response_authority_guards.py` (wire D-2/D-3 provenance checks)
- `memory/provenance.py` (read-only — use existing EpistemicClass/AuthorityLevel)
- `memory/vault.py` or equivalent (add `epistemic_class` field to write)

## Files NOT in scope

- `runtime/executive.py` (D-2/D-3 are guard-layer, not executive decisions)
- Unity / Design / MT files
