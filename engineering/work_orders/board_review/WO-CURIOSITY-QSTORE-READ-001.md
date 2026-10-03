# WO-CURIOSITY-QSTORE-READ-001 — Curiosity Question Store Read Path

**Priority:** P1  
**Assigned:** Builder 1  
**Lane:** `data/curiosity_questions.jsonl` + `runtime/server.py`

## Gap

`data/curiosity_questions.jsonl` is written by `faculties/learning/faculty.py` line 214 (`_persist_curiosity_question`). No code reads it back. `grep` across `runtime/`, `server.py`, `spine.py` found zero read sites. Questions are persisted and lost — curiosity is not causal. The write side exists; the read + surface side does not.

## Fix

Build `curiosity_questions_prompt_block(turn_text)` in `faculties/learning/faculty.py` or a new helpers module:  
1. Read `data/curiosity_questions.jsonl`.  
2. Find questions with `status="open"` and `context_tags` matching `turn_text` keywords.  
3. Return oldest 1–2 matching questions as a prompt block: `"[CURIOSITY: You have an unanswered question about X. This turn may be relevant.]"`  
4. Wire into `server.py` alongside `expectation_tracker` block.  
5. On question answered: update `status="resolved"` in the jsonl.

## Acceptance

Question written in session A surfaces as a prompt block in session B when the turn contains matching context. Executive sees the question. eLo can refer to it without being re-prompted.
