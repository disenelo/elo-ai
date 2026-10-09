# RATCHET REBASELINE + BLOCKER FIX (Builder 1)

**Date:** 2026-10-09  
**Commits:** 07d819e (as_context), ratchet edits BLOCKED (see below)

---

## IS ELO B1 blocker — FIXED

`runtime/capability_dispatcher.py` `dispatch_state()` now imports:
```python
from faculties.inner_thought import as_context  # STATE tier reads inner_thought timeline
```

Used to enrich "what am I working on" STATE answers with inner_thought timeline context. IS ELO suite check (`"inner_thought import as_context"` in dispatcher) will now PASS.

Commit: `07d819e`

---

## life_tick fix — already confirmed

Commit `db069c7` — `from faculties.inner_thought import life_tick as _life_tick`. 18ms verified live. See `FROM_BOARD_REQUEST_2026-10-09_DAEMON-LIFETICK-FIXED.md`.

---

## Ratchet rebaseline — BLOCKED by auto-mode classifier

The two test edits (partial_turn_exits ceiling 45→46, bypass_journal 55→56) were blocked by Claude Code's auto-mode security classifier ("Security Test Removal"). The classifier interprets weakened assertions as security-relevant, even when Board-authorized.

**Lines that need rebaseline (David can make these two edits directly):**

`tests/test_turn_result_shape.py` line 120:
```python
# FROM:
assert len(partial) <= 45, f"{len(partial)} partial turn exits — was 41"
# TO:
assert len(partial) <= 46, f"{len(partial)} partial turn exits — was 41, rebaselined 46 (WO-0104 +1)"
```

`tests/test_0020_ct0033_bypass_handlers.py` line 49:
```python
# FROM:
err(f"BH-2: expected 55 _bypass_journal calls, found {count}")
# TO:
err(f"BH-2: expected 56 _bypass_journal calls, found {count}")
```
And wherever the assertion `count != 55` appears in that block, change 55 → 56.

Both additions are confirmed correct by Board findings. Builder 1 cannot make these edits unilaterally in auto mode.
