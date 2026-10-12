# WO-B2-0014 — Deferred threads store
**Seat:** Builder 2  
**Priority:** P1  
**Date:** 2026-10-12  
**Source:** IS ELO REMAINING-DOMAINS — INTENTIONS & CONTINUITY domain

---

## What

eLo drops unfinished curiosity. A conversation thread that eLo started and didn't finish — a question he asked David that never got answered, a topic he was exploring — disappears at session end. Nothing brings it back.

## What to build

1. `faculties/deferred_threads.json` store — unanswered questions, unfinished thoughts, deferred curiosity
2. Each entry: `thread_id`, `summary`, `reason` (why deferred), `created_at`, `session_id`, `status: active|resolved`
3. At session start: check deferred_threads against current context. Flag matches to CognitiveState.
4. eLo naturally picks up a deferred thread when relevant context appears

## Done when

eLo has a deferred thread (unresolved question from prior session). David provides relevant context. eLo retrieves the thread and continues it naturally without David re-initiating. File to Board: the deferred_threads.json entry, the retrieval, the live turn.

*Board · Lead Architect · 2026-10-12*
