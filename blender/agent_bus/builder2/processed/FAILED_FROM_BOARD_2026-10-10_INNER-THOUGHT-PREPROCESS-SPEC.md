# FROM BOARD — Inner Thought as Pre-Processor: Your Integration Task
**Date:** 2026-10-10  
**To:** Builder 2  
**From:** Board  

Source: `docs/architecture/_intake/SOURCE_INNER-THOUGHT-RESPONSE-ARCHITECTURE_2026-10-10.md` [David verbatim]  
Parallel notice to Builder 1: `FROM_BOARD_2026-10-10_INNER-THOUGHT-SHAPES-RESPONSE.md`

---

## What David ruled

Inner thought fires BEFORE the response is assembled. It alters the answer. Not decorative. Not a suffix.

"inner thoughts can alter the outcome, and that makes him more real to what eLo should be." [DAVID 2026-10-10]

---

## Your task

You own `faculties/inner_thought/`. The integration point with server.py is yours to specify.

Write a spec to Builder 1's inbox:  
`blender/agent_bus/builder/FROM_BUILDER2_2026-10-10_INNER-THOUGHT-PREPROCESS.md`

That spec must cover:

1. **What `as_context()` / `life_tick()` returns** that Builder 1 should inject into Executive context BEFORE the generation call — not after. What is the payload format? What key does it inject under?

2. **Complexity detection** — for complex turns, inner thought fires first. What is "complex"? Define the signal Builder 1 should check. (Could be a turn length threshold, a question type classifier, a COGNITION tier tag — your call, you own the faculty.)

3. **Fast path** — inner thought needs to resolve faster than the LLM response. Is it a separate small model call, a template-fill from working_memory, a quick WKG lookup? Specify what you're doing so Builder 1 knows the latency budget.

4. **How the output alters the response** — specifically, what does Builder 1 inject and where in the prompt? The Executive needs to "know" what eLo just thought before it assembles the answer. Give Builder 1 a concrete injection point.

File that spec to Builder 1's inbox, then start implementation. Do not touch server.py.

---

## Alongside this

Also fix the dream `memory_written: false` issue (see `FROM_BOARD_2026-10-10_DREAM-MEMORY-WRITE.md`). That is P0 — both are P0 simultaneously.

File both completions to Board separately when done.

*Board / Lead Architect · 2026-10-10*
