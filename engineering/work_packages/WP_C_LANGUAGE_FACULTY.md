# WP_C — Language Faculty Audit

**Status:** PENDING
**Priority:** HIGH
**Depends On:** WP_B (One Brain frozen)
**Architecture Reference:** `docs/architecture/02_language_faculty.md`

---

## Purpose

Audit, validate, and freeze the Language Faculty. The Language Faculty is eLo's primary input processor — it classifies meaning, detects register, and routes intent. Errors here cascade through every subsequent faculty.

---

## Objective

At the end of WP_C:
- The Language Faculty's classification accuracy is measured and documented
- Register detection (SOUTH_LDN_MODE, PATOIS_MODE, HYBRID_MODE) is validated against real inputs
- Intent detection false positives are identified and resolved (news/tool routing)
- The Language Faculty is frozen

---

## Existing Architecture Review Required

**Files to audit:**

| File | Role |
|---|---|
| `runtime/router/intent_engine.py` | Intent classification patterns |
| `runtime/router/typo_engine.py` | Typo correction before classification |
| `runtime/router/pipeline.py` | Pipeline orchestration |
| `runtime/router/agent_router.py` | Agent selection from intent |
| `tools/tool_router.py` | Tool-side intent map (duplicated — risk) |
| `docs/architecture/02_language_faculty.md` | Architecture specification |

**Known issues to investigate:**

1. **Dual intent maps** — `intent_engine.py` and `tool_router.py` both define intent patterns. This is duplication. Audit whether both are needed, what happens when they disagree, and which takes precedence.

2. **News false positives** — `\bnews\b` was firing on "don't want the news", "why are you telling me the news". Negation context was ignored. Mitigated in July 2026 session. Validate fix is holding.

3. **"Going on" pattern** — `\bwhat.*going\s+on\b` was mapped to news intent. Removed July 2026. Validate removal.

4. **Follow-up agent persistence** — `_last_agent` in `tool_router.py` persists across turns and can re-fire news/weather when user input is unrelated. Audit whether this is desirable.

5. **Search pattern breadth** — `r"\bwhat(?:'s| is)\s+(?:a\s|an\s|the\s)?(?!\d)"` is very broad. Audit false positive rate.

---

## Gap Analysis

1. Is there a single canonical intent classification system, or is classification split between `intent_engine.py` and `tool_router.py`?
2. Does register detection cover all of David's natural register (South London, patois blends)?
3. Are there inputs that consistently misclassify?
4. Does the Language Faculty ever decide anything, or does it only classify?

---

## Interaction Audit

| Interacts With | Nature | Status |
|---|---|---|
| Typo Engine | Pre-processes input before intent classification | Active |
| Pipeline | Receives intent classification, routes to agents | Active |
| Executive | Receives language output (intent, register, meaning) | Active |
| Tool Router | Parallel intent map — overlap risk | Needs audit |
| Attention Faculty | Receives meaning for attention scoring | Active |

---

## Validation Plan

1. Test 50 inputs against the intent classification. Record actual vs expected.
2. Test register detection: send 10 South London phrases, 5 patois phrases, 5 formal phrases.
3. Test negation handling: "don't want X", "stop X", "never X" for all tool-triggerable nouns.
4. Confirm `_last_agent` follow-up logic does not re-fire incorrectly.
5. One Brain check: Language Faculty classifies and reports — it never selects a response.

---

## Freeze Criteria

- [ ] All intent patterns audited and documented
- [ ] False positive rate < 5% on test inputs
- [ ] Negation handling validated
- [ ] Dual intent map situation resolved or documented
- [ ] Register detection validated with real inputs
- [ ] One Brain compliance confirmed
- [ ] Regression tests pass
