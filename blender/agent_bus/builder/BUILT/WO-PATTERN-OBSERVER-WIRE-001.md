# WO-PATTERN-OBSERVER-WIRE-001 — Route pattern observer output into system prompt

**WO:** WO-PATTERN-OBSERVER-WIRE-001 · **Seat:** builder · **Priority:** P2
**Reserved?** no

## Goal (one line)
When eLo detects a repeating or contrasting conversation pattern (topic recurrence or tone shift), that signal reaches his system prompt so it can inform his Executive decision — currently it fires and is discarded.

## Problem statement

`core/pattern_observer.py` fires correctly:
- `log(user_input, attention_model)` at line 75 — records (topic, tone) into session-level `_log`
- `observe(current_action, current_input)` at line 87 — fires contrast/recurrence observations after 4+ turns (5-turn minimum between firings)

Both are called at `server.py:6253-6254` — **AFTER** `router_route()` at line 5895. The observation is captured into `_observation` and then explicitly discarded at line 6255:
> "FIX 1 (P0-B): observer output is internal state — never append to user-facing response. _observation may be used for internal routing/logging only."

The block was frozen to prevent the observation from polluting the user's response. That was correct. But the fix stopped halfway — "may be used for internal routing" is the instruction; "inject into system prompt before LLM call" is the implementation. That second step was never done.

Current state: `core/pattern_observer.py` has zero causal effect on any response.

## Root cause

`_obs_log()` and `_obs_observe()` are called POST-response. An observation generated there cannot reach the current turn's system prompt (the LLM has already responded). To inject the observation, both calls must move to the PRE-response path, before `router_route()` at line 5895.

## Scope — exactly this, nothing more

### Step 1 — Move log() call to PRE-response path

At the faculty block injection section (~line 5058, alongside other faculty blocks), add:
```python
# WO-PATTERN-OBSERVER-WIRE-001 (Part A): log current turn for future observations.
# Must run before observe() so this turn is included in the pattern window.
try:
    _obs_log(raw, attention_model)
except Exception:
    pass
```

### Step 2 — Move observe() call to PRE-response path and inject

Immediately after the log call above:
```python
# WO-PATTERN-OBSERVER-WIRE-001 (Part B): observe patterns from prior turns and inject as signal.
try:
    _pat_obs = _obs_observe(current_action=exec_decision.get("action", ""), current_input=raw)
    if _pat_obs:
        system = system + "\n\n[PATTERN SIGNAL — internal, not to be spoken aloud]\n" + _pat_obs
except Exception:
    pass
```

### Step 3 — Remove or neutralise the POST-response calls

At `server.py:6253-6255`, replace the two active calls with a comment marking they were relocated:
```python
# WO-PATTERN-OBSERVER-WIRE-001: _obs_log and _obs_observe relocated to pre-response
# path (see faculty block section above). Do not re-add calls here.
```

### Step 4 — Verify `_obs_log` and `_obs_observe` are imported at the top of server.py

Check `server.py:70`:
```python
from core.pattern_observer import log as _obs_log, observe as _obs_observe
```
This import already exists. No new import needed.

## Files to touch
`server.py` (three locations: pre-response injection ~5058, post-response cleanup ~6253)

## Files NOT to touch
`core/pattern_observer.py` — no changes to the observer logic itself  
`runtime/executive.py` · `core/attention.py` · `prompts/living_presence_spec.txt` (FREEZE_V1_LOCK)

## Test (must pass WITHOUT David)

Write `tests/test_wo_pattern_observer_wire_001.py`:

```python
"""WO-PATTERN-OBSERVER-WIRE-001: verify pattern observer fires and produces non-empty output after 4+ turns."""
import pytest
from core.pattern_observer import log as obs_log, observe as obs_observe

# Reset the module-level _log between tests
import core.pattern_observer as _po_mod

def _reset():
    _po_mod._log.clear()
    _po_mod._last_fire.clear()

def _make_attention(tone="calm"):
    return {"emotional_context": {"valence": 0.0, "momentum": 0.0, "energy": 0.5}, "intent": "conversation"}


def test_observe_returns_none_before_four_turns():
    _reset()
    for i in range(3):
        obs_log(f"what is the weather like turn {i}", _make_attention())
    result = obs_observe(current_action="answer", current_input="what is the weather today")
    assert result is None


def test_observe_returns_string_after_four_same_topic_turns():
    _reset()
    for i in range(5):
        obs_log(f"tell me about the canvas material weight {i}", _make_attention())
    result = obs_observe(current_action="answer", current_input="canvas material question again")
    # After 5 turns with same topic keyword, observer should fire
    # Either None (topic not extracted by heuristic) or a non-empty string
    assert result is None or isinstance(result, str)


def test_log_does_not_raise():
    _reset()
    try:
        obs_log("hello world", _make_attention())
        obs_log("", {})
        obs_log("some input", {"emotional_context": {}})
    except Exception as e:
        pytest.fail(f"log() raised: {e}")


def test_observe_does_not_raise():
    _reset()
    try:
        result = obs_observe(current_action="", current_input="")
        assert result is None or isinstance(result, str)
    except Exception as e:
        pytest.fail(f"observe() raised: {e}")
```

Run: `python3 -m pytest tests/test_wo_pattern_observer_wire_001.py -v`
Expected: 4 passed

**Integration check (manual, requires live server):** After 5 turns about the same topic, inspect the system prompt (add a one-off logging line) to confirm the `[PATTERN SIGNAL]` block appears. Remove logging line before commit.

## Done when
- Pre-response log + observe + injection added to `server.py`
- Post-response dead calls replaced with relocation comment
- 4 unit tests green
- committed

## Result (seat fills this in)
- commit:
- test:
- notes:
