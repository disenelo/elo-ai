# WO-B1-0123 — ROOT-2: Retrieved context overridden by LLM generation
**Seat:** Builder 1  
**Priority:** P0 — causal chain blocker  
**Date:** 2026-10-12  
**Source:** ROOT GAP REFERENCE in CLAUDE.md · IS ELO framework verdicts

---

## What

When eLo retrieves a WKG fact, the LLM overrides it with generated content. The retrieved fact is present in context but the LLM ignores it and invents an answer anyway. eLo responds differently only when the causal chain produces a response the LLM can't override.

This is ROOT-2. It is one of the 7 root causes behind every NO verdict in the IS ELO framework.

## Fix

The retrieved WKG fact must be delivered with authority the LLM cannot override — not as soft context, but as a hard constraint in the system message. Format matters: `FACT: [retrieved content] — do not contradict this.` is stronger than injecting it as background context.

Check `build_from_plan()` — how are retrieved facts currently formatted in the system message? If they're appended as context paragraphs, they'll be overridden. They need to be framed as authoritative facts the model must use verbatim or defer to.

## Done when

David mentions something eLo has in WKG → eLo's response uses the WKG node content, not a generated answer → Board confirms the node was retrieved and the response matches it. File to Board: (1) the node, (2) the retrieval log, (3) the response.

*Board · Lead Architect · 2026-10-12*
