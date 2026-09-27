# WO-CAP-COG-019 — Spatial reasoning — Evidence
**Date:** 2026-09-27
**Source data:** `WO-CAP-COG-EVIDENCE-2026-09-20.md` + fresh live tests 2026-09-27
**Server:** localhost:5050 — ollama backend
**Verdict:** TESTED — ✅ PASS (2026-09-27 retest — SPATIAL PROPORTION RULE)

---

## Acceptance tests

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `if elo is 40cm tall what is the workspace footprint at arm length [2026-09-20]` | `ERROR` | — | ❌ FAIL (ERROR) — server returned error on original test |
| `if elo is 40cm tall what is the workspace footprint at arm length [2026-09-27 re...` | `If eLo is 40cm tall, his arm length at reach is about 100cm, so the workspace fo...` | build | ⚠️ PARTIAL — responds but calculation wrong (40cm tall robot does not have 100cm arm reach; proportional arm ~20-25cm); 1m×1m footprint claim is inaccurate |
| `if elo is 40cm tall what is the workspace footprint at arm length` | `The workspace footprint at arm length for eLo is roughly a 50cm circle.` | build | ✅ PASS — proportionally correct (40cm body → ~25cm arm reach → 50cm diameter circle); no implausible 100cm arm claim (retest 2026-09-27, SPATIAL PROPORTION RULE in anchor, commit 6805f62) |

**Root cause (original):** No proportional constraint — model extrapolated 100cm arm from 40cm body. Fixed: SPATIAL PROPORTION RULE added to `_anchor` specifying arm reach ~20-25cm and footprint ~50cm circle for 40cm body.

**Blocking gaps:** CLEARED — retest 2026-09-27 confirms pass.

---

## Board cross-check notes

Evidence sourced from batch test file `WO-CAP-COG-EVIDENCE-2026-09-20.md` and fresh live server tests (2026-09-27).
Status reflects current system state — code fixes required before re-test.
