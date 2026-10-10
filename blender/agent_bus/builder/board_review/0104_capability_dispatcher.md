# WO-B1-0104 — Capability Dispatcher — Board Review

**Moved by**: Builder 1  
**Date**: 2026-10-08  
**Commit**: 0dcc363

---

## What was built

### `runtime/capability_dispatcher.py` (new file)

**`classify(request)`** — pure regex tier classifier, sub-millisecond, zero LLM:
- `FACT` — time, date, tomorrow, yesterday, battery, disk, uptime, math expressions
- `STATE` — "what am I working on", "what's next", "what's my battery"
- `COGNITION` — "what should I do", "explain", "why", "help me decide"
- `UNKNOWN` — anything else (fall through to executive)

**`dispatch_fact(request)`** — deterministic FACT resolver:
- Tries `tools.system_primitives` (Builder 3 B3-0007) first
- Falls back to `_dispatch_fact_builtin()` when system_primitives unavailable
- Builtin handles: time, date, tomorrow, yesterday, math
- Battery/disk/uptime: gracefully return None until system_primitives arrives

**`_safe_eval_math(expr)`** — AST-gated arithmetic (no exec on arbitrary user input):
- Walks parse tree and rejects any non-arithmetic node
- Handles `+`, `-`, `*`, `/`, `**`, `//`, `%`

**`dispatch_state(request)`** — reads `company_state` for "what am I working on":
- Returns state dict with `source: elo_state, authority: recorded, confidence: 0.9`

### `server.py`

Added WO-0104 FACT-tier intercept after T11 (time/date fast-path):
- Only fires for FACT tier + dispatch_fact returns a non-None value
- Explicitly excludes time/date (T11 already handles those)
- Math expressions like "28 × 74" or "calculate 5+3*2" now answer without LLM
- Returns `{"response": ..., "mode": "direct", "backend": "capability_dispatcher"}`

### `tests/test_capability_dispatcher.py`

32 tests, all passing. Covers:
- classify() for all tiers and edge cases
- dispatch_fact() time/date/tomorrow/yesterday/math metadata shape
- Math correctness: 28×74=2072, 5+3=8, 100/4=25, 2+3×4=14
- Injection attack safety (exec path never fires)
- Performance gate (dispatch_fact < 1s → no LLM call)

---

## What's NOT done (blocked on Builder 3)

- Battery/disk/uptime dispatch — needs `tools/system_primitives.py` (B3-0007)
- These return None gracefully until B3-0007 arrives

---

## Status

✅ classify() — fully operational  
✅ dispatch_fact() — operational for time/date/math; falls through gracefully for battery/disk/uptime  
✅ server.py intercept — math fast-path live (time/date already covered by T11)  
✅ 32/32 tests passing  
⏳ Battery/disk/uptime — waiting on B3-0007
