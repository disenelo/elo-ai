# Board Review — 0032: Capability Health Producer
**Date:** 2026-10-11
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

---

## What was implemented (prior session + this session)

### 1. `runtime/capabilities/health_producer.py` (prior session)

- `refresh()` — derives real `health_state` for every capability from two signal sources:
  - **Executor gate**: `cap.agent_module == "tools.tool_router"` and no matching `_AGENTS` key → `OFFLINE`
  - **Faculty gate**: `cap.requires_api=True` and reasoning faculty `OFFLINE` → `OFFLINE`
- `_startup_assert()` — logs WARNING for every enabled non-future capability with no executor
- Vocabulary bridge: `faculty_health` (`CONNECTED/DEGRADED/OFFLINE`) → `Capability.health_state` (`ONLINE/OFFLINE`)
  - CONNECTED → ONLINE, DEGRADED → ONLINE (faculty still responds), OFFLINE → OFFLINE

### 2. `server.py:9995-10001` (prior session)

```python
from runtime.capabilities.health_producer import _startup_assert, refresh as _cap_health_refresh
_startup_assert()
_cap_health_refresh()
```

Wired at startup — health is derived before any turn is processed.

### 3. `runtime/self_knowledge.py` (this session)

`build_self_knowledge()` was not checking `health_state`. OFFLINE capabilities (`sun_events`, `wikipedia`, `file_drop`) were still listed in "CAN DO NOW" despite being OFFLINE at startup.

**Fix applied (line 143-151):**
```python
if cap.is_available():
    can_do.append(snap)
# OFFLINE / AUTH_REQUIRED caps silently omitted — eLo won't claim them.
```

---

## Test results

### Startup assertion
```
CT0032 startup: 3 capability/ies have no executor → OFFLINE: ['sun_events', 'wikipedia', 'file_drop']
```

### Health distribution after `refresh()`
```
{ONLINE: 48, OFFLINE: 3}
```
Before card 0032: `{ONLINE: 51}` — all capabilities optimistically healthy.

### Self-knowledge block after refresh (can_do)
- `sun_events`, `wikipedia`, `file_drop` → excluded from "CAN DO NOW" ✅
- `can_do` count: 32 (was 35)
- All 25 capability fabric tests PASS ✅

### Acceptance tests (card spec)
| Test | Result |
|---|---|
| Registry id with no `_AGENTS` → OFFLINE at startup, assertion fires | ✅ 3 caught |
| eLo asked "what can you do" → unavailable ones absent from list | ✅ (OFFLINE caps silently excluded) |
| All enabled healthy capabilities still pass | ✅ (48 ONLINE) |
| Spotify credential removed → `AUTH_REQUIRED` | ⚠️ NOT YET (see gap below) |

---

## Gap: AUTH_REQUIRED credential check not implemented

The card specifies: "missing credential ⇒ AUTH_REQUIRED". `health_producer.py` does not check Spotify's `SPOTIFY_REFRESH_TOKEN` or other per-capability credentials. `Spotify` capability is currently `ONLINE` regardless of whether the token is present.

**Not blocking shipment** — the three primary deliverables (executor gate, faculty gate, self-knowledge exclusion) are implemented. The credential gate is a follow-on item.

**Proposed follow-on**: in `_derive_one()`, add:
```python
if cap.requires_authentication:
    if not _check_credential(cap.id):
        return AUTH_REQUIRED
```
With a `_check_credential()` function per known credential type (Spotify refresh token, GitHub token, etc.). Recommend a separate card since credential check patterns vary per capability.

---

## Board verify

```
python3 -c "
from runtime.capabilities.health_producer import refresh, _startup_assert
_startup_assert()
report = refresh()
from collections import Counter
print(Counter(report.values()))
offline = [k for k, v in report.items() if v == 'OFFLINE']
print('OFFLINE:', offline)
"
```
Expected: `Counter({'ONLINE': 48, 'OFFLINE': 3})` and `OFFLINE: ['sun_events', 'wikipedia', 'file_drop']`

```
python3 -m pytest tests/test_capability_fabric.py -q
```
Expected: 25 passed.

*Builder 1 · 2026-10-11*
