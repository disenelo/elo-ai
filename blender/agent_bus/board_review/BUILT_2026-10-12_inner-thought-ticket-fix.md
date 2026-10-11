# Board Review — Inner Thought: Ticket consumed before Ollama finished
**Date:** 2026-10-12
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

---

## Root cause

`ThoughtInFlight.collect()` set `_collected = True` on timeout even when the thread was still running. The pre-spine collect (timeout_s=0.35) fired long before Ollama finished (~17s under contention), consuming the ticket permanently. Every later collect — including `_run_inner_thought` daemon — returned `""`. Thought generated but unreachable.

## Fix

**`faculties/inner_thought/early_runner.py`**
- `ThoughtInFlight.collect()`: on timeout (thread still alive), returns `""` WITHOUT setting `_collected = True`. Ticket preserved for a later caller with more time.

**`server.py:9108`**
- `_run_inner_thought` daemon: collects with `timeout_s=30.0` (was `None` → default 0.35). Daemon runs after reply generation (~17s), so thought has had that long to form.

---

## What David reported vs what this fixes

> "I hear it" (TTS works) · "the -- thoughts don't show anymore"

David heard it on fast turns (thought completed in <0.35s, pre-spine collect fired). On slow turns (Ollama under load), the ticket was consumed and the daemon got nothing → neither `_publish_text()` nor `_voice_speak_inner()` fired.

Both paths now work: fast turns collected early (still published), slow turns collected by daemon with 30s ceiling.

---

## Verification

```
python3 -c "
from faculties.inner_thought.early_runner import ThoughtInFlight
import time

handle = ThoughtInFlight('test')
def slow_gen():
    time.sleep(0.5)
    return 'a slow thought arrives'
handle._spawn(slow_gen)

t1 = handle.collect(timeout_s=0.05)  # fast collect — NOT consumed
print('fast:', repr(t1), '_collected:', handle._collected)
# → fast: '' _collected: False  ✓

t2 = handle.collect(timeout_s=1.0)   # slow collect — gets result
print('slow:', repr(t2), '_collected:', handle._collected)
# → slow: 'a slow thought arrives' _collected: True  ✓

t3 = handle.collect(timeout_s=1.0)   # idempotent
print('third:', repr(t3))
# → third: ''  ✓
"
```

All three assertions confirmed.

---

## Board decisions required

None.

*Builder 1 · 2026-10-12*
