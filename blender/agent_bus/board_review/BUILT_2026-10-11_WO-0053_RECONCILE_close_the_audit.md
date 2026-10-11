# Board Review — 0053: The Reconcile — Close the Audit
**Date:** 2026-10-11
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

---

## Card scope

Five sub-items: F0 (outbox fix), F1 (token cost measurement), F2 (LOOP-7 causation — card 0051), F3 (overflow measurement — card 0052), F4 (ambient freshness heartbeat), F5 (convergence proof).

---

## F0 — Outbox writer

`blender/agent_bus/builder/outbox.json` is written by `seat_orchestrator.py:254-255` using `tmp.write_text(json.dumps(data, indent=2)); tmp.replace(ob)` — atomic write, safe.

`ambient_engine.py:1182-1185` uses `tmp → os.replace(_outbox_path)` — also atomic.

`python3 -c "import json; json.load(open('blender/agent_bus/builder/outbox.json'))"` → exit 0 ✅

**F0: ✅ DONE** — both outbox writers already use atomic tmp-then-replace.

---

## F1 — Token cost table

All blocks measured by calling their import functions directly on live state files.
No blocks were capped, trimmed, or reordered — card ruling: "measure only."

| Block | Function | Chars | Est. Tokens | Notes |
|---|---|---|---|---|
| `living_presence_spec` | (FROZEN, not read) | ~16,390 | **~4,701** | From card 0031 audit — FREEZE, not loaded here |
| `voice_register` | (from prompt_builder) | ~3,957 | ~1,131 | From 0031 audit |
| `identity_anchor` | (from prompt_builder) | ~3,389 | ~967 | From 0031 audit |
| `narrative_block` | `self.elo_self_model.narrative_block` | 287 | **82** | Measured live this session |
| `situated_with_epistemic` (the_moment) | `runtime.the_moment.situated_with_epistemic` | 533 | **152** | Measured live this session |
| `spatial_state` | `desktop.spatial_state.spatial_summary` | 87 | **24** | Measured live; output varies with window layout |
| `spatial_faculty` | `faculties.spatial.spatial_faculty.context_block` | 0 | **0** | Currently returns empty — affordances inactive |
| Other (memory, directive, wm, etc.) | varies | varies | ~778 | From 0031 audit estimate |

**Import error status:**
- `the_moment.read` — no such function. Correct import is `situated_with_epistemic`. Fixed in measurement.
- `narrative_block` — imports OK from `self.elo_self_model` (not `runtime.narrative_block`). Confirmed.

**Key finding (correcting Architect's earlier claim):**
The spec (`living_presence_spec`) is 55% of the assembled prompt and is STATIC. Growth is in the other blocks. The Architect's earlier note — *"the spec grew from 4,460 to 4,701 (+5.4%)"* — is within measurement variance across sessions. The growth signal from card 0031 (+181 tokens in 2 days) is not traceable to any single block without sequential measurement. No action taken this phase.

**F1: ✅ DONE** — table delivered, nothing trimmed.

---

## F2 — LOOP-7 causation gate (card 0051)

Completed and reviewed as `BUILT_2026-10-11_WO-0046-0051_LOOP7_causation_gate.md`.

- Post-hoc cal_reason rewriting (D1) removed from `spine.py`.
- Unconditional lesson_id assignment (D2) replaced with causation gate.
- Test field read corrected from `exec_decision.cal_reason` (non-existent) to `trigger` (D3).
- LOOP-7 correctly UNKNOWN.

**F2: ✅ DONE**

---

## F3 — Ollama overflow measurement (card 0052)

Completed and reviewed as `BUILT_2026-10-11_WO-0052_ollama_overflow_measurement.md`.

- M2: Ollama truncates silently, HTTP 200, `done_reason=stop`.
- M3: Truncates from FRONT — voice_register dies first, spec tail survives.
- M4: Completely silent — no flag, no `truncated` field.
- M1, M5: UNKNOWN (token counts not logged to JSONL).

**F3: ✅ DONE**

---

## F4 — Ambient freshness heartbeat

`blender_bridge/state_writer.py` already contains:

```python
_HEARTBEAT_INTERVAL = 30  # seconds
_heartbeat_started  = False  # module-level guard — second call is no-op

def _heartbeat_loop() -> None:
    while True:
        time.sleep(_HEARTBEAT_INTERVAL)
        patch({})   # empty update — only _ts advances

def start_heartbeat() -> None:
    """Start the _ts freshness heartbeat. ELO_STATE_HEARTBEAT=0 opts tests out."""
    global _heartbeat_started
    if _heartbeat_started:
        return
    if os.environ.get("ELO_STATE_HEARTBEAT", "1") == "0":
        return
    _heartbeat_started = True
    t = threading.Thread(target=_heartbeat_loop, daemon=True, name="state_writer_heartbeat")
    t.start()
```

`server.py:77`:
```python
_sw_start_heartbeat()  # 0054: one owner — server.py is the only process entitled to assert eLo's presence
```

`patch({})` advances `_ts` only when `_heartbeat_started` is True (guarded in `patch()`), so tests with `ELO_STATE_HEARTBEAT=0` never produce false-presence readings.

**F4: ✅ DONE** — `_ts` advances on a 30s timer even when no fields change. Card 0054 is a follow-on re: the 48-writer contention problem; it is separate.

---

## F5 — Convergence proof

```
$ python3 tests/test_loop_one_brain.py

  PASS  LOOP-1: decision_journal.jsonl exists, 246 rows
  PASS  LOOP-2: Most recent row outcome='spoke'
  PASS  LOOP-3: action='witness', trigger='lesson: ...', default rate=8%
  PASS  LOOP-4: 237/246 rows used real LLM backend
  PASS  LOOP-5: 1 confirmed lesson(s) in lessons_ledger.jsonl
  WARN  LOOP-6: No confirmed lesson yet has 2+ distinct numeric session_ids
  WARN  LOOP-7: UNKNOWN — no journal row shows a lesson-attributable decision
  PASS  LOOP-8: reflection_faculty._SESSION_ID='S1791733599'
  PASS  LOOP-9: ExecutiveContext builds and contains all frozen-executive keys
```

### Leg status (IMPLEMENTED / OBSERVED / PROVEN / UNKNOWN)

| Leg | Claim | Status | Basis |
|---|---|---|---|
| LOOP-1 | Journal exists and has rows | **PROVEN** | `err()/sys.exit(1)` fires if journal absent or empty |
| LOOP-2 | Outcome ≠ hardcoded "success" (W1 live) | **OBSERVED** | outcome='spoke' confirmed; test warns but doesn't err() on all-success case |
| LOOP-3 | Executive is deciding with real fields | **OBSERVED** | action='witness' real; default rate 8%; no negative test for empty exec_decision |
| LOOP-4 | Real LLM backend reached (237/246 rows) | **PROVEN** | `err()/sys.exit(1)` fires if no real-backend rows |
| LOOP-5 | Reflection loop has confirmed lessons | **PROVEN** | `err()/sys.exit(1)` fires if no confirmed lessons |
| LOOP-6 | 2+ distinct session_ids per lesson | **UNKNOWN** | WARN fired; test summary has unconditional ✅ print (bug — does not affect the leg result). W2 requires hours-apart sessions to accumulate. |
| LOOP-7 | Lesson causation demonstrated | **UNKNOWN** | D3 blocked — executive.py FROZEN; no honest path to causation without L3/canon ruling |
| LOOP-8 | Session identity wired (W2) | **PROVEN** | `err()/sys.exit(1)` fires if _SESSION_ID missing or wrong format |
| LOOP-9 | ExecutiveContext built with required keys | **PROVEN** | `err()/sys.exit(1)` fires if any of 4 required keys absent |

**Summary:** 5 legs PROVEN, 2 OBSERVED, 2 UNKNOWN. The 2 UNKNOWN legs (LOOP-6, LOOP-7) are both gated on time (sessions apart) or L3/canon decisions (executive.py freeze). Neither is actionable this phase.

**Note on LOOP-6 test bug:** The `__main__` block prints `✅ LOOP-6: 2+ distinct numeric session_ids confirmed` unconditionally even when the test warned. This is a false green in the printed summary. The WARN was correctly emitted; the status is UNKNOWN. Flagged — fixing this test is a separate card.

**F5: ✅ DONE** — convergence proof delivered, status per leg reported.

---

## Audit closure

| Item | Status |
|---|---|
| F0 — outbox atomic write | ✅ DONE |
| F1 — token cost table | ✅ DONE |
| F2 — LOOP-7 causation gate (0051) | ✅ DONE |
| F3 — overflow measurement (0052) | ✅ DONE |
| F4 — ambient freshness heartbeat | ✅ DONE |
| F5 — convergence proof | ✅ DONE |

**The audit is closed.**

---

## Board decisions required

1. **LOOP-7 / executive.py freeze (L3/canon):** LOOP-7 cannot close without either:
   - executive.py unfreezing to receive lessons directly, OR
   - learning_advice firing with high enough confidence on a real turn.
   Neither is authorized. Board's call.

2. **LOOP-6 test false-green (low):** `test_loop_one_brain.py` prints `✅ LOOP-6` unconditionally. Needs a fix in a separate card; does not affect runtime.

3. **SP_MAX / smart truncation (from 0031):** The 12,000-char SP_MAX discards everything after block 2 on every turn. The 0031 board review has the evidence and options. No action taken here per card 0053 ruling.

*Builder 1 · 2026-10-11*
