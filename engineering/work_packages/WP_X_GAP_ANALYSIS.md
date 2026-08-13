# WP_X — Behaviour Consistency Gap Analysis

**Status:** REVIEW COMPLETE — 2 HIGH gaps, 2 MEDIUM gaps
**Proof document:** `engineering/proofs/09_behaviour_consistency_proof.md`
**Next stage:** Implementation Plan

---

## What the architecture expects vs. what exists

| Architecture Expectation | Current Reality | Gap? |
|---|---|---|
| All 14 FORBIDDEN rules enforced | ✓ All 14 in prompt_builder.py | ✓ Match |
| VOICE RULE (15–30 words) enforced | ✗ Advisory only; sentence count enforced, not word count | 🔴 GAP |
| MULTI-TURN RULE (one question/turn) enforced | ✗ Advisory only | 🔴 GAP |
| Avatar self-reference prohibited in all embodiments | ✗ Terminal _av_note missing prohibition | 🔴 GAP |
| Character DNA identical across embodiments | ✓ Same spec file, both paths | ✓ Match |
| Max sentences enforced | ✓ `normalise()` in backend_router | ✓ Match |
| Ambient speech register appropriate | ✓ Neutral warmth by design | ✓ Match |
| Eyes absent from all expressions | ✓ No eye shapes anywhere | ✓ Match |
| DISENELO Presence named consistently | ✗ Terminal _av_note doesn't name it | ⚠️ |

---

## Gaps requiring implementation

### GAP 1 — Terminal _av_note missing avatar self-reference prohibition (🔴 HIGH)

**Shared with WP-I GAP 1.** Implementation tracked there. No separate action needed here — implementation of WP-I GAP 1 closes this.

---

### GAP 2 — VOICE RULE advisory only (🔴 MEDIUM)

**What architecture expects:** Responses target 15–30 words. One breath. Dense delivery over verbose explanation.

**What exists:** The 15–30 word target is a directive in the system prompt. `normalise()` enforces `max_sentences` but has no word-count validation. A 3-sentence, 80-word response passes without issue.

**Resolution:**
In `runtime/backend_router.py` `normalise()` function — after sentence truncation, add word count check:
```python
words = response.split()
if len(words) > 45:
    # Truncate to sentence boundary within 30 words
    response = _truncate_to_word_limit(response, max_words=38)
```

`_truncate_to_word_limit()`: split into sentences, add sentences until word count would exceed limit, return joined result.

**Implementation scope:** `runtime/backend_router.py` (~20 lines added to `normalise()`)

---

### GAP 3 — MULTI-TURN RULE advisory only (⚠️ MEDIUM)

**What architecture expects:** Ask one slot per turn. Confirm previous slot implicitly.

**What exists:** System prompt directive only. No post-generation check. LLM can ask two questions and nothing catches it.

**Resolution (lightweight):**
In `runtime/backend_router.py` `normalise()` — after sentence truncation, count sentence-ending question marks:
```python
question_count = response.count("?")
if question_count > 1:
    # Log a behaviour audit event (don't truncate — too risky to auto-fix)
    _log_behaviour_audit("multi_question_detected", response)
```

**Resolution (stronger):**
- If two questions detected, drop the second sentence that ends with `?`
- Risky if auto-applied — could remove intentional clarification
- Safer: log + optionally surface in diagnostics

**Recommendation:** Lightweight path first (log audit). Evaluate audit logs before enforcing truncation.

**Implementation scope:** `runtime/backend_router.py` (~10 lines), `logs/behaviour_audit.jsonl` (new log file)

---

## What already satisfies the architecture

- 14 FORBIDDEN rules: Complete
- Character DNA: Locked and consistent
- Max sentences: Enforced
- Ambient register: Correct by design
- Eyes absent: Correct
- South London register detection: Available both embodiments

---

## Implementation priority order

1. **GAP 1** — handled by WP-I GAP 1 (terminal _av_note fix)
2. **GAP 2** — VOICE RULE word count enforcement. Medium effort, high behaviour quality impact.
3. **GAP 3** — MULTI-TURN RULE audit logging. Low effort, low risk.

---

## Invariants unblocked

| Invariant | Status Now | Status After |
|---|---|---|
| Avatar identity consistent | ✗ Terminal weaker | ✓ (after WP-I GAP 1) |
| VOICE RULE enforced | ✗ Advisory | ✓ (after GAP 2) |
| MULTI-TURN RULE enforced | ✗ Advisory | ✓ (after GAP 3 — logging) |
