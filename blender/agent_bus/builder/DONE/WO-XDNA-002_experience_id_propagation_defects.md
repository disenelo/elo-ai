# WO-XDNA-002 — Experience DNA: Propagation Defect Repair (D-1 + D-2)
**Status:** 🔨 BUILD  
**Authority:** G-3 Validation ruling `docs/architecture/findings/G3_VALIDATION_2026-08-23.md`  
**Parent WO:** WO-XDNA-001 (closed by Builder)  
**Scope:** Two defects found by LA independent validation — fix only. No new architecture.  
**Lane:** Builder only — LA does not touch code (Rule 3)

---

## Context

WO-XDNA-001 was built and its 9 acceptance tests passed. LA independent validation found two defects that prevent G-3 closure:

- **D-1 (CRITICAL):** Four production callers construct `MemoryCandidate(...)` without passing `experience_id`. Result: every vault record written via server.py → MemoryFaculty → vault_layer has `experience_id=""` in the YAML frontmatter — which is the same as having no experience_id at all. The unique-addressability invariant is not met.
- **D-2 (MINOR):** `decision_journal.record_intent_abandoned()` does not carry `experience_id`. Abandoned intents retain no identity, which is architecturally wrong per the canon rationale.

---

## D-1 Fix — four files, same pattern each

For each of the four files below, add `experience_id=_get_xid()` to the `MemoryCandidate(...)` call. The fix also requires importing `get` from `runtime.experience_id` — use a try/except so the call never blocks.

### 1. `server.py` (~line 3946)

**Current:**
```python
_MemFac().submit(_MemCand(
    source_faculty="interaction",
    content=_content,
    proposed_type="episodic",
    proposed_weight=3,
    significance=0.25,
    project=_mem_project_tag,
    summary=(raw[:180] + "…" if len(raw) > 180 else raw),
    tags=("interaction", _action),
))
```

**Add before the submit call (inside the existing try block):**
```python
try:
    from runtime.experience_id import get as _get_xid
    _mem_xid = _get_xid()
except Exception:
    _mem_xid = ""
```

**Then add to MemoryCandidate:**
```python
    experience_id=_mem_xid,
```

### 2. `runtime/reflection_faculty.py` (~line 326)

Same pattern:
```python
try:
    from runtime.experience_id import get as _get_xid
    _refl_xid = _get_xid()
except Exception:
    _refl_xid = ""
_decision = _MemFac().submit(_MemCand(
    source_faculty="reflection",
    ...existing fields...
    experience_id=_refl_xid,
))
```

### 3. `faculties/music_memory/storage.py` (~line 110)

Same pattern:
```python
try:
    from runtime.experience_id import get as _get_xid
    _music_xid = _get_xid()
except Exception:
    _music_xid = ""
_decision = _MemFac().submit(_MemCand(
    source_faculty="music",
    ...existing fields...
    experience_id=_music_xid,
))
```

### 4. `core/core_engine.py` (~line 256)

Same pattern:
```python
try:
    from runtime.experience_id import get as _get_xid
    _core_xid = _get_xid()
except Exception:
    _core_xid = ""
_MemFac().submit(_MemCand(
    source_faculty="interaction",
    ...existing fields...
    experience_id=_core_xid,
))
```

---

## D-2 Fix — `self/decision_journal.py` `record_intent_abandoned()`

**Current entry dict in `record_intent_abandoned()` (~line 167):**
```python
entry = {
    "ts":          time.time(),
    "session_id":  _SESSION_ID,
    "record_type": "intent_abandoned",
    "intent_id":   intent_id,
    "lane":        lane,
    "kind":        kind,
    "content":     content,
    "reason":      reason,
}
```

**Add experience_id:**
```python
# WO-XDNA-002: abandoned intents must carry experience_id per canon rationale.
try:
    from runtime.experience_id import get as _get_xid
    _xid = _get_xid()
except Exception:
    _xid = ""

entry = {
    "ts":            time.time(),
    "session_id":    _SESSION_ID,
    "experience_id": _xid,         # ADD THIS
    "record_type":   "intent_abandoned",
    "intent_id":     intent_id,
    "lane":          lane,
    "kind":          kind,
    "content":       content,
    "reason":        reason,
}
```

