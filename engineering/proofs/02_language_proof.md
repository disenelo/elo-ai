# WP-C Language Faculty — Current Reality Review

**Status:** REVIEW COMPLETE
**Audit date:** 2026-07-12
**Score:** 80% aligned

---

## What Language Faculty owns

| Responsibility | File | Status |
|---|---|---|
| Input normalisation | `runtime/router/meaning_engine.py normalise()` | ✓ |
| Typo repair | `runtime/router/typo_engine.py repair()` | ✓ |
| Intent classification | `runtime/router/intent_engine.py detect()` | ✓ |
| Social signal detection | `meaning_engine.py` (embedded in normalise) | ✓ |
| Register detection | **MISSING — lives in relationship_faculty + executive** | 🔴 |
| Semantic extraction | `meaning_engine.py normalise()` | ✓ |

## No violations found

- Does not call LLM ✓
- Does not modify session state ✓
- Does not make routing decisions ✓
- Does not generate text ✓

## Gap: Register detection (MEDIUM)

`_detect_register()` exists in two places:
- `runtime/spine/relationship_faculty.py:96–106` — South London + Patois signals
- `runtime/executive.py:305–323` — same signals plus Cockney

Register is a **language interpretation** responsibility. It belongs in the Language Faculty and should be part of `_language_faculty()` output before downstream faculties ever run.

**Fix:** Move register detection into `_language_faculty()` (spine.py:29–70). Populate `result["register"]` before returning. Remove duplicate from executive.py and relationship_faculty.py.

## No drift found

No language logic discovered outside the Language Faculty. No other module reimplements normalise/repair/intent.
