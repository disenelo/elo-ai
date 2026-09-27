# WO-CAP-COG-008 — Engineering reasoning — Evidence
**Date:** 2026-09-27
**Source data:** `WO-CAP-COG-EVIDENCE-2026-09-20.md` + fresh live tests 2026-09-27
**Server:** localhost:5050 — ollama backend
**Verdict:** TESTED — ⚠️ PARTIAL

---

## Acceptance tests

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `elos shoulder joint needs more torque than current motor provides what are real ...` | `Motor upgrade to 8Nm rated unit or add additional arm actuators for more torque.` | reflect | ⚠️ PARTIAL — correct directions (upgrade or add actuators) but too brief; doesn't explain trade-offs, Bowden cable option, or gear reduction |

**Root cause:** Correct direction, shallow depth. Missing key engineering options (Bowden cable redistribution, gear reduction) that are in the spec. Secondary issue: normalise max_sentences=4 was truncating numbered-list responses at option 1 (numbered items split as individual sentences by normalise regex).

**Layer 2 fix (commit d14ceb4):**
- ENGINEERING DEPTH RULE: replaced numbered-list instruction with explicit two-sentence semicolon format
- route_streaming: added engineering keyword detection; overrides max_sentences 4→8 for torque/actuator/joint queries
- Both fixes prevent normalise from truncating before all three options are expressed

**Retest (2026-09-27, via understudy_shadow audit log):**
- `elo_raw_gen` (365 chars): "Bowden cable — motor lower, force via cable, tradeoff routing complexity; gear reduction — multiply torque, tradeoff backlash and parts; motor upgrade — higher Nm, tradeoff heavier joint. A motor upgrade fits eLo's 40cm soft-shell form best, as it provides the necessary torque without significantly increasing the weight, maintaining eLo's agility and portability." ✅ PASS at generation layer — all three options, tradeoffs, synthesis
- `elo_final`: "More of that." ❌ BLOCKED — capability pipeline substitutes

**Blocking gaps (remaining):**
- Generation layer: ✅ PASS — all three options present with tradeoffs
- Capability pipeline: substitutes elo_final — same root cause as COG-010 blocker

---

## Board cross-check notes

Evidence sourced from batch test file `WO-CAP-COG-EVIDENCE-2026-09-20.md` and fresh live server tests (2026-09-27).
Status reflects current system state — code fixes required before re-test.
