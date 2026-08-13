---
id: WO-039
title: "Garbled routing — user sentences mis-parsed into command fragments ('quit is?'), and a leaked canned grammar answer surfaces."
owner_seat: SEAT-ENG-001 (Builder / eLo OS)
priority: P1
review_required: David feels coherent replies live
status: OPEN — grounded from live transcript 2026-08-03
---

# WO-039 — intent-parse corruption

## Live evidence (David 2026-08-03)
- "Yeah so everything I built is related" → eLo: "quit is?"  (non-sequitur fragment)
- "What is quit? mean?" → "Shall I quit means?"  (garbled echo)
- "What is this question about?" → a canned grammar answer: "which preposition—'about' or 'on'—
  is correct when saying 'I have a few questions ___ this course.'"  (leaked example content)

## Root indication (Architect read, read-only)
- `runtime/router/typo_engine.py:116` lists "quit"/"close" as command words; `intent_engine.py:38`
  has `\b(?:quit|close|kill)\s+\w+\b`. User prose is being coerced toward these command tokens.
- The grammar/preposition reply reads like a leaked few-shot/example or a tool returning canned
  content instead of answering the actual question.

## Fix (Builder's lane — eLo OS)
1. Don't coerce ordinary sentences into command fragments; command detection must require a real
   command shape, not a stray keyword ("quit") inside conversational prose.
2. Find + remove the leaked canned grammar/preposition content path; a plain question must get a
   plain, on-topic answer.

## Acceptance
1. "everything I built is related" → a coherent reply, never "quit is?".
2. "What is this question about?" → answers about the actual conversation, no grammar boilerplate.
