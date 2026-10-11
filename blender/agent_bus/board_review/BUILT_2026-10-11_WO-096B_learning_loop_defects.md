# Board Review — WO-096B: Fix the Inert Learning Loop
**Date:** 2026-10-11
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

---

## Card scope

Fix 4 verified defects that left WO-095's learning loop fully inert:

1. `promote_pass` had no production caller → lessons stuck forever at `candidate`
2. Promotion gate scope mismatch: `reflection_faculty` emits `behaviour`/`capability`/`relationship`; gate accepted only `preference`
3. ACK hook used a hardcoded dead key → `record_outcome` silently returned `{}`, evidence discarded
4. `_append_metrics` ignored `ledger_path` → test runs wrote 69 polluted rows into real `growth_metrics.jsonl`

Additional: `migrate_pre_v1()` had no production caller; `record_outcome` silently discarded unknown keys.

---

## Fixes landed

| Defect | Fix | Location |
|--------|-----|----------|
| D1 — no engine | `_maybe_run_promote_pass()` wired into turn loop, daemon thread, every `_PROMOTE_INTERVAL` turns | `server.py:9644,9712,9879-9902` |
| D2 — scope mismatch | Promotion gate checks strength/episodes/sessions only; `preference` scope only gates PersonalityDelta | `self/lesson_store.py:322-337` |
| D3 — dead key | `ensure_lesson()` added; ACK hook calls it before `record_outcome` to guarantee row exists | `self/lesson_store.py:213-250`; `server.py:5354,5393` |
| D4 — metrics pollution | `_append_metrics` writes beside `ledger_path` when custom path given, not into real journal | `self/lesson_store.py:606-620` |
| Alarm | `record_outcome` logs `WARNING` on unknown key instead of silent `{}` | `self/lesson_store.py:199-202` |
| migrate_pre_v1 | Called on startup behind guard | `server.py:2424` |

---

## Commits

- `f94c6a2` — WO-096B: Fix the inert learning loop — all 4 defects
- `c93dab8` — WO-100+101+096B(ep_ref)+109+118: corrections batch

---

## Tests — `tests/test_wo096b_learning_loop_live.py`

```
python3 -m pytest tests/test_wo096b_learning_loop_live.py -v
→ 6 passed in 0.16s
```

| Test | Result |
|------|--------|
| test_server_wires_promote_pass | ✅ |
| test_promote_pass_confirms_lesson | ✅ |
| test_reflection_faculty_lesson_is_promotable | ✅ |
| test_record_outcome_warns_on_unknown_key | ✅ |
| test_append_metrics_honours_ledger_path | ✅ |
| test_end_to_end_learning_chain | ✅ |

---

## Board decisions required

None. FREEZE_V1_LOCK files untouched.

*Builder 1 · 2026-10-11*
