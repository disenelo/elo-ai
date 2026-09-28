# FROM_BUILDER — Four-Layer Identity Model Suite

**Date:** 2026-09-11  
**Status:** DONE  
**Authority:** Board → Builder 2026-09-01 (David Four-Layer Identity Model verification request)

---

## Suite run

```
python3 -m pytest \
  tests/test_wo_vessel_loop_001.py \
  tests/test_wo_voice_register_001.py \
  tests/test_wo_inner_child_001.py \
  tests/test_consumption_invariant.py \
  tests/test_wo_expressed_elo_001.py \
  -v --tb=short
```

## Results

| File | Tests | Pass | Fail | Skip |
|---|---|---|---|---|
| test_wo_vessel_loop_001.py | 4 | 4 | 0 | 0 |
| test_wo_voice_register_001.py | 5 | 5 | 0 | 0 |
| test_wo_inner_child_001.py | 4 | 4 | 0 | 0 |
| test_consumption_invariant.py | 5 | 5 | 0 | 0 |
| test_wo_expressed_elo_001.py | 6 | 6 | 0 | 0 |
| **TOTAL** | **24** | **24** | **0** | **0** |

**Result: 24/24 PASS** (0 skipped — previous session Ollama skip not reproduced)

## Note on David's deeper question

"Is eLo choosing what it wants to say, or is the faculty just passing output through?" — the two-arm consumption invariant (test_consumption_invariant.py AT-2 through AT-4) is the current unit-test proof: prompt assembly differs between arms, context is injected, the arm is read-only. This proves the pipeline consumes context differently per arm. Live evidence from a conversational turn where eLo's expressed output demonstrably differs because of context injection remains the final proof. Board may open a dedicated investigation card.

— Builder · 2026-09-11
