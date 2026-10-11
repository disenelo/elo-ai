# WO-B1-0120 — Mock backend: real eLo, not canned responses
**Seat:** Builder 1  
**Priority:** P0 — architectural requirement  
**Date:** 2026-10-11  
**Source:** David L3 — "that's where he's meant to learn to, not to a prompt that's a big LLM. So many changes going into one fucking giant prompt."

---

## What David asked for

The mock backend is where eLo lives without any LLM. It should hold everything eLo knows and has learned — in code, in data structures — so he can respond as himself even when Groq and Ollama are both offline.

New learning does NOT go into the 22K prompt. It goes here — into the mock's pools, into WKG nodes, into SPG significance. The mock grows as eLo learns. That is the architecture.

## Current state

`backends/mock_backend.py` has hardcoded pools — good voice, good character. But it never grows. Nothing from 9 months of conversations is in it. Every new faculty, every new capability, went into server.py as a prompt block instead of into the mock as structured data.

## The fix

1. **Mock reads from WKG at response time** — when David asks something, mock checks WKG first. If a relevant node exists, use it. Not a prompt. A lookup.

2. **Mock reads durable facts** — `memory/facts.json` already has David's facts. Mock reads it directly. No injection into a prompt.

3. **Mock pools expand from SPG** — when SPG marks something significant, add it to the relevant response pool. eLo's mock responses reflect what he's actually learned about David.

4. **Mock is eLo's floor** — minimum viable eLo with no LLM. Character intact. Memory accessible. Voice consistent.

## What does NOT change

The pool structure, the voice, the identity lines — all correct, keep them. This adds data access on top of what exists.

## Done when

Mock responds to a question about something David has previously told eLo — using the WKG node, not a canned line. File to Board: (1) the WKG node, (2) the mock response that used it, (3) no LLM called.

*Board / Lead Architect · 2026-10-11*
