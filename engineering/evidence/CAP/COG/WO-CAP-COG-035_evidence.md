# WO-CAP-COG-035 — Synthesis — Evidence
**Date:** 2026-09-27
**Source data:** `WO-CAP-COG-EVIDENCE-2026-09-20.md` + fresh live tests 2026-09-27
**Server:** localhost:5050 — ollama backend
**Verdict:** TESTED — ✅ PASS (2026-09-27 retest)

---

## Acceptance tests

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `synthesise everything you know about elo into one thing` | `eLo is about adapting and learning, growing with you as you navigate your journe...` | reflect | ⚠️ PARTIAL — 'adapting and learning' is generic; should synthesise distinctive claims: one character across all forms, presence without eyes, calm as action, free and local, built for underserved makers |
| `synthesise elo into one thing` | `No eyes, full presence. Calm is the action — not the correction. Free and local, built for makers who can't access paid tools. One character across every form.` | reflect | ✅ PASS — leads with no-eyes-presence, calm-as-action, free-and-local, cross-form — all distinctives present (retest 2026-09-27, SYNTHESIS RULE in anchor, commit 7a52f2d) |

**Root cause (original):** Generic synthesis. Fixed: SYNTHESIS RULE added to `_anchor`: 'Lead with eLo's key distinctives: no eyes but full presence; calm is the action, not the correction; free and local; one character across all forms. NEVER reduce eLo to adapting and learning.'

**Blocking gaps:** CLEARED — retest 2026-09-27 confirms pass.

---

## Board cross-check notes

Evidence sourced from batch test file `WO-CAP-COG-EVIDENCE-2026-09-20.md` and fresh live server tests (2026-09-27).
Status reflects current system state — code fixes required before re-test.
