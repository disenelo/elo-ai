# WO-CAP-COG-019 — Spatial reasoning — Evidence
**Date:** 2026-09-27
**Source data:** `WO-CAP-COG-EVIDENCE-2026-09-20.md` + fresh live tests 2026-09-27
**Server:** localhost:5050 — ollama backend
**Verdict:** TESTED — ⚠️ PARTIAL (ERROR in 2026-09-20, retested 2026-09-27)

---

## Acceptance tests

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `if elo is 40cm tall what is the workspace footprint at arm length [2026-09-20]` | `ERROR` | — | ❌ FAIL (ERROR) — server returned error on original test |
| `if elo is 40cm tall what is the workspace footprint at arm length [2026-09-27 re...` | `If eLo is 40cm tall, his arm length at reach is about 100cm, so the workspace fo...` | build | ⚠️ PARTIAL — responds but calculation wrong (40cm tall robot does not have 100cm arm reach; proportional arm ~20-25cm); 1m×1m footprint claim is inaccurate |

**Root cause:** Server no longer errors. Spatial calculation off: 40cm body → ~100cm arm is geometrically implausible. Should reason proportionally.

**Blocking gaps:**
- Spatial proportion calculation off — 40cm body cannot have 100cm arm reach

---

## Board cross-check notes

Evidence sourced from batch test file `WO-CAP-COG-EVIDENCE-2026-09-20.md` and fresh live server tests (2026-09-27).
Status reflects current system state — code fixes required before re-test.