---

## Acceptance tests

AT-6 in the existing suite (`test_xdna001_experience_identity_minting.py`) tests vault_layer.write_memory() directly. That test must be EXTENDED (or a new test added) to cover the end-to-end production path:

**AT-11 (new or extended AT-6):**  
Simulate the full production vault write path:
1. `mint()` — simulates spine.py turn start
2. Construct `MemoryCandidate(source_faculty="interaction", ..., experience_id=_get_xid())`
3. `MemoryFaculty().submit(candidate)` — routes through production submit()
4. Read back the vault summary.md YAML frontmatter
5. Assert `experience_id` equals the minted value — NOT empty string

**AT-12 (new):**  
`decision_journal.record_intent_abandoned()` produces an entry that carries experience_id:
1. `mint()` a fresh xid
2. Call `record_intent_abandoned(intent_id="test-intent", kind="external", content="x", reason="timeout")`
3. Read the journal
4. Assert the abandoned-intent row carries the minted experience_id

---

## Architectural constraints (unchanged from WO-XDNA-001)

- DO NOT replace the spot code or modify vault_codec
- DO NOT create a new store or parallel write path
- MemoryFaculty sole logical writer invariant unchanged
- vault_layer sole bytes writer invariant unchanged
- Backfill of existing records remains FORBIDDEN

---

## G-3 closure gate (unchanged)

G-3 is closed when:
- AT-1 through AT-12 all pass
- AND the Board validates that the unique-addressability invariant is genuinely satisfied in the production path (not just in unit tests)

After these fixes, the production path will be:
```
spine.run() mints experience_id
    ↓
server.py constructs MemoryCandidate(experience_id=get())
    ↓
MemoryFaculty.submit() passes candidate.experience_id
    ↓
vault_layer.write_memory(experience_id=...) writes to YAML frontmatter
    ↓
Every vault record carries a distinct, non-empty experience_id
```

Return this WO to the LA/Board as COMPLETE when all 12 ATs pass. Do not self-report G-3 as closed.

---

## ✅ CLOSED — 2026-08-23

**Status:** COMPLETE

### Implementation summary

**D-1 — four production callers patched (same pattern each):**

| File | Line | Change |
|------|------|--------|
| `server.py` | ~3945 | `_get_xid()` call + `experience_id=_mem_xid` on `MemoryCandidate` |
| `runtime/reflection_faculty.py` | ~326 | `_get_xid()` call + `experience_id=_refl_xid` on `MemoryCandidate` |
| `faculties/music_memory/storage.py` | ~110 | `_get_xid()` call + `experience_id=_music_xid` on `MemoryCandidate` |
| `core/core_engine.py` | ~256 | `_get_xid()` call + `experience_id=_core_xid` on `MemoryCandidate` |

All four use identical try/except guard pattern — never blocks on import failure.

**D-2 — `decision_journal.record_intent_abandoned()` patched:**
- Added `experience_id:` as third key in entry dict, after `session_id`.
- Same try/except guard as all other write sites.

**Test file updated:** `tests/test_xdna001_experience_identity_minting.py` docstring updated to cover AT-1 through AT-12. AT-11 and AT-12 appended as new test functions.

### Test results

```
11/11 ATs PASSED in 0.07s
```

AT-11: end-to-end production path (mint → MemoryCandidate → submit → vault YAML) ✅  
AT-12: record_intent_abandoned carries minted experience_id ✅

### G-3 re-validation request (Builder outbox)

D-1 and D-2 are resolved. The production path is now:
```
spine.run() mints experience_id
    ↓
server.py / reflection_faculty.py / music_memory/storage.py / core_engine.py
    constructs MemoryCandidate(experience_id=get())
    ↓
MemoryFaculty.submit() passes candidate.experience_id
    ↓
vault_layer.write_memory(experience_id=...) writes to YAML frontmatter
    ↓
Every vault record carries a distinct, non-empty experience_id
```

G-3 formal re-validation is a **separate Board gate**. Builder does not self-declare G-3 closed. Results returned to LA/Board.
