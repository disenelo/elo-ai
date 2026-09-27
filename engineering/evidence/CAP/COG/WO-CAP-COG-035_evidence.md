# WO-CAP-COG-035 — Synthesis — Evidence
**Date:** 2026-09-27
**Source data:** `WO-CAP-COG-EVIDENCE-2026-09-20.md` + fresh live tests 2026-09-27
**Server:** localhost:5050 — ollama backend
**Verdict:** TESTED — ⚠️ PARTIAL

---

## Acceptance tests

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `synthesise everything you know about elo into one thing` | `eLo is about adapting and learning, growing with you as you navigate your journe...` | reflect | ⚠️ PARTIAL — 'adapting and learning' is generic; should synthesise distinctive claims: one character across all forms, presence without eyes, calm as action, free and local, built for underserved makers |

**Root cause:** Synthesis too generic. Key eLo distinctives missing: no eyes but presence, calm as the action (not correction), free distribution, one character across all forms.

**Blocking gaps:**
- Synthesis misses key distinctives: no-eyes-presence, calm-as-action, free-and-local, cross-form consistency

---

## Board cross-check notes

Evidence sourced from batch test file `WO-CAP-COG-EVIDENCE-2026-09-20.md` and fresh live server tests (2026-09-27).
Status reflects current system state — code fixes required before re-test.
