# WO-TIER-FIX-001 — Dead-Ollama Tier Fix Result

**Builder 1 · 2026-10-08**
**Commit: a26eedc**

---

## What was fixed

David ruling: "fix the Tier system" / "silence is not acceptable when cloud is live."

Root cause: when `ELO_BACKEND=local` and action is NOT in `_INTENT_PROVIDER_PREFERENCE`,
the intent-first router (IFR) never fired, so `_get_boot_health()` was never called.
The `mode == "local"` branch then called `_ollama_available()` fresh → 2-second HTTP probe
on a dead Ollama server every single turn. On actions in the IFR table this was already fixed
(commit eac097f); this commit covers ALL other actions.

Additionally: when Ollama was dead and mode was "local", the system returned mock (silent).
David explicitly said this is wrong — cloud is live, eLo should respond.

---

## Three changes to runtime/backend_router.py

**1. Boot health populated unconditionally at route() entry**
```python
# After mode is resolved:
_boot_health = _get_boot_health()
```
This primes the 30s Ollama TTL cache before any branch runs, regardless of action type.

**2. mode == "local" uses cached health — no re-probe**
```python
if _boot_health.get("ollama", False):   # was: if _ollama_available():
```

**3. mode == "local" + dead Ollama → degrade to cloud, not mock**
```python
for _fallback_p in ("groq", "cerebras", "gemini", "openai", "claude"):
    if not _boot_health.get(_fallback_p):
        continue
    _r = _ifr_call(system_prompt, user_input, _fallback_p, ...)
    if _r:
        return _r
return _mock_fallback(user_input), "mock"
```

**4. IFR no longer calls _get_boot_health() again**
```python
_health = _boot_health  # already populated above — no re-probe
```

---

## Test status

- 12/12 directly related tests pass (bypass_journal count, causal chain acceptance)
- 738 other tests pass
- 2 pre-existing failures NOT caused by this commit:
  - `test_xi_ad2_parity_proven` — sentinel gate, designed to stay red until Unity routes proven
  - `test_5_executive_py_byte_identical` — stale SHA1 hash from David's authorized commit 02d3a55
    (_REFLECT_PHRASES added). Hash needs advancing: `9f55186da3386234b065ccb1b0efeb98afa56d2f`.
    Auto mode classifier blocked Builder 1 from updating this test — David must advance it manually.

---

## Board action required

1. **Close WO-TIER-FIX-001** (commit a26eedc — tier fix complete)
2. **executive.py hash test** — David: run `python -m pytest tests/test_d3_lesson_reaches_executive.py` and update `_EXECUTIVE_FROZEN_SHA1` in that test to `9f55186da3386234b065ccb1b0efeb98afa56d2f` (authorized — your own commit 02d3a55).
3. **Live verification** — David says "What time is it" to eLo. Expected: response in under 3 seconds, answered by groq or cerebras (not mock). Log should show `WO-TIER-FIX-001: local-dead fallback answered by groq`.
