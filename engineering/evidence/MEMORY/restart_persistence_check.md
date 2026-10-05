# Vault-Write Pipeline — Restart Persistence Evidence
**Date:** 2026-10-05  
**Builder:** Builder 1  
**Status:** PASS — write → persist → survive module reload

---

## Pipeline audit

### Step 1 — Write path wired

`server.py:6330` calls `save_fact(key, value)` in the preference-detection block:
```python
from memory.fact_store import save_fact as _sf
_sf(_pref_key, f"David said: {_pref_text}")
```

### Step 2 — Load path wired

`server.py:4960` calls `facts_summary()` on every turn and injects as:
```
[DURABLE FACTS — always true, survive restart]
- <fact 1>
- <fact 2>
...
```
Block prepended to `_combined_vault` before system prompt assembly.

### Step 3 — Persistence confirmed (live 2026-10-05)

Canary fact written via `save_fact('vault_test_canary_2026_10_05', 'CANARY: Builder 1 vault-write live test 2026-10-05')`.

**Immediate read:** `'CANARY: Builder 1' in facts_summary()` → **PASS**

**Restart simulation** (fresh `importlib.reload(memory.fact_store)`):
`'CANARY: Builder 1' in facts_summary()` → **PASS**

Total facts in store after test: 11 (including canary)

---

## Current stored facts (sample)

```
- Studio / home location: Hackney Wick
- Born in Fulham (NOT Camberwell — corrected 2026-09-29)
- Grew up in Brixton, South London (NOT Camberwell)
- Date of birth: 18 January 1986, 01:17
- Email: dcharles@disenelo.com
- Founder / CEO / Chief Architect / L3 Authority — DISENELO
- Full name: David Charles. Address as 'David'
- Active projects: eLo AI OS, eLo-Planet, eLo Robot, DISENELO...
- CANARY: Builder 1 vault-write live test 2026-10-05
```

---

## Live end-to-end note

The write path fires when David makes preference statements matching `_PREF_RE`
(e.g. "my favourite X is Y", "I love X", "I use X"). The fact persists in
`memory/facts.json` and is injected into every subsequent session via `facts_summary()`.

A full live test (say → restart actual server → verify eLo references fact)
requires a human-driven session — structure is confirmed, live session
completes the evidence.

Builder 1 · 2026-10-05
