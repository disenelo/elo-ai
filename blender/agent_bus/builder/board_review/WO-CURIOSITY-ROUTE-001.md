# WO-CURIOSITY-ROUTE-001 — Wire curiosity_faculty.top_question() into server prompt

**WO:** WO-CURIOSITY-ROUTE-001 · **Seat:** builder · **Priority:** P2
**Reserved?** no

## Goal (one line)
eLo's top open curiosity question is injected into his system prompt each turn (when the topic matches), and once surfaced, that question is marked so the same one doesn't repeat every turn.

## Problem statement

`faculties/curiosity/curiosity_faculty.py` is fully implemented:
- `top_question()` at line 213 — returns highest-priority unsurfaced question from `self/state/open_questions.json`
- `curiosity_prompt_block()` at line 246 — renders a `[CURIOSITY — internal]` block ready for injection

**It is never called from server.py.**

The existing injection at `server.py:5058` calls `faculties.learning.faculty.curiosity_questions_prompt_block` — a different module that reads from `data/curiosity_questions.jsonl` (the learning faculty's write path). The proper curiosity faculty's question store (`self/state/open_questions.json`) is completely disconnected from the prompt pipeline.

Secondary problem: `top_question()` filters for `q.get("surfaced", False) == False` but nothing ever sets `surfaced=True`. Once a question enters `open_questions.json`, it would appear every turn indefinitely.

## Scope — exactly this, nothing more

1. **Add `mark_surfaced(q_text: str) -> None`** to `faculties/curiosity/curiosity_faculty.py`:
   - Loads `_QUESTIONS_PATH`, finds the question matching `q_text`, sets `"surfaced": True`, saves back.
   - Call it when the block is non-empty (i.e. the question was just injected).

2. **Add relevance gate to injection** — only inject when `top_question()["topic"]` has at least one token overlap with the current turn's raw input (case-insensitive). If no overlap, skip injection this turn (question waits for a relevant context).

3. **Add injection in server.py** at the existing faculty block section (~line 5058):
   ```python
   # WO-CURIOSITY-ROUTE-001: inject top open curiosity question when topic-relevant
   try:
       from faculties.curiosity.curiosity_faculty import (
           curiosity_prompt_block as _cfac_pb,
           mark_surfaced as _cfac_mark,
           top_question as _cfac_top,
       )
       _cfac_q = _cfac_top()
       if _cfac_q:
           _cfac_topic_tokens = set(_cfac_q.get("topic", "").lower().split())
           _cfac_input_tokens = set((raw or "").lower().split())
           if _cfac_topic_tokens & _cfac_input_tokens:
               _cfac_block = _cfac_pb()
               if _cfac_block:
                   system = system + "\n\n" + _cfac_block
                   _cfac_mark(_cfac_q.get("text", ""))
   except Exception as _cfac_err:
       _logging.warning("curiosity_faculty block failed (non-fatal): %s", _cfac_err)
   ```

4. **Keep the existing `server.py:5058` block** (`faculties.learning.faculty.curiosity_questions_prompt_block`) — it reads from a different source and is a separate system. Do not remove it.

## Files to touch
`faculties/curiosity/curiosity_faculty.py` (add `mark_surfaced()`) · `server.py` (~line 5058 area)

## Files NOT to touch
`runtime/executive.py` · `core/attention.py` · `prompts/living_presence_spec.txt` (FREEZE_V1_LOCK)

## Test (must pass WITHOUT David)

Write `tests/test_wo_curiosity_route_001.py`:

```python
"""WO-CURIOSITY-ROUTE-001: verify curiosity_faculty.top_question() injection + mark_surfaced."""
import json, tempfile, pathlib, pytest

def _write_questions(path, questions):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(questions))

def test_top_question_returns_unsurfaced():
    from faculties.curiosity import curiosity_faculty as cf
    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td) / "open_questions.json"
        _write_questions(p, [
            {"text": "Why does canvas fray at tight seams?", "topic": "canvas seams", "weight": 8, "surfaced": False},
            {"text": "Already shown", "topic": "other", "weight": 9, "surfaced": True},
        ])
        old = cf._QUESTIONS_PATH
        cf._QUESTIONS_PATH = p
        try:
            q = cf.top_question()
            assert q is not None
            assert q["text"] == "Why does canvas fray at tight seams?"
        finally:
            cf._QUESTIONS_PATH = old

def test_mark_surfaced_sets_flag():
    from faculties.curiosity import curiosity_faculty as cf
    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td) / "open_questions.json"
        _write_questions(p, [
            {"text": "Test question?", "topic": "test", "weight": 5, "surfaced": False},
        ])
        old = cf._QUESTIONS_PATH
        cf._QUESTIONS_PATH = p
        try:
            cf.mark_surfaced("Test question?")
            data = json.loads(p.read_text())
            assert data[0]["surfaced"] is True
        finally:
            cf._QUESTIONS_PATH = old

def test_top_question_none_when_all_surfaced():
    from faculties.curiosity import curiosity_faculty as cf
    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td) / "open_questions.json"
        _write_questions(p, [{"text": "Done?", "topic": "x", "weight": 5, "surfaced": True}])
        old = cf._QUESTIONS_PATH
        cf._QUESTIONS_PATH = p
        try:
            q = cf.top_question()
            assert q is None
        finally:
            cf._QUESTIONS_PATH = old

def test_curiosity_prompt_block_empty_when_no_questions():
    from faculties.curiosity import curiosity_faculty as cf
    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td) / "open_questions.json"
        _write_questions(p, [])
        old = cf._QUESTIONS_PATH
        cf._QUESTIONS_PATH = p
        try:
            block = cf.curiosity_prompt_block()
            assert block == ""
        finally:
            cf._QUESTIONS_PATH = old
```

Run: `python3 -m pytest tests/test_wo_curiosity_route_001.py -v`
Expected: 4 passed

## Done when
- `mark_surfaced()` added to `faculties/curiosity/curiosity_faculty.py`
- Injection wired in `server.py` with relevance gate
- 4 tests green
- committed

## Result (seat fills this in)
- commit: 64b024d
- test: 4/4 passed (test_wo_curiosity_route_001.py)
- notes: mark_surfaced() added to curiosity_faculty.py; relevance-gated injection added to server.py after learning.faculty block; existing learning.faculty curiosity block preserved unchanged.
