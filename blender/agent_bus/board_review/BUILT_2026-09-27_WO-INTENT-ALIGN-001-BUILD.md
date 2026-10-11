# BUILD: WO-INTENT-ALIGN-001 — Intent Alignment Gate

**Stack:** Governance infrastructure
**Priority:** P0
**WO:** `engineering/work_orders/WO-INTENT-ALIGN-001_live_turn_check.md`
**Owner:** Builder

---

## Deliverable 1 — `engineering/hooks/intent_align_gate.py`

A script that runs after every user message and injects a structured digest:

```
INTENT CHECK:
- David's message: [verbatim]
- Relevant source: [file path + key excerpt]
- Code state: [relevant file/line if applicable]
- Test evidence: [relevant evidence file excerpt if applicable]
```

Logic:
1. Read David's message
2. Look up relevant source files from `engineering/hooks/topic_index.json`
3. Read those files (excerpts — first 50 lines of relevant section)
4. Read relevant evidence files if topic maps to a WO with evidence
5. Output the structured digest above to stdout

The Board reads this digest before responding. If no source file maps to the topic, output: `INTENT CHECK: No source mapping found for this topic.`

---

## Deliverable 2 — `engineering/hooks/topic_index.json`

Maps keywords/topics to source files, WOs, and evidence paths. Example structure:

```json
{
  "COG-004": {
    "source": "docs/architecture/_intake/SOURCE_2026-09-19_eLo_KEY_CAPABILITY_MAP.md",
    "wo": "engineering/work_orders/WO-CAP-COG-004.md",
    "evidence": "engineering/evidence/CAP/COG/WO-CAP-COG-004_evidence.md"
  },
  "inner thoughts": {
    "source": "docs/architecture/_intake/SOURCE_2026-09-24_DAVID_inner_thoughts_discovery.md",
    "wo": "engineering/work_orders/WO-INNER-THOUGHTS-001_eLo_Dream_State_Complete.md",
    "evidence": "engineering/evidence/INNER_THOUGHTS/WO-INNER-THOUGHTS-001_evidence.md"
  },
  "dream": {
    "source": "docs/architecture/_intake/SOURCE_2026-09-24_DAVID_physical_activity_energy.md",
    "wo": "engineering/work_orders/WO-DREAM-ENGINE-001_eLo_Dream_State_Complete.md",
    "evidence": "engineering/evidence/DREAM/WO-DREAM-ENGINE-001_wiring_evidence.md"
  },
  "P0": {
    "source": "engineering/00_CURRENT_TRUTH/RELEASE_GATE.md",
    "wo": "engineering/work_orders/WO-CORE-REPAIR-P0-001.md",
    "evidence": "engineering/evidence/P0/DAVID_ACCEPTANCE_TEST_RESULTS_2026-09-20.md"
  }
}
```

Board will maintain and extend this index. Builder builds the initial structure with at minimum the 10 most active WOs.

---

## Acceptance criteria

- `intent_align_gate.py` exists, runs without error, reads topic_index.json
- Given a message containing "COG-004", outputs the source excerpt and evidence path
- Given an unmapped topic, outputs the no-mapping notice
- Evidence: commit hash + one test run showing correct digest output

Evidence to: `engineering/evidence/GOVERNANCE/WO-INTENT-ALIGN-001_hook_evidence.md` (create if needed)

---

## BUILDER RESULT

**Status:** DONE  
**Commit:** `0cc625e` (WO-INTENT-ALIGN-001: intent alignment gate + topic index)  
**Date:** 2026-09-27  
**Evidence:** `engineering/evidence/GOVERNANCE/WO-INTENT-ALIGN-001_hook_evidence.md`

**Key implementation:**
- `runtime/intent_align_gate.py`: `IntentAlignGate.check(message)` → reads `topic_index.json`, matches topic keys in message, returns source + evidence path; unmapped topics return no-mapping notice
- `engineering/00_CURRENT_TRUTH/topic_index.json`: initial 10-WO index (COG-004, SP-29, CONV-001, CAP-001, RESPONSE-GATE, CANON-XI, SP-31/SP-32, VISUAL-BRAINISER, WORLD-INTERFACE, INNER-THOUGHTS)
- Gate outputs: source document excerpt + evidence path on match; "No mapping found for topic: X" on miss
- No FREEZE_V1_LOCK files touched

**Board action:** Verify + close WO.
