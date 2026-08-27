# FROM BUILDER — WO-WORLD-001 Defect: `astral` declared
**Seat:** Builder  
**WO:** WO-WORLD-001 Defect — `astral` undeclared  
**Date:** 2026-08-27  
**Commit:** see below  

---

## D-1 — `astral>=2.2` added to requirements.txt ✅

One line added: `astral>=2.2` in alphabetical position between `anthropic` and `groq`.

---

## D-2 — 8/8 ATs PASS ✅

```
/Users/Disenelo/miniconda3/bin/python3 -m pytest tests/test_wo_world001_world_time_capability.py -q
........
8 passed in 1.31s
```

AT-1 (location configured) ✅  
AT-2 (mobile override) ✅  
AT-3 (absent) ✅  
AT-4 (sun populated with location) ✅  
AT-5 (sun absent without location) ✅  
AT-6 (sun absent without hint) ✅  
AT-7 (E-4 DomainHealth.failed) ✅  
AT-8 (spine capability_hint to world) ✅  

---

## D-3 — Collection gap noted ✅

The test file uses pytest-style assertions (`assert`). When collected by `python3 -m unittest`, 0 tests are reported and the suite appears to pass silently. This gap is programme-wide — any pytest-only test file is invisible to the unittest runner. Filed for Board assessment; test file not modified.

**Secondary note:** On Homebrew Python (`/opt/homebrew/bin/python3`), `pip install` is blocked by PEP 668 (system Python protection). The server runs on miniconda3 where `astral` installs correctly. The test runner must be miniconda3 Python for all elo-ai tests.

---

## Status

WO-WORLD-001 defect: CLOSED. Dependency declared. 8/8 PASS.  
Lane: WO-NAV-013 ✅ → WORLD-001 ✅ → WO-CAP-001 (Board-gated)

*Builder · 2026-08-27*
