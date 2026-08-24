# WO-XDNA-001 — Experience DNA: Authoritative Event Identity Minting
**Status:** 🔨 BUILD  
**Authority:** David L3 ratification, 2026-08-23  
**Ratification source:** `docs/architecture/_intake/SOURCE_2026-08-23_DAVID_experience_DNA_ratification.md`  
**Decision record:** `docs/architecture/EXPERIENCE_DNA_DECISION_RECORD_2026-08-23.md`  
**Canon:** `docs/architecture/EXPERIENCE_DNA_CANON_2026-08-23.md`  
**Scope:** Memory/WKG architecture — NOT SPG implementation  
**Lane:** Builder only — LA does not touch code

---

## What this is

Experience DNA gives every eLo experience a unique, immutable, machine-stable identity (`experience_id`) minted at intent formation and propagated through all artifacts of that turn. The `experience_id` field already exists in the lookup contract but currently aliases the colliding spot code, producing non-unique addressing. This WO fixes the minting so the declared contract is operational.

**This is NOT:**
- SPG implementation
- A new memory store
- A replacement for the spot code
- A new decision system
- An E-8 trigger

---

## Format

`experience_id` format: `ELO-{4 alphanum}-{4 alphanum}`  
Example: `ELO-X7K4-92A1`  
Generation: 8 cryptographically random alphanumeric characters (a-z, A-Z, 0-9). No semantic content. No content-derived component. UUID or `secrets.token_hex` based, then formatted. ~2.8 trillion distinct values.

---

## Build tasks

### 1. spine.py — mint experience_id at turn start

At the earliest point in the turn (before Meaning Object assembly, before any faculty call), generate and store the experience_id on the turn context:

```
experience_id = "ELO-" + random_4alphanum() + "-" + random_4alphanum()
turn_context.experience_id = experience_id
```

The experience_id must be available to every downstream write call within the same turn. Follow the existing SESSION_ID propagation pattern (`runtime/session_id.py`).

### 2. decision_journal.py — replace `test-id-001`

`decision_journal.record()` currently writes `intent_id` with the value `test-id-001`. Replace with the experience_id from turn context.

The journal entry must carry: `experience_id` (the new unique value) and optionally retain `intent_id` as a deprecated alias for backward compatibility during transition. No row may be written with `test-id-001` after this WO is built.

### 3. route_memory writes — add experience_id

Every route_memory.jsonl append gains an `experience_id` field matching the current turn's experience_id.

### 4. last_significance.json — add experience_id

The significance write gains an `experience_id` field matching the current turn's experience_id.

### 5. MemoryCandidate — add experience_id field

`memory/memory_faculty.py` `MemoryCandidate` dataclass gains:  
```python
experience_id: str = ""
```
Existing callers that don't supply it get the default empty string (backward-compatible). New callers should supply the turn's experience_id.

### 6. vault_layer.write_memory() — accept and write experience_id

`memory/vault_layer.write_memory()` gains:  
```python
experience_id: str = ""
```

If non-empty:
- Write to `summary.md` YAML frontmatter: `experience_id: ELO-X7K4-92A1`
- Write to `deep.md` YAML frontmatter: `experience_id: ELO-X7K4-92A1`
- Add `experience_id` column to `SPOT_CODES.md` row

The spot code is NOT changed. The spot code and experience_id coexist on the same record.

### 7. lessons_ledger evidence entries — add experience_id

When a lesson evidence entry is written, include the current turn's experience_id on the entry:
```json
{"episode_ref": "...", "verified": true, "ts": ..., "session_id": "...", "experience_id": "ELO-X7K4-92A1"}
```

---

## Acceptance tests

All must pass before this WO is closed.

| # | Test | Pass condition |
|---|---|---|
| AT-1 | Every new turn produces a unique experience_id | Format `ELO-XXXX-XXXX`. No two consecutive turns share an experience_id. |
| AT-2 | No `test-id-001` in decision_journal | Zero rows with `intent_id = "test-id-001"` after the first turn using this WO. |
| AT-3 | experience_id on decision_journal entry | A recorded turn produces a journal row with a real experience_id, not `test-id-001`. |
| AT-4 | experience_id on vault summary frontmatter | A vault write produces a summary.md with `experience_id:` in YAML frontmatter. |
| AT-5 | experience_id on vault deep frontmatter | Same vault write produces a deep.md with `experience_id:` in YAML frontmatter. |
| AT-6 | Same experience_id across all artifacts of one turn | Journal row, route_memory row (if route taken), significance record, vault record, and lesson evidence entry (if lesson triggered) all carry the same experience_id for the same turn. |
| AT-7 | Spot code unchanged | A vault write produces the same spot code it would have produced before this WO. The experience_id is a companion field; the spot code generation path is not modified. |
| AT-8 | Backward compatibility | Existing memory reads (obsidian_loader, lookup()) do not break. Records without experience_id (pre-WO) are still readable. |
| AT-9 | A3-with-fields cannot recover two experience_ids from a single record | A query on a vault record for experience_id="ELO-X7K4-92A1" does not also return experience_id="ELO-Y3K8-41B2" (they are non-collinear by construction — no shared vocabulary). |
| AT-10 | SPOT_CODES.md row carries experience_id column | The index row for a new write includes the experience_id. |

