# WO-VAULT-EPISTEMIC-CLASS-ENFORCE-001 — Result Card

**Status**: COMPLETE — already implemented; verified 2026-10-06
**Lane**: `memory/vault_layer.py`
**Date**: 2026-10-06

## What was found

All three deliverables are implemented in `memory/vault_layer.py`:

1. **`epistemic_class` guard** (vault_layer.py:108): `vault_write(epistemic_class="verified")` without `source_ref` raises `ValueError`.
2. **`source_ref` requirement for "verified"**: documented in `write_memory()` docstring (lines 98–103).
3. **Epistemic class validation in test suite**: `tests/test_wo_vault_epistemic_class_enforce.py` (6 tests).

## Acceptance tests (verified)

| Test | Result |
|---|---|
| `test_verified_without_source_ref_raises` | PASS |
| `test_verified_with_source_ref_succeeds` | PASS |
| `test_inference_without_source_ref_succeeds` | PASS |
| `test_compress_session_still_works` | PASS |
| `test_memory_candidate_has_epistemic_class_field` | PASS |
| `test_memory_faculty_passes_epistemic_class_through` | PASS |

6/6 PASS.

## Implementation location

`memory/vault_layer.py:108`:
```python
if epistemic_class == "verified" and not source_ref:
    raise ValueError(
        "write_memory: epistemic_class='verified' requires a non-empty source_ref "
        "(file path, turn_id, or session id). Pass source_ref=... or use a less "
        "certain class like 'inference' or 'conversation'."
    )
```

No code changes made this session — implementation was already present.
