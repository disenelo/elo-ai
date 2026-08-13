# Testing Standards — eLo OS

**Status:** ACTIVE
**Authority:** Lead Systems Architect

---

## Testing Philosophy

Every test validates behaviour, not implementation. Tests must pass before freeze. A passing test on broken behaviour is worse than no test.

**The test hierarchy:**

```
Unit Tests          — isolated components, mocked dependencies
Conversation Tests  — real exchanges with a running server
Desktop Tests       — embodiment behaviour (DISENELO Presence)
Unity Tests         — Unity avatar and game integration
Robot Tests         — physical embodiment (future)
Regression Tests    — prior frozen phase baselines
Stress Tests        — long sessions, edge cases, load
```

---

## Unit Tests

**Location:** `tests/test_[component_name].py`
**Runner:** `python3 -m pytest tests/ -v`

### Required Coverage

Every new component must have unit tests covering:

| Case | Description |
|---|---|
| Happy path | Normal input produces expected output |
| Empty input | `None` / `""` / `{}` → returns empty, does not raise |
| Malformed input | Bad types, missing keys → returns empty, does not raise |
| Long input | Very long strings do not crash |
| Component isolation | Executive is mocked — tests the component, not the full pipeline |

### What Unit Tests Must Not Do

- Never test the LLM response content (non-deterministic)
- Never call real external APIs (mock them)
- Never depend on `blender_state.json` file state
- Never depend on `.env` values in CI

---

## Conversation Tests

**Who runs them:** Conversation Reviewer
**When:** After implementation, before regression

### Protocol

Run at least 20 turns covering:

1. Greeting variations (yo, wagwan, safe, what's good)
2. Work discussion (game, robot, book — at most one per response)
3. Short inputs (single emoji, single word)
4. Tool invocations (weather, vision, news — confirm data is NOT echoed verbatim)
5. Avatar commands (wave, invade, scale)
6. Farewells (safe, in a bit, laters)
7. Emotional content (low energy, frustration, celebration)
8. The thing this work package changes — test it directly

### Acceptance Criteria

| Criterion | Standard |
|---|---|
| Response length | Conversational — sentences, not paragraphs. 1-3 lines unless explaining. |
| Project anchoring | Only when directly relevant to the input |
| Self-reference | Never "the system", "the platform", "the software" |
| Context echoing | Never raw CONTEXT block, raw headlines, raw data |
| Emoji response | Natural reply, no analysis or explanation |
| Identity | Never "nice to meet you" or first-meeting phrases |
| Anti-fabrication | Never invents errors, events, or details |

---

## Desktop and Embodiment Tests

**Who runs them:** Presence Reviewer
**When:** After conversation tests pass

### Protocol

1. Start DISENELO Presence app
2. Confirm eLo is visible and animated
3. Send 10 messages via the chat panel
4. Confirm blender_state.json updates each turn
5. Confirm voice fires on first bubble only
6. Confirm multi-bubble delivery (if applicable)
7. Run an "invade" command — confirm SpawnWave fires
8. Run scale commands — confirm avatar size changes

### Acceptance Criteria

- [ ] Avatar responds to every message
- [ ] No NullReferenceException in Unity console
- [ ] blender_state.json updated correctly per turn
- [ ] Voice does not fire when user is marked away
- [ ] Animation commands trigger correct animation

---

## Regression Tests

**Who runs them:** Regression Engineer
**When:** After all other tests pass, before Freeze Decision

The regression standard is zero tolerance. Every prior frozen phase baseline must pass. If it does not pass, implementation is rolled back, not the baseline.

See `engineering/templates/regression.md` for the full test matrix.

---

## Stress Tests

**Minimum protocol:**

| Test | Duration / Repetitions |
|---|---|
| Long session | 45 minutes continuous |
| Identical input loop | 10 identical messages |
| Rapid-fire | 20 messages in 60 seconds |
| Tool load | All tools invoked in sequence |
| Absent desktop | No app in focus |
| Vision off | ELO_VISION=false |

**What to watch for:**
- Memory growth (Python process size)
- Response time degradation
- Loop guard firing unexpectedly
- Background threads dying silently
- State file corruption

---

## Robot Tests (Future)

When the physical robot is connected:

- Run the same conversation tests
- Confirm NeoPixel colour matches eLo OS mode
- Confirm jaw servo responds to voice
- Confirm no separate state machine — robot reads blender_state.json, same as Desktop

---

## Test File Standards

```python
# tests/test_component_name.py

import pytest
from tools.component_name import function_name

def test_happy_path():
    result = function_name("normal input")
    assert result is not None
    assert "expected_field" in result

def test_empty_input():
    result = function_name("")
    assert result is None or result == ""

def test_does_not_raise():
    # Should not raise regardless of input
    function_name(None)
    function_name({})
    function_name(["unexpected", "type"])
```
