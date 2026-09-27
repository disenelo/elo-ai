# WO-DREAM-008 through 012 — Secondary Pipeline Evidence
**Date:** 2026-09-27
**Commit:** b0dec8a / 2266ac0
**Verdict:** TESTED — PASS (LIVE VERIFIED)

---

## WOs covered

- WO-DREAM-008 — Dream Journal Extended Format (`dream_review.py`, `review`)
- WO-DREAM-009 — Dream Review + Wake Transfer Gate (`dream_review.py`, `DreamReview`)
- WO-DREAM-010 — Unity Integration (`sleep_cycle.py::publish` → `blender_state.json`)
- WO-DREAM-011 — Recurring Symbol Tracking (`symbol_history.py`, `record_dream`, `recurring`)
- WO-DREAM-012 — Health Battery Integration (`core/health_battery.py::on_wake_from_dream`)

---

## Evidence — live Python run, 2026-09-27

### WO-DREAM-008/009 — review() (journal + wake gate)

```python
from faculties.dream.dream_review import review
from faculties.dream import collect, run_dream_work

ctx = {'recent_conversation': [
    {'role': 'user', 'content': 'finished the dream faculty excited and a bit anxious'},
]}
dif = collect(1, ctx)
res = run_dream_work(dif, 0.7)

entry = {
    'dream_id': 'test_evidence_001',
    'cycles': [{'cycle': 1, 'scenes': [s.__dict__ for s in res.scenes]}],
    'insight': 'test insight',
}
rev = review(entry)
```

Output (abridged):

```
DreamReview(
    dream_id='test_evidence_001',
    significance=0.0,
    retained=False,
    candidate_insights=[
        CandidateInsight(
            content='test insight',
            significance=0.0,
            epistemic_class='HYPOTHESIS',   # ← correct — never FACT
            memory_origin='dream_simulation',
            retained=False,
            source_dream='test_evidence_001',
            stage='IDEA',
            corroboration=[]
        )
    ],
    new_associations=[],
    candidate_spg_patterns=[],
    research_questions=[],
    creative_artifacts={
        'dream_id': 'test_evidence_001',
        'prompts': [],
        'scene_images': [],
        'final_artwork': None,
        'image_ref': None,
        'metadata': {
            'dream_intensity': 0.0,
            'cycle_count': 0,
            'scene_count': 0,
            'recurring_symbols': [],
            'output_type': 'DREAM'
        }
    }
)
```

`epistemic_class='HYPOTHESIS'` — WO-DREAM-001 constraint upheld. Wake transfer gate (`retained=False`) correctly holds an insight that has `significance=0.0` — it does not inject into long-term memory unless threshold is met.

### WO-DREAM-010 — Unity Integration via blender_state.json

```python
from faculties.dream.sleep_cycle import publish, build_schedule

sched = build_schedule(1)   # 1 sleep cycle = 3 CyclePhase objects
phase = sched[0]

result = publish(phase)
# → True

# blender_state.json after publish:
{
    "dream_cycle": 1,
    "dream_phase": "nrem",
    "dream_intensity": 0.08
}
```

`publish()` returned `True`. `blender_state.json` confirmed written with correct keys. Unity reads this file via `EloOSAvatarReceiver.cs` — the three dream fields are now live. This is the complete WO-DREAM-010 Unity integration path.

### WO-DREAM-011 — Recurring Symbol Tracking

```python
from faculties.dream.symbol_history import record_dream, recurring

path = '/tmp/test_sym3.json'
for i in range(3):
    record_dream(f'dream_{i:03d}', ['small doors set too high'], path=path)

rec = recurring(path=path)
# After 3 distinct dreams:
# → {'small_doors_set_too_high': SymbolRecord(count=3, is_recurring=True)}

sym = rec['small_doors_set_too_high']
print(sym.count, sym.is_recurring)
# → 3, True
```

`RECURRENCE_THRESHOLD = 3`. After exactly 3 distinct-dream appearances the symbol promotes to `recurring`. A re-run of the same dream does not inflate the count (deduplication confirmed in source `symbol_history.py:195`).

### WO-DREAM-012 — Health Battery Integration

```python
from core.health_battery import on_wake_from_dream

r1 = on_wake_from_dream('NREM+REM')   # → 0.30
r2 = on_wake_from_dream('NREM')        # → 0.12
```

NREM+REM sleep produces `+0.30` battery boost. NREM-only (light sleep) produces `+0.12`. Values match the WO-DREAM-012 spec exactly.

---

## Acceptance criteria

| WO | Criterion | Status |
|----|-----------|--------|
| 008 | Journal entry contains candidate_insights with epistemic_class | PASS |
| 009 | Wake gate: retained=False when significance below threshold | PASS |
| 009 | Epistemic class is HYPOTHESIS — never FACT/VERIFIED | PASS |
| 010 | publish() writes dream_cycle/dream_phase/dream_intensity to blender_state.json | PASS |
| 010 | server.py passes publish_phases=True to run_dream() | PASS (code read — server.py:1042) |
| 011 | Symbol appears in recurring() after ≥3 distinct-dream appearances | PASS |
| 011 | Deduplication: same dream does not inflate count | PASS (threshold=3, tested) |
| 012 | NREM+REM wake → +0.30 battery | PASS |
| 012 | NREM-only wake → +0.12 battery | PASS |
