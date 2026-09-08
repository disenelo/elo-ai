# WO-PROVENANCE — Result Card

**Status:** DONE  
**Completed:** 2026-08-30  
**Authority:** David L3 — WO-PROVENANCE authorisation 2026-08-30  
**Source:** SOURCE_ALIGNMENT_REGISTER_2026-08-30.md G-13; BOARD COMMAND — eLo Response Authority §memory integrity

---

## What was built

### runtime/response_authority_guards.py (modified)

- Removed "not yet wired" stub comment
- Added provenance imports block — `EpistemicClass` from `memory.provenance` (guarded try/except; safe if module missing)
- `_EPISTEMIC_HIGH` = {CANONICAL, CURRENT_STATE, CURRENT_SESSION} → claim stands
- `_EPISTEMIC_MEDIUM` = {RETRIEVED_MEMORY, RETRIEVED_LORE} → qualify "I think…"
- `_EPISTEMIC_LOW` = {INFERRED, GENERATED, UNKNOWN} → qualify "I'm not certain, but…"
- `guard_d3_contradiction_resurrection()`: added `memory_provenance: dict | None = None` param (backward compatible); when `_epistemic_class` key present and class is not HIGH, applies provenance-calibrated qualifier
- `apply_authority_guards()`: added `memory_provenance` param; when `tool_agent` is set, injects `EpistemicClass.GENERATED` automatically so D-2→D-3 provenance thread is seamless

### memory/vault_layer.py (modified)

- `write_memory()`: added `epistemic_class: str | None = None` param (defaults to `"verified"`)
- `_write_summary_note()`: writes `epistemic_class: <value>` in YAML frontmatter
- `_write_deep_note()`: writes `epistemic_class: <value>` in YAML frontmatter

---

## Acceptance tests — tests/test_wo_provenance.py

| AT | Description | Result |
|----|-------------|--------|
| AT-1 | "not yet wired" stub removed; EpistemicClass wired | ✅ |
| AT-2 | INFERRED claim → qualified "I'm not certain, but…" | ✅ |
| AT-3 | CANONICAL claim → passes unmodified | ✅ |
| AT-4 | vault write includes epistemic_class in summary + deep notes | ✅ |
| AT-5 | D-2 tool_agent injects GENERATED → D-3 qualifies | ✅ |
| AT-6 | WO-GUARD-001 tests (6/6) remain green | ✅ |
| AT-7 | py_compile clean | ✅ |

No regressions: WO-CCM-SPINE 6/6, WO-SP29 6/6, WO-RESPONSE-GATE 7/7, WO-DREAM-STATE 6/6.

---

## Notes on enum mapping

Actual `EpistemicClass` values differ from WO card description:
- WO card "VERIFIED" → implemented as CANONICAL / CURRENT_STATE / CURRENT_SESSION (high confidence)
- WO card "INFERRED" → EpistemicClass.INFERRED (matched exactly)
- WO card "HYPOTHETICAL" (not in actual enum) → mapped to GENERATED / UNKNOWN (low confidence)

Default for vault writes that don't specify epistemic_class: `"verified"` (experienced events per WO spec).
LLM-generated summaries should pass `epistemic_class="inferred"` at their call site.
