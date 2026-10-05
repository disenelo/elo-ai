# WO-MEMORY-OFFLINE-SIGNAL-001 — Result Card
**Builder:** Builder 1  
**Date:** 2026-10-05  
**Status:** COMPLETE — previously shipped, result card written 2026-10-05

---

## Gap closed

Vault write failures were silent — eLo could promise to remember things it couldn't persist.

---

## What was implemented (already in HEAD)

**`memory/memory_faculty.py` `submit()`** — vault exception path:
```python
except Exception as exc:
    _mark_vault_offline(str(exc))
    return {"action": "drop", "spot": None, "reason": f"vault error: {exc}"}
```
- Calls `_mark_vault_offline()` which writes `data/vault_offline.json` with timestamp + reason
- Returns `reason="vault error: ..."` (not a silent drop)

**`server.py` ~line 5030** — WO-MEMORY-OFFLINE-SIGNAL-001 injection block:
```python
# WO-MEMORY-OFFLINE-SIGNAL-001: if vault write failed last turn, warn the model.
# Sentinel file expires after 5 minutes.
if _vol_os.path.exists(_vol_path):
    _vol_data = ...
    if time.time() - float(_vol_data.get("ts", 0)) < 300:
        system = system + (
            "\n\n[SYSTEM] Memory vault is temporarily offline — "
            "do NOT promise to remember anything this turn."
        )
```

---

## Mechanism

1. Vault write fails → `_mark_vault_offline(reason)` writes `data/vault_offline.json`
2. Next turn: server.py reads the sentinel; if `ts` < 5 minutes old → injects `[SYSTEM] Memory vault is temporarily offline` into the system prompt
3. eLo sees the signal and cannot promise to remember
4. Sentinel expires after 5 min — warning is per-failure, not permanent

---

## Acceptance (verified by code inspection)

✅ Vault exception path returns `action="drop", reason="vault_error: ..."` (not silent)  
✅ `_mark_vault_offline()` writes sentinel to `data/vault_offline.json`  
✅ server.py reads sentinel and injects memory-offline warning before LLM response  
✅ Warning expires after 5 minutes — transient, not permanent noise

Note: Live forced-failure test (mock) is the remaining live evidence step.
