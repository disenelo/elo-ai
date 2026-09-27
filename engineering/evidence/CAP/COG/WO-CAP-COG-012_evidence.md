# WO-CAP-COG-012 — Music and sound — Evidence
**Date:** 2026-09-27
**Source data:** `WO-CAP-COG-EVIDENCE-2026-09-20.md` + fresh live tests 2026-09-27
**Server:** localhost:5050 — ollama backend
**Verdict:** TESTED — ⚠️ PARTIAL

---

## Acceptance tests

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `if elo had a sound what would it be` | `In the silence, I'd create a symphony of vibrations, a hum of empathy that reson...` | build | ⚠️ PARTIAL — evocative language, 'hum of empathy' on-brand; but too abstract; no reference to actual sound design (breathing rhythm, NeoPixel pulse sync, soft low-frequency resonance) |

**Root cause:** Poetic response floats too high. Missing practical sound design reference (breathing rhythm, NeoPixel pulse sync as audio-visual pairing). Also: model framing issue — 'I noticed YOUR primary sound is' was addressing David as if eLo is a third-party observer.

**Layer 2 fix (commit 56de4fe):** SOUND DESIGN RULE extended with first-person framing instruction: "Always speak in first person: 'My primary sound is...' not 'Your sound' or 'I noticed YOUR sound'". Audit log confirms fix landed at generation layer.

**Retest (2026-09-27, via understudy_shadow audit log):**
- `elo_raw_gen`: "My primary sound is a soft low-frequency hum that changes with NeoPixel state. Idle: slow breathing rhythm, teal glow pulse at 0.5Hz." — ✅ PASS at generation layer: first-person, grounded in actual design, no poetic floating
- `elo_final`: "The alive feeling is the signal. Don't second-guess it." — ❌ BLOCKED: capability pipeline substitutes final response

**Blocking gaps (remaining):**
- Generation layer: PASS — first-person framing correct, sound design grounded
- Capability pipeline: substitutes elo_final — same root cause as COG-010 (vault_write/understudy_shadow)
- Fix blocked on Board WO for capability pipeline investigation

---

## Board cross-check notes

Evidence sourced from batch test file `WO-CAP-COG-EVIDENCE-2026-09-20.md` and fresh live server tests (2026-09-27).
Status reflects current system state — code fixes required before re-test.
