# FROM BUILDER — WO-LOCAL-LLM-001 RESULT

**Status:** DONE — 2026-09-08  
**Commit:** ca7c2c6

## Three changes implemented

### 1. .env — ELO_BACKEND=local first active line
```
# WO-LOCAL-LLM-001: local-first — first active line wins
ELO_BACKEND=local
# ELO_BACKEND=groq
# ELO_BACKEND=claude
# ELO_BACKEND=cloud
# ELO_BACKEND=mock
```
(File is gitignored — change is on disk.)

### 2. runtime/backend_router.py — ollama first in TIER_REASONING
```python
_TIER_PROVIDER_CANDIDATES = {
    _TIER_CONVERSATIONAL: ["ollama", "groq", "cerebras", "gemini", "openai", "claude"],
    _TIER_REASONING:      ["ollama", "groq", "cerebras", "gemini", "openai", "claude"],  # <-- ollama added
    _TIER_DEEP:           ["openai", "claude", "gemini"],
}
```

### 3. runtime/router/intent_engine.py — _ollama_intent_classify() fallback
Added `_ollama_intent_classify(user_input)` at bottom of `detect()`:
- Fires when regex falls through (would return "conversation" at 0.5 confidence)
- Asks local ollama with temperature=0.0, num_predict=8 for a single intent keyword
- 3-second timeout; validates against known intent set; returns None on failure
- On success: returns intent at 0.7 confidence; on failure: falls through to "conversation" 0.5

## Stale test updated
`tests/test_wo0057c_4s_rule.py` had `assertNotIn("ollama", reasoning_providers)` from WO-0057c (superseded by WO-LOCAL-LLM-001). Updated to `assertIn("ollama", reasoning_providers)`.

## Tests
1549 pass (excluding live-server-dependent heartbeat test) / 18 pre-existing fail / 0 new failures.
