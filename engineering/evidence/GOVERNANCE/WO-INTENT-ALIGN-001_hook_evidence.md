# Evidence — WO-INTENT-ALIGN-001: Intent Alignment Gate

**Date**: 2026-09-26  
**Commit**: `0cc625e`  
**Files created**:
- `engineering/hooks/intent_align_gate.py`
- `engineering/hooks/topic_index.json`

---

## Test 1 — Mapped topic: "COG-004"

```
$ python3 engineering/hooks/intent_align_gate.py "COG-004"

INTENT CHECK:
- David's message: COG-004

--- Topic: COG-004 ---
- Relevant source: [docs/architecture/_intake/SOURCE_2026-09-19_eLo_KEY_CAPABILITY_MAP.md]
# VERBATIM — primary source, do not summarise
# Source: eLo — Key Capability Map.rtf
...
- Code state: engineering/cap_wos/board_review/WO-CAP-COG-004.json
- Test evidence: [engineering/evidence/CAP/COG/WO-CAP-COG-004_evidence.md]
...
```

**Verdict**: PASS — source excerpt and evidence path returned.

---

## Test 2 — Unmapped topic: "what about the weather today"

```
$ python3 engineering/hooks/intent_align_gate.py "what about the weather today"

INTENT CHECK:
- David's message: what about the weather today
- Relevant source: INTENT CHECK: No source mapping found for this topic.
```

**Verdict**: PASS — no-mapping notice returned.

---

## Topic index coverage (15 entries)

COG-004, COG-003, inner thoughts, dream, dream engine, health, energy, P0,
identity, ID-035, embodiment, intent align, stack, conversation grounding,
trigger phrases.

---

## Status

PASS — both acceptance criteria met. Board crosscheck required.
