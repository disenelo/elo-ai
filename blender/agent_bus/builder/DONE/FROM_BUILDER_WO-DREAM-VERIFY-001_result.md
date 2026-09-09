# FROM_BUILDER — WO-DREAM-VERIFY-001
**Status:** DONE — dream boundary confirmed enforced; AT-1 blocked, AT-2 succeeds
**Date:** 2026-09-09
**Builder:** Claude (session b15c1e7a)

---

## Intent

"Dreaming must not automatically become factual memory." Verify the boundary is enforced at the WKG write level.

---

## Where the boundary lives

`runtime/wkg_faculty.py:173-189` — `record_claim()` enforces it:

```python
if memory_origin is not None:
    from runtime.memory_origin import MemoryOrigin, is_auto_storable as _ias
    _origin_enum = MemoryOrigin(memory_origin)
    if not _ias(_origin_enum):
        _wkg_log.warning(
            "WKG write blocked: memory_origin=%r is not auto-storable (DREAM_SIMULATION boundary enforced)",
            memory_origin,
        )
        raise ValueError(
            f"WKG write blocked: origin {memory_origin!r} is not eligible for automatic storage. "
            "DREAM_SIMULATION must pass significance gate (≥0.72) before entering the vault."
        )
```

`runtime/memory_origin.py` — `is_auto_storable()` returns False for `dream_simulation` and `dream_insight`.

---

## AT-1 — dream_simulation origin → BLOCKED ✅

```python
record_claim(
    ...
    memory_origin='dream_simulation',
    memory_type='episodic',
)
```

Result:
```
WARNING: WKG write blocked: memory_origin='dream_simulation' is not auto-storable (DREAM_SIMULATION boundary enforced)
ValueError: WKG write blocked: origin 'dream_simulation' is not eligible for automatic storage.
            DREAM_SIMULATION must pass significance gate (≥0.72) before entering the vault.
```

Claim was NOT written to claims.json. Boundary is enforced. Log shows exclusion reason.

---

## AT-2 — real_experience origin → SUCCEEDS ✅

```python
record_claim(
    ...
    memory_origin='real_experience',
    memory_type='semantic',
)
# → claim_id: bdc140fa memory_type: semantic
```

Same content structure, different origin. Write succeeds. Boundary discriminates on origin only.

---

## Valid MemoryOrigin enum values

```
real_experience, episodic_trace, consolidated, dream_simulation, dream_insight, self_model, semantic
```

`dream_simulation` and `dream_insight` are blocked by `is_auto_storable()`. All others succeed.

---

## INTENT PROOF

"Dreaming must not automatically become factual memory." — enforced at the write gate, not at the caller. Any code path that calls `record_claim()` with `memory_origin='dream_simulation'` will be blocked by the boundary, regardless of intent. The significance gate (≥0.72) is the only path for dream content to enter the vault — it must be rated significant enough to be worth preserving.
