# FROM BUILDER — WO-SP31 Self-Initiation — DONE

**WO:** WO-SP31-SELF-INITIATION  
**Priority:** P1 · **Authority:** David L3, 2026-08-30  
**Date:** 2026-08-30  
**Status:** COMPLETE

---

## Result

**4/4 AT PASS** (core) + **13/13 PASS** (full SP31/SP32 suite)

```
✅ AT-1: significance 0.75 → SelfInitResult(allowed=True, tier='verbal', reason='attending+significant')
✅ AT-2: significance 0.0  → SelfInitResult(allowed=False, tier='ambient_only', reason='below_threshold')
✅ AT-3: is_enabled() = True — ELO_SELF_INITIATION=1 confirmed active
✅ AT-4: tests/test_sp31_sp32_self_initiation.py → 13/13 PASS
```

## What was done

1. `VERIFY FIRST` — confirmed all SP31/SP32 gate logic already implemented and passing
2. Confirmed `significance_faculty.py` + relationship context wired: `SELF_INIT_THRESHOLD = 0.72`, `EXCEPTIONAL_THRESHOLD = 0.90`
3. Confirmed low-significance (< 0.72) → `ambient_only` (no spine call)
4. Set `ELO_SELF_INITIATION=1` in `.env` per David L3 ruling (SOURCE_2026-08-30_DAVID_CA_architectural_locks_unlocks.md §4)

Note: `.env` is gitignored (contains secrets). The flag is live in the local file. No commit needed for this change.

## Previous state

Flag was absent from `.env` entirely. `is_enabled()` returned False. Self-initiation was silently blocked. Now active.

## Boundary holds

Self-initiation fires ONLY when:
- `ELO_SELF_INITIATION=1` is set ✓
- Significance threshold met (≥ 0.72 when attending, ≥ 0.90 when not attending) ✓
- Not in hard-quiet or dismiss-quiet window ✓

No random chatter. No low-significance noise. eLo waits when significance is not sufficient.

*Builder / Board — 2026-08-30*
