# WO-RELATIONSHIP-STYLE — Result Card

**Status:** DONE  
**Completed:** 2026-08-30  
**Authority:** David L3 — WO-RELATIONSHIP-STYLE dispatch; SPEC_relationship_style_2026-08-30.md  
**verified_done counter:** 96

---

## What was built

### A. `runtime/spine/relationship_faculty.py` (modified)

Added to `RelationshipContext` dataclass:
```python
relationship_mode: str = "developing"   # new | developing | established | in_conflict | post_conflict
```

Added signal sets:
- `_CONFLICT_SIGNALS` — frustration/correction phrases that override familiarity thresholds
- `_REPAIR_SIGNALS` — reconciliation phrases that trigger post_conflict

Added helper:
```python
def _derive_relationship_mode(raw_lower: str, familiarity: float) -> str:
    # Priority: conflict signals → repair signals → familiarity thresholds
    # < 0.35 → new | 0.35–0.65 → developing | ≥ 0.65 → established
```

Wired into `analyse()` — `relationship_mode` now set on every returned `RelationshipContext`.

### B. `kernel/relationship_register.py` (new)

`get_style(mode: str) -> dict` — returns `{forbidden, required, texture}` per mode:

| Mode | Forbidden | Texture |
|---|---|---|
| new | assumed-familiarity callbacks ("as we discussed", "remember when", etc.) | more explanatory; open questions; no assumed context |
| developing | (none) | callbacks begin; humour starts; settled voice |
| established | setup/scaffolding phrases ("just to clarify", "let me explain", etc.) | direct; trusts shared context; holds position |
| in_conflict | performative care ("I hear you", "that sounds hard", "I apologise for", etc.) | honest without escalating; shorter turns; names what's happening |
| post_conflict | over-apologetic phrases ("I promise I'll", "I'll make it up", "never again", etc.) | steady; no over-correction; lets thread rebuild naturally |

Unknown mode falls back to `developing` — never raises.

---

## Acceptance tests — tests/test_wo_relationship_style.py

| AT | Description | Result |
|----|-------------|--------|
| AT-1 | NEW mode: familiarity=0.20 → mode='new'; assumed-familiarity callbacks in forbidden | ✅ |
| AT-2 | ESTABLISHED mode: familiarity=0.75 → mode='established'; setup phrases forbidden; texture='direct' | ✅ |
| AT-3 | IN_CONFLICT: conflict signal in raw → mode='in_conflict'; care phrases forbidden | ✅ |
| AT-4 | POST_CONFLICT: repair signal in raw → mode='post_conflict'; apology phrases forbidden | ✅ |
| AT-5 | Core character: all 5 modes have full keys; unknown mode falls back cleanly | ✅ |
| AT-6 | py_compile clean on both files | ✅ |

**6/6 PASS**

No regressions: WO-PLANETARY-KERNEL 6/6, WO-PROVENANCE 7/7, WO-CCM-SPINE 6/6.

---

## Spec coverage

Per SPEC_relationship_style_2026-08-30.md:
- §A: Relationship mode wired to language shaping — `relationship_mode` on `RelationshipContext`, accessible to Executive Faculty
- §B: Single new parameter `relationship_mode` on `RelationshipContext` — no new faculty, extended existing
- §C: Core character never changes across modes — no mode removes eLo's voice; only forbidden phrases differ
