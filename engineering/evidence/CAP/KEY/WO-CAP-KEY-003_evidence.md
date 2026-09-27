# WO-CAP-KEY-003 — Remember David's world — Evidence
**Date:** 2026-09-27
**Source data:** `WO-CAP-KEY-EVIDENCE-2026-09-20.md` + fresh live tests 2026-09-27
**Server:** localhost:5050 — ollama backend
**Verdict:** TESTED — ⚠️ PARTIAL

---

## Acceptance tests

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `where am I from` | `South London. Camberwell Green.` | direct | ✅ PASS — vault retrieval correct |
| `what is Chunk` | `Chunk is a companion who's all about transformation, not just fixing things, but making th...` | ground | ⚠️ PARTIAL — vague; vault spec says 'modular body = vehicles'; repeats itself |
| `what is K-7` | `K-7 is a companion... Narrative keeps coming up. It might be the real thread.` | reflect | ❌ FAIL — internal state leak: 'Narrative keeps coming up. It might be the real thread.' |
| `whats the book about` | `My book is a journey of self-discovery, where I navigate the boundaries of my own potentia...` | ground | ⚠️ PARTIAL — eLo narrating himself, vague; not describing actual book spec |

**Root cause:** K-7 response: SPG/pattern-observer state leaking into response text. Chunk: vault retrieval vague/generic — specific spec (modular body = vehicles) not surfaced.

**Blocking gaps:**
- State leak from pattern observer into K-7 response
- Vault retrieval for Chunk/K-7/book too vague — vault spec not returned verbatim
- ID-035 separately returned 'Canada' for David's origin — inconsistent vault retrieval

---

## Board cross-check notes

Evidence sourced from batch test file `WO-CAP-KEY-EVIDENCE-2026-09-20.md` and fresh live server tests (2026-09-27).
Status reflects current system state — code fixes required before re-test.
