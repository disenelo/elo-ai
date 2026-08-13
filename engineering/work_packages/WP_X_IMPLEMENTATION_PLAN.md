# WP_X — Behaviour Consistency Implementation Plan

**Status:** READY FOR REVIEW
**Gap Analysis:** `WP_X_GAP_ANALYSIS.md`
**Proof document:** `engineering/proofs/09_behaviour_consistency_proof.md`

---

## Scope

Two changes in `runtime/backend_router.py`:
1. Word count enforcement for VOICE RULE
2. Multi-turn audit logging for MULTI-TURN RULE

GAP 1 (terminal _av_note) is handled by WP-I Step 1 — no separate action here.

---

## Step 1 — Add word count enforcement to normalise()

**File:** `runtime/backend_router.py`

Find the `normalise()` function. After the existing sentence-truncation logic, add word count check:

```python
def _truncate_to_word_limit(text: str, max_words: int = 38) -> str:
    """Truncate text to sentence boundary at or before max_words."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    result = []
    word_count = 0
    for sentence in sentences:
        words = sentence.split()
        if word_count + len(words) > max_words:
            break
        result.append(sentence)
        word_count += len(words)
    return " ".join(result) if result else sentences[0]  # never return empty


def normalise(text: str, max_sentences: int = 4) -> str:
    # ... existing sentence truncation logic ...

    # VOICE RULE enforcement (15–30 words target; 38-word hard cap with margin)
    word_count = len(text.split())
    if word_count > 38:
        text = _truncate_to_word_limit(text, max_words=38)

    return text
```

**Rationale for 38-word cap:** The spec says 30 words. A 25% margin (38 words) avoids aggressively cutting responses that are slightly over but still within one natural breath. Responses over 38 words are reliably violating the intent.

---

## Step 2 — Add multi-turn audit logging

**File:** `runtime/backend_router.py`

Add audit log function and call it in `normalise()`:

```python
import json as _json
import time as _time
import os as _os

_BEHAVIOUR_LOG = _os.path.join(_os.path.dirname(__file__), "..", "..", "logs", "behaviour_audit.jsonl")

def _log_behaviour_audit(event: str, response: str) -> None:
    """Append a behaviour audit event to logs/behaviour_audit.jsonl."""
    try:
        entry = {"ts": round(_time.time(), 3), "event": event, "response_preview": response[:120]}
        with open(_BEHAVIOUR_LOG, "a", encoding="utf-8") as f:
            f.write(_json.dumps(entry) + "\n")
    except Exception:
        pass


def normalise(text: str, max_sentences: int = 4) -> str:
    # ... existing logic + VOICE RULE word count (Step 1) ...

    # MULTI-TURN RULE audit (one question per turn)
    question_count = sum(1 for s in re.split(r'(?<=[.!?])\s+', text) if s.strip().endswith("?"))
    if question_count > 1:
        _log_behaviour_audit("multi_question_detected", text)

    return text
```

**No truncation** — only logging. Auto-removing questions is too risky (could strip intentional clarification). Audit log surface allows review before enforcement is tightened.

---

## Step 3 — Regression check

- Trigger a response that is longer than 38 words; confirm it is truncated to sentence boundary
- Trigger a response with two questions; confirm `logs/behaviour_audit.jsonl` gets an entry
- Confirm short responses (under 38 words) are not affected
- Confirm single-question responses do not trigger audit

---

## What does NOT change

- `runtime/executive.py` — FREEZE_V1_LOCK
- `prompts/` — FREEZE_V1_LOCK
- The 14 FORBIDDEN rules (already complete)
- Max sentences enforcement (preserved alongside word count)
- Any LLM routing, spine logic, or faculty code

---

## Implementation order

```
Step 1 — Add _truncate_to_word_limit() + word count check in normalise() [~20 lines]
    ↓
Step 2 — Add _log_behaviour_audit() + multi-question detection in normalise() [~15 lines]
    ↓
Step 3 — Regression test
    ↓
WP_X DONE (GAP 1 handled by WP-I)
```
