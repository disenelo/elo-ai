# WP_F — Relationship Faculty Implementation Plan

**Status:** READY FOR REVIEW
**Gap Analysis:** `WP_F_GAP_ANALYSIS.md`
**Proof document:** `engineering/proofs/05_relationship_proof.md`

---

## Scope

Two changes:
1. Add time decay to rapport scoring in `relationship_faculty.py`
2. Add trust signal infrastructure — `significance_engine.py` writes signal, `relationship_faculty.py` reads it

---

## Step 1 — Add time decay to _score_rapport()

**File:** `runtime/spine/relationship_faculty.py`

Find `_score_rapport(session_state)`. Add time decay factor:

```python
import math as _math
from datetime import datetime as _dt

def _score_rapport(session_state: dict) -> float:
    base = (
        min(session_state.get("interaction_count", 0), 100) / 100 * 0.5
        + min(len(session_state.get("emotional_history", [])), 20) / 20 * 0.3
        + min(len(session_state.get("session_summaries", [])), 10) / 10 * 0.2
    )

    # Time decay: warmth cools with silence
    last_session_str = session_state.get("last_session_date", "")
    if last_session_str:
        try:
            last_dt = _dt.fromisoformat(last_session_str)
            days_silent = (_dt.utcnow() - last_dt).days
            decay = _math.exp(-0.005 * max(days_silent, 0))   # ~half after 140 days
            decay = max(decay, 0.8 if base > 0.1 else 1.0)    # cap decay at 0.8× for active users
            base *= decay
        except (ValueError, TypeError):
            pass  # no last_session_date — no decay

    # Trust signals from high-significance events
    trust_signals = min(len(session_state.get("trust_signals", [])), 3)
    base = min(base + trust_signals * 0.05, 1.0)

    return round(base, 3)
```

---

## Step 2 — Add trust signal infrastructure

**File 1:** `memory/state_manager.py`

In the session state schema / initialisation, add `trust_signals` list:
```python
# In default state dict or initialisation:
"trust_signals": [],   # list of {"ts": float, "category": str}
```

**File 2:** `memory/significance_engine.py`

After scoring, when score is high enough and category qualifies, append a trust signal:

```python
def route(user_input: str, elo_response: str, session_state: dict) -> dict:
    result = _score(user_input, elo_response)
    
    # Trust signal: deep emotional or creative moments accelerate rapport
    if result["score"] > 0.85 and result.get("category") in ("emotional", "creative"):
        signals = session_state.get("trust_signals", [])
        signals.append({"ts": _time.time(), "category": result["category"]})
        session_state["trust_signals"] = signals[-10:]  # keep last 10 only
    
    return result
```

**Note:** `significance_engine.py` already receives `session_state` in its call path (confirm this via read before implementing). If not, thread it through from the caller.

---

## Step 3 — Regression check

- Run with a fresh session (no last_session_date): confirm no decay applied
- Run with a last_session_date 7 days ago: confirm small decay
- Run with a last_session_date 200 days ago: confirm rapport reduced but not zeroed
- Trigger a high-significance emotional turn: confirm `trust_signals` entry added to session state
- Confirm rapport score increases after trust_signals are present

---

## What does NOT change

- `runtime/executive.py` — FREEZE_V1_LOCK
- Register detection (tracked in WP-C, not here)
- Any LLM routing or response generation
- The tier labels (new/acquaintance/familiar/trusted/close)

---

## Implementation order

```
Step 1 — Add time decay to _score_rapport() [~20 lines changed]
    ↓
Step 2a — Add trust_signals to state_manager.py schema [~3 lines]
Step 2b — Add trust signal append in significance_engine.py [~8 lines]
    ↓
Step 3 — Regression test
    ↓
WP_F DONE
```