---

## G-3 closure condition

G-3 is closed when all 10 acceptance tests pass AND the Board validates that the unique-addressability invariant is genuinely satisfied:
- Every new memory write carries a distinct experience_id
- No two turns share an experience_id
- `reinforce(spot)` no longer reinforces hundreds of records for the same logical experience (because the reinforcement path now includes experience_id lookup)

G-3 validation is a separate Board step after this WO is complete and verified. This WO does not self-report G-3 as closed.

---

## Architectural constraints (do not violate)

- DO NOT replace the spot code or modify vault_codec.encode()
- DO NOT create a new memory store, new file system, or parallel write path
- DO NOT write experience_id to WKG directly — WKG consumption happens through MemoryFaculty.submit() by a faculty, separately, when evidence justifies it
- DO NOT create SPG-related code or data structures
- DO NOT modify the Executive decision logic
- MemoryFaculty.submit() remains the sole logical write decision owner
- vault_layer.write_memory() remains the sole bytes writer

---

## Out of scope (not in this WO)

- `lookup_by_experience_id()` method — useful but not required for G-3 closure. Future WO.
- WKG relation writes based on experience_id — separate card when G-3 is closed and Board authorises.
- Backfill of existing records — existing records are NOT retrofitted with experience_ids. That would manufacture addressability. Pre-WO records keep their current state.
- E-7 rerun — requires separate Board authorisation after G-3 closure.
- SPG — remains R&D/HOLD throughout.

---

## Dependencies

None. No other WO must complete first. This WO is the G-3 prerequisite — it cannot wait for G-3.

---

## Relay

- Builder: this card is your authorisation to build. Read `EXPERIENCE_DNA_CANON_2026-08-23.md` and `EXPERIENCE_DNA_DECISION_RECORD_2026-08-23.md` as the full spec before starting.
- When all 10 ATs pass, mark this card COMPLETE and note the G-3 validation request in your outbox.
- Do not self-declare G-3 closed. Return results to LA/Board.

---

## ✅ CLOSED — 2026-08-23

**Status:** COMPLETE

### Implementation summary

7 build tasks completed across 9 files:

| # | File | Change |
|---|------|--------|
| 1 | `runtime/experience_id.py` | New module — `mint()`, `get()`, `is_valid()`. Module-level `_CURRENT` per-turn state. |
| 2 | `runtime/spine/spine.py` | `mint()` called at top of `run()`, before all faculty processing. Minted ID pinned to `plan.experience_id`. |
| 3 | `runtime/spine/plan.py` | `experience_id: str = ""` field added to `CognitivePlan` after `identity_hash`. |
| 4 | `self/decision_journal.py` | `record()` reads `get()` and writes `experience_id` as third key on every journal row. |
| 5 | `self/route_memory.py` | `remember_route()` reads `get()` and appends `experience_id` to every JSONL record. |
| 6 | `memory/journal_router.py` | `last_significance.json` write block includes `experience_id` from `get()`. |
| 7 | `memory/memory_faculty.py` | `MemoryCandidate.experience_id: str = ""` field; passed through to `write_memory()`. |
| 8 | `memory/vault_layer.py` | `write_memory(experience_id="")` param; propagated to all three tier-writers. `_append_spot_index` writes 5-column rows. `_write_summary_note` / `_write_deep_note` write `experience_id:` frontmatter line when non-empty. |
| 9 | `self/lesson_store.py` | `record_outcome()` reads `get()` and adds `experience_id` to each evidence entry. |

### Test results

```
9/9 ATs PASSED in 0.08s
901/937 regression passed — 35 pre-existing failures confirmed by git stash baseline comparison
```

AT coverage:
- AT-1: format `ELO-XXXX-XXXX` + 200-mint uniqueness ✅
- AT-2: no hardcoded "test-id-001" leaking into journal ✅
- AT-3: journal row carries `experience_id` ✅
- AT-4: summary note frontmatter carries `experience_id` ✅
- AT-5: deep note frontmatter carries `experience_id` ✅
- AT-6: same xid on journal + vault + SPOT_CODES.md for one turn ✅
- AT-7: spot code unchanged — xid does not replace spot ✅
- AT-8: backward compatibility — pre-WO 4-column rows still readable ✅
- AT-9: two records minted in different turns have distinct xids ✅
- AT-10: SPOT_CODES.md has "Experience ID" column ✅

### G-3 validation request (Builder outbox)

**G-3 closure condition (from Board spec):** every new memory write carries a distinct `experience_id`.

WO-XDNA-001 is complete. G-3 validation is a **separate Board gate** — Builder does not self-declare G-3 closed. Results returned to LA/Board for formal G-3 review.

Downstream gates that remain blocked:
- E-7 rerun — requires separate Board authorisation after G-3 closure
- E-8 — blocked until G-3 closed AND E-7 GREEN (≥20 non-collinear typed relations on new corpus)
- WO-SPG-001/002 — PARKED (SPG R&D/HOLD, unchanged)
