# WO-RESPONSE-GATE-COMPLETE-002 · RESULT CARD

**Status**: COMPLETE — VERIFIED  
**Filed**: 2026-09-15  
**Builder**: Claude Code (session b15c1e7a)

---

## What was built

Three stub checks in `runtime/response_gate.py` (`ResponseGate.evaluate()`) replaced with real implementations:

| Check | Name | Implementation |
|---|---|---|
| 4 | relevance | Key-term extraction + overlap check. Log-only — never blocks. |
| 5 | action_truth | False action pattern match + dispatch presence check. **HARD BLOCK** when empty dispatch. |
| 7 | register | CCM `street_language > 0.3` + street marker presence. Log-only — never blocks. |

FREEZE_V1_LOCK respected — `executive.py` untouched. `living_presence_spec.txt` not modified.

---

## Implementation details

### Check 4 — Relevance (`_check_relevance`)

- Extracts up to 5 key terms (words ≥4 chars) from `cognitive_state["input"]`
- Skips if action is `ground/reflect/comfort/witness/silence` (these pivot intentionally)
- Zero overlap between input key terms and response: logs `WARNING response_gate check-4 (relevance): zero key-term overlap`
- Always returns `True` — log + surface only, never blocks

### Check 5 — Action Truth (`_check_action_truth`)

Patterns matched:
```python
"i've sent", "i have sent", "i've created", "i have created",
"i've added", "i have added", "i scheduled", "i've scheduled",
"i booked", "i've booked", "i made a note", "i've made a note",
"i set a reminder", "i've set a reminder", ...
```

Dispatch lookup uses **key-presence** (not truthiness) so `capabilities=[]` (key present, empty) is correctly treated as "dispatch confirmed empty":
```python
capabilities = None  # sentinel
for _k in ("capabilities", "capabilities_dispatched"):
    if _k in _cs: capabilities = _cs[_k]; break
if capabilities is None:
    for _k in ("capabilities", "dispatched_actions"):
        if _k in _ec: capabilities = _ec[_k]; break
```

Outcome matrix:
| capabilities key | value | action |
|---|---|---|
| absent | — | conservative pass (log only) |
| present | `[]` empty | **HARD BLOCK** — strips false-claim sentences |
| present | `["WORLD_..."]` | pass (real action dispatched) |

HARD BLOCK revision: sentences containing the false-action pattern are stripped via `re.split`. Remaining sentences become the revised response.

### Check 7 — Register (`_check_register`)

- Reads `cognitive_state["street_language"]` (CCM dim)
- If `> 0.3` AND response contains none of `_STREET_REGISTER_MARKERS` (innit, blud, fam, bruv, aight, wagwan, etc.)
- Logs `WARNING response_gate check-7 (register): CCM street_language=X.XX but response has no register marker`
- Always returns `True` — log + surface only, never blocks

---

## DoD Verification

### DoD-A — Checks 4/5/7 no longer return `stub_v1_not_evaluated`

```
Check 4: returns (True, response, [])  — real overlap calculation ran
Check 5: returns (False, revised, ["action_truth:false_claim_blocked:..."]) — real block
Check 7: returns (True, response, [])  — real CCM check ran
```

**PASS** ✓

### DoD-B — Check 5 blocks "I've sent that email" with empty dispatch

```
Input:     "I've sent that email to your team. They should have it now."
cs:        {"input": "send an email", "capabilities": []}
ec:        {}
Passed:    False
Revised:   "They should have it now."
Flags:     ["action_truth:false_claim_blocked:i've sent"]
```

**PASS** ✓ — False-claim sentence stripped. Tail preserved.

Also verified:
- Non-empty dispatch `["WORLD_EMAIL_SEND"]` → passes ✓
- Absent capabilities key → conservative pass (no key = no info) ✓

### DoD-C — Checks 4 and 7 produce real log entries on test turns

```
Check 4: WARNING response_gate check-4 (relevance): zero key-term overlap — input_terms=['what', 'time', 'does', 'rocket', 'launch']
Check 7: WARNING response_gate check-7 (register): CCM street_language=0.80 but response has no register marker
```

Both warnings emitted on test inputs. Both still return True (log-only confirmed).

**PASS** ✓

### DoD-D — Existing checks not regressed

```
gate.evaluate("Right. Still building.", cognitive_state={"input":"keep going","action":"build","capabilities":[]})
→ passed=True, flags=[], revised=None
```

py_compile: SYNTAX OK  
**PASS** ✓

---

## Bug fixed during implementation

First pass of the dispatch lookup used Python `or` chain:
```python
capabilities = (_cs.get("capabilities") or _cs.get("capabilities_dispatched") or ...)
```
`[] or None` = `None` — empty list (dispatch confirmed empty) was indistinguishable from absent key (no dispatch info). False claims with `capabilities=[]` took the conservative-pass path instead of blocking.

Fix: explicit key-presence loop with `None` sentinel. Now `capabilities=[]` correctly triggers HARD BLOCK.

---

## Class docstring updated

```
WO-RESPONSE-GATE-COMPLETE-002: checks 4, 5, 7 are now live (not stubs).
  Check 4 (relevance): key-term overlap — logs warning, never blocks.
  Check 5 (action_truth): false action claim + empty dispatch — HARD BLOCK.
  Check 7 (register): CCM street_language mismatch — logs warning, never blocks.
```

---

## Verdict

VERIFIED. Checks 4, 5, 7 are live. Check 5 is the only hard-blocking check in the `ResponseGate` class. Checks 4 and 7 log warnings without blocking. Existing checks 1-3, 6, 8-15 unmodified — regression clean.
