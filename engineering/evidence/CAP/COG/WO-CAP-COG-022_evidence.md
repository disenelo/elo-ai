# WO-CAP-COG-022 — Working knowledge graph (WKG) — Evidence
**Date:** 2026-09-27
**Source data:** `WO-CAP-COG-EVIDENCE-2026-09-20.md` + fresh live tests 2026-09-27
**Server:** localhost:5050 — ollama backend
**Verdict:** TESTED — ❌ FAIL

---

## Acceptance tests

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `what do you actually know about me` | `We exploring emotion and identity, and it's hard to put into words.` | answer | ❌ FAIL — non-answer; WKG should surface actual tracked info from session; 'we exploring emotion and identity' is deflection with broken grammar |

**Root cause:** WKG not surfacing tracked session information. 'What do you know about me' should return actual vault data (David, South London, DISENELO, projects). Instead deflects.

**Blocking gaps:**
- WKG data not surfaced on direct query
- Broken grammar: 'We exploring' (missing 'are')

---

## Board cross-check notes

Evidence sourced from batch test file `WO-CAP-COG-EVIDENCE-2026-09-20.md` and fresh live server tests (2026-09-27).
Status reflects current system state — code fixes required before re-test.
